"""BE-24: etiquetas QR reales en PDF y SVG (R-06, A-10)."""

import io
import warnings

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.etiquetas import Etiqueta, etiqueta_pdf, etiquetas_pdf
from tests.conftest import entrar
from tests.test_facturas import FACTURA, bulto, golfo, miercoles  # noqa: F401

EJEMPLO = Etiqueta("B-0003", "OC-26-1182", "Suc. 07", "PAP-0100", 10, "CEDIS1;B=B-0003")


def texto(pdf: bytes) -> str:
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)


def test_etiqueta_con_los_datos_del_prototipo() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # falla si a Poppins le falta un glifo
        pdf = etiqueta_pdf(EJEMPLO)
    assert pdf.startswith(b"%PDF")
    contenido = texto(pdf)
    for dato in (
        "Bulto",
        "B-0003",
        "OC · Sucursal",
        "OC-26-1182 · Suc. 07",
        "SKU · Piezas",
        "PAP-0100 · 10",
    ):
        assert dato in contenido


def test_21_etiquetas_por_hoja_carta() -> None:
    pdf = etiquetas_pdf([EJEMPLO] * 22)
    paginas = PdfReader(io.BytesIO(pdf)).pages
    assert len(paginas) == 2
    assert round(float(paginas[0].mediabox.width) / 72 * 25.4) == 216  # carta


def test_qr_svg_del_bulto(api: TestClient, golfo: dict) -> None:  # noqa: F811
    folio = bulto(api, golfo).json()["bultos"][0]["folio"]
    r = api.get(f"/api/bultos/{folio}/qr.svg", headers=golfo)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in r.content


def test_qr_decodifica_el_texto_del_bulto(api: TestClient, golfo: dict) -> None:  # noqa: F811
    import segno

    creado = bulto(api, golfo).json()["bultos"][0]
    # Mismo texto, misma matriz: el QR codifica bulto, OC, sucursal, SKU y piezas (R-06).
    assert creado["qr"].startswith(f"CEDIS1;B={creado['folio']};OC=OC-26-")
    assert segno.make(creado["qr"], error="m").designator


def test_etiqueta_pdf_del_bulto(api: TestClient, golfo: dict) -> None:  # noqa: F811
    folio = bulto(api, golfo).json()["bultos"][0]["folio"]
    r = api.get(f"/api/bultos/{folio}/etiqueta.pdf", headers=golfo)
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"] == f'attachment; filename="{folio}.pdf"'
    assert folio in texto(r.content)


def test_etiquetas_de_la_factura(api: TestClient, golfo: dict) -> None:  # noqa: F811
    bulto(api, golfo, cantidad=3)
    r = api.get(f"/api/facturas/{FACTURA}/etiquetas.pdf", headers=golfo)
    assert r.headers["content-disposition"] == f'attachment; filename="{FACTURA}-etiquetas.pdf"'
    assert texto(r.content).count("SKU · Piezas") == 3


def test_oficina_tambien_las_descarga(api: TestClient, golfo: dict) -> None:  # noqa: F811
    bulto(api, golfo)
    r = api.get(f"/api/facturas/{FACTURA}/etiquetas.pdf", headers=entrar(api, "admin.cedis"))
    assert r.status_code == 200


def test_factura_sin_bultos(api: TestClient, golfo: dict) -> None:  # noqa: F811
    r = api.get(f"/api/facturas/{FACTURA}/etiquetas.pdf", headers=golfo)
    assert (r.status_code, r.json()["code"]) == (409, "factura_sin_bultos")


@pytest.mark.usefixtures("golfo")
def test_sucursal_no_descarga(api: TestClient) -> None:
    r = api.get(f"/api/facturas/{FACTURA}/etiquetas.pdf", headers=entrar(api, "suc07"))
    assert r.json()["code"] == "sin_permiso"
