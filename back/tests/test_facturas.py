"""BE-23: factura desglosada por bulto, con un solo SKU por bulto (R-05)."""

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import tiempo
from app.models import Bulto, Factura, Producto
from app.pedidos.facturas import caja
from tests.conftest import entrar

FACTURA = "FAC-A-20418"


@pytest.fixture(autouse=True)
def miercoles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tiempo, "hoy", lambda: date(2026, 11, 25))
    monkeypatch.setattr(tiempo, "ahora", lambda: datetime(2026, 11, 25, 7, 0, tzinfo=tiempo.ZONA))


@pytest.fixture
def golfo(api: TestClient, semillas: None) -> dict[str, str]:
    """Papelera del Golfo con su cita confirmada para 14 bultos de hojas y 10 de resmas."""
    suc = entrar(api, "suc07")
    lineas = [{"sku": "PAP-0100", "bultos": 14}, {"sku": "RES-0500", "bultos": 10}]
    oc = api.post("/api/pedidos", json={"lineas": lineas}, headers=suc).json()["folio"]
    enc = entrar(api, "pgolfo")
    cita = {"oc": oc, "folio_factura": FACTURA, "anden": "R1", "dia": "2026-11-26",
            "inicio": "11:00", "duracion_min": 60}  # fmt: skip
    assert api.post("/api/citas", json=cita, headers=enc).status_code == 201
    return enc


def bulto(api: TestClient, enc: dict, **cambios: object):
    datos = {"sku": "PAP-0100", "piezas": 10, "kg": 5.1, "m3": 0.018} | cambios
    return api.post(f"/api/facturas/{FACTURA}/bultos", json=datos, headers=enc)


def test_factura_sin_bultos(api: TestClient, golfo: dict) -> None:
    r = api.get(f"/api/facturas/{FACTURA}", headers=golfo).json()
    assert (r["folio"], r["bultos_esperados"], r["totales"], r["cuadra"], r["bultos"]) == (
        FACTURA,
        24,
        {"bultos": 0, "kg": 0.0, "m3": 0.0},
        False,
        [],
    )
    assert r["diferencias"] == [
        {"sku": "PAP-0100", "esperados": 14, "capturados": 0},
        {"sku": "RES-0500", "esperados": 10, "capturados": 0},
    ]


def test_agregar_un_bulto(api: TestClient, golfo: dict) -> None:
    r = bulto(api, golfo)
    assert r.status_code == 201
    nuevo = r.json()["bultos"][0]
    assert nuevo["folio"].startswith("B-")
    assert (nuevo["producto"]["sku"], nuevo["piezas"], nuevo["kg"], nuevo["m3"], nuevo["caja"]) == (
        "PAP-0100",
        10,
        5.1,
        0.018,
        "verde",
    )
    oc = r.json()["factura"]["oc"]
    assert nuevo["qr"] == f"CEDIS1;B={nuevo['folio']};OC={oc};SUC=07;SKU=PAP-0100;PZ=10"
    assert r.json()["factura"]["totales"] == {"bultos": 1, "kg": 5.1, "m3": 0.018}


def test_cantidad_crea_varios_con_folio_propio(api: TestClient, golfo: dict) -> None:
    r = bulto(api, golfo, cantidad=14)
    folios = [b["folio"] for b in r.json()["bultos"]]
    assert len(set(folios)) == 14
    bulto(api, golfo, sku="RES-0500", kg=25.0, m3=0.032, cantidad=10)
    f = api.get(f"/api/facturas/{FACTURA}", headers=golfo).json()
    assert (f["totales"], f["cuadra"], f["diferencias"]) == (
        {"bultos": 24, "kg": 321.4, "m3": 0.572},
        True,
        [],
    )
    orden = api.get("/api/proveedor/ordenes", headers=golfo).json()["items"][0]
    assert orden["factura"] == {"folio": FACTURA, "bultos_capturados": 24}


def test_avisa_si_sobran(api: TestClient, golfo: dict) -> None:
    bulto(api, golfo, cantidad=15)
    dif = api.get(f"/api/facturas/{FACTURA}", headers=golfo).json()["diferencias"][0]
    assert dif == {"sku": "PAP-0100", "esperados": 14, "capturados": 15}


@pytest.mark.parametrize(
    ("cambios", "campo", "mensaje"),
    [
        ({"sku": "LAP-0012"}, "sku", "Ese producto no está en la orden"),
        ({"piezas": 0}, "piezas", "Las piezas deben ser al menos 1"),
        ({"kg": 0}, "kg", "El peso debe ser mayor a 0"),
        ({"kg": 1001}, "kg", "El peso no puede pasar de 1,000 kg, la capacidad de una tarima"),
        ({"m3": 0}, "m3", "El volumen debe ser mayor a 0"),
        ({"m3": 3}, "m3", "El volumen no puede pasar de 2.576 m³, la capacidad de una tarima"),
        ({"cantidad": 101}, "cantidad", "La cantidad debe ser de 1 a 100 bultos"),
    ],
)
def test_validaciones(
    api: TestClient, golfo: dict, cambios: dict, campo: str, mensaje: str
) -> None:
    r = bulto(api, golfo, **cambios)
    assert r.status_code == 422
    assert r.json()["campos"] == {campo: mensaje}


@pytest.mark.parametrize(
    ("kg", "color"), [(15, "roja"), (14.9, "naranja"), (7, "naranja"), (6.9, "verde")]
)
def test_caja_por_peso(kg: float, color: str) -> None:
    from decimal import Decimal

    assert caja(Decimal(str(kg))) == color


def test_la_base_impide_un_bulto_de_otro_producto(
    api: TestClient, golfo: dict, db: Session
) -> None:
    factura = db.scalars(select(Factura).filter_by(folio=FACTURA)).one()
    lapiz = db.scalars(select(Producto).filter_by(sku="LAP-0012")).one()
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(Bulto(folio="B-9999", factura=factura, producto=lapiz, piezas=1, kg=1, m3=0.01))
        db.flush()
    assert error.value.orig.diag.constraint_name == "fk_bultos_producto_de_la_factura"  # type: ignore[union-attr]


def test_quitar_un_bulto(api: TestClient, golfo: dict) -> None:
    folio = bulto(api, golfo).json()["bultos"][0]["folio"]
    assert api.delete(f"/api/bultos/{folio}", headers=golfo).json() == {"resultado": "eliminado"}
    assert api.get(f"/api/facturas/{FACTURA}", headers=golfo).json()["totales"]["bultos"] == 0


def test_lista_de_facturas(api: TestClient, golfo: dict) -> None:
    r = api.get("/api/facturas", headers=golfo).json()
    assert r["total"] == 1 and r["items"][0]["folio"] == FACTURA
    assert "bultos" not in r["items"][0]


def test_factura_ajena(api: TestClient, golfo: dict, db: Session) -> None:
    from app.contrasenas import hashear
    from app.models import Proveedor, Usuario

    atlas = db.scalars(select(Proveedor).filter_by(rfc="DAT110820KL3")).one()
    db.add(Usuario(usuario="datlas", nombre="Atlas", rol="proveedor", canal="web",
                   contrasena_hash=hashear("cedis2026"), contrasena_temporal=False,
                   proveedor_id=atlas.id))  # fmt: skip
    db.commit()
    otro = entrar(api, "datlas")
    assert api.get(f"/api/facturas/{FACTURA}", headers=otro).json()["code"] == "no_encontrado"
    folio = bulto(api, golfo).json()["bultos"][0]["folio"]
    assert api.delete(f"/api/bultos/{folio}", headers=otro).json()["code"] == "no_encontrado"
