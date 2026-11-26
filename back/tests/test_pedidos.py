"""BE-20: pedido de sucursal por bultos que genera una OC dividida por proveedor (R-16, A-16)."""

import re
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import tiempo
from app.models import OrdenCompra, ParteOc, Producto, Proveedor
from app.pedidos.fechas import dias_habiles_despues
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("semillas")
RUTA = "/api/pedidos"
# El carrito del prototipo: 4 bultos de hojas (Papelera del Golfo) y 2 de lápices (Atlas).
CARRITO = {"lineas": [{"sku": "PAP-0100", "bultos": 4}, {"sku": "LAP-0012", "bultos": 2}]}


@pytest.fixture
def sucursal(api: TestClient) -> dict[str, str]:
    return entrar(api, "suc07")


@pytest.fixture(autouse=True)
def miercoles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tiempo, "hoy", lambda: date(2026, 11, 25))


def test_crea_la_oc_dividida_por_proveedor(api: TestClient, sucursal: dict) -> None:
    r = api.post(RUTA, json=CARRITO, headers=sucursal)
    assert r.status_code == 201
    oc = r.json()
    assert re.fullmatch(r"OC-26-\d{4,}", oc["folio"])
    assert oc["sucursal"] | {"id": 0} == {"id": 0, "clave": "07", "nombre": "Suc. 07 Boca del Río"}
    assert (oc["paso"], oc["paso_indice"], oc["embarque"]) == ("oc_emitida", 0, None)
    assert (oc["bultos"], oc["kg"], oc["m3"]) == (6, 25.2, 0.088)
    resumen = [
        (x["producto"]["sku"], x["proveedor"]["nombre"], x["bultos"], x["piezas"], x["kg"], x["m3"])
        for x in oc["lineas"]
    ]
    assert resumen == [
        ("PAP-0100", "Papelera del Golfo", 4, 40, 20.4, 0.072),
        ("LAP-0012", "Distribuidora Atlas", 2, 48, 4.8, 0.016),
    ]
    assert [(p["proveedor"]["nombre"], p["bultos"], p["cita"]) for p in oc["partes"]] == [
        ("Papelera del Golfo", 4, None),
        ("Distribuidora Atlas", 2, None),
    ]
    assert oc["lineas"][0]["producto"] | {"id": 0} == {
        "id": 0,
        "sku": "PAP-0100",
        "nombre": "Hojas carta, paquete 100",
        "ilustracion": "hojas",
        "unidad": "paquetes",
        "piezas_por_bulto": 10,
    }
    assert oc["creado_en"].endswith("-06:00")


def test_muchos_a_muchos_entre_oc_y_proveedor(api: TestClient, sucursal: dict, db: Session) -> None:
    api.post(RUTA, json=CARRITO, headers=sucursal)
    api.post(RUTA, json={"lineas": [{"sku": "RES-0500", "bultos": 3}]}, headers=sucursal)
    golfo = db.scalars(select(Proveedor).filter_by(rfc="PGO090312AB1")).one()
    ocs_de_golfo = db.scalars(select(ParteOc).filter_by(proveedor_id=golfo.id)).all()
    assert len(ocs_de_golfo) == 2
    primera = db.scalars(select(OrdenCompra).order_by(OrdenCompra.id)).first()
    assert primera is not None and len(primera.partes) == 2


def test_suma_skus_repetidos(api: TestClient, sucursal: dict) -> None:
    lineas = [{"sku": "pap-0100", "bultos": 1}, {"sku": "PAP-0100", "bultos": 2}]
    oc = api.post(RUTA, json={"lineas": lineas}, headers=sucursal).json()
    assert [(x["producto"]["sku"], x["bultos"]) for x in oc["lineas"]] == [("PAP-0100", 3)]


def test_llega_estimado_en_dias_habiles(api: TestClient, sucursal: dict) -> None:
    # Miércoles 25 + 3 días hábiles = sábado 28.
    assert api.post(RUTA, json=CARRITO, headers=sucursal).json()["llega_estimado"] == "2026-11-28"


def test_los_domingos_no_cuentan() -> None:
    assert dias_habiles_despues(date(2026, 11, 27), 3) == date(2026, 12, 1)  # vie → mar


def test_folios_consecutivos(api: TestClient, sucursal: dict) -> None:
    a = api.post(RUTA, json=CARRITO, headers=sucursal).json()["folio"]
    b = api.post(RUTA, json=CARRITO, headers=sucursal).json()["folio"]
    assert int(b.rsplit("-", 1)[1]) == int(a.rsplit("-", 1)[1]) + 1


@pytest.mark.parametrize(
    ("cuerpo", "mensaje"),
    [
        ({}, "Agrega productos"),
        ({"lineas": []}, "Agrega productos"),
        ({"lineas": [{"sku": "PAP-0100", "bultos": 0}]}, "Los bultos deben ser al menos 1"),
        (
            {"lineas": [{"sku": "PAP-0100", "bultos": 1000}]},
            "Un pedido admite hasta 999 bultos por producto",
        ),
        ({"lineas": [{"sku": "NO-0000", "bultos": 1}]}, "El producto NO-0000 no está disponible"),
    ],
)  # fmt: skip
def test_validaciones(api: TestClient, sucursal: dict, cuerpo: dict, mensaje: str) -> None:
    r = api.post(RUTA, json=cuerpo, headers=sucursal)
    assert r.status_code == 422
    assert r.json() == {"detail": mensaje, "code": "validacion", "campos": {"lineas": mensaje}}


def test_producto_inactivo(api: TestClient, sucursal: dict, db: Session) -> None:
    db.scalars(select(Producto).filter_by(sku="CLI-0100")).one().estado = "inactivo"
    db.commit()
    r = api.post(RUTA, json={"lineas": [{"sku": "CLI-0100", "bultos": 1}]}, headers=sucursal)
    assert r.json()["detail"] == "El producto CLI-0100 no está disponible"


def test_producto_sin_proveedor(api: TestClient, sucursal: dict, db: Session) -> None:
    db.scalars(select(Producto).filter_by(sku="CLI-0100")).one().proveedor_id = None
    db.commit()
    r = api.post(RUTA, json={"lineas": [{"sku": "CLI-0100", "bultos": 1}]}, headers=sucursal)
    assert r.json()["detail"] == (
        "El producto CLI-0100 no tiene proveedor asignado. Comunícate con Oficina"
    )


def test_proveedor_suspendido(api: TestClient, sucursal: dict, db: Session) -> None:
    db.scalars(select(Proveedor).filter_by(rfc="DAT110820KL3")).one().estado = "suspendido"
    db.commit()
    r = api.post(RUTA, json=CARRITO, headers=sucursal)
    assert r.json()["detail"] == "El proveedor de LAP-0012 está suspendido. Comunícate con Oficina"


def test_lista_solo_los_de_la_sucursal(api: TestClient, sucursal: dict, db: Session) -> None:
    from app.contrasenas import hashear
    from app.models import Sucursal, Usuario

    api.post(RUTA, json=CARRITO, headers=sucursal)
    xalapa = db.scalars(select(Sucursal).filter_by(clave="04")).one()
    db.add(Usuario(usuario="suc04", nombre="Suc. 04", rol="sucursal", canal="web",
                   contrasena_hash=hashear("cedis2026"), contrasena_temporal=False,
                   sucursal_id=xalapa.id))  # fmt: skip
    db.commit()
    otra = entrar(api, "suc04")
    api.post(RUTA, json={"lineas": [{"sku": "RES-0500", "bultos": 1}]}, headers=otra)

    mios = api.get(RUTA, headers=sucursal).json()
    assert mios["total"] == 1 and mios["items"][0]["bultos"] == 6
    ajeno = api.get(RUTA, headers=otra).json()["items"][0]["folio"]
    assert api.get(f"{RUTA}/{ajeno}", headers=sucursal).json()["code"] == "no_encontrado"


def test_lista_del_mas_nuevo_y_en_curso(api: TestClient, sucursal: dict, db: Session) -> None:
    a = api.post(RUTA, json=CARRITO, headers=sucursal).json()["folio"]
    b = api.post(RUTA, json=CARRITO, headers=sucursal).json()["folio"]
    assert [p["folio"] for p in api.get(RUTA, headers=sucursal).json()["items"]] == [b, a]
    db.scalars(select(OrdenCompra).filter_by(folio=a)).one().paso = "recibido"
    db.commit()
    en_curso = api.get(RUTA, params={"en_curso": "true"}, headers=sucursal).json()
    assert [p["folio"] for p in en_curso["items"]] == [b]


def test_ver_un_pedido(api: TestClient, sucursal: dict) -> None:
    folio = api.post(RUTA, json=CARRITO, headers=sucursal).json()["folio"]
    assert api.get(f"{RUTA}/{folio.lower()}", headers=sucursal).json()["folio"] == folio


@pytest.mark.parametrize("usuario", ["admin.cedis", "pgolfo"])
def test_solo_sucursal(api: TestClient, usuario: str) -> None:
    r = api.post(RUTA, json=CARRITO, headers=entrar(api, usuario))
    assert r.json()["code"] == "sin_permiso"


# --- Catálogo para pedir ---------------------------------------------------------------


def test_sucursal_lee_solo_productos_activos(api: TestClient, sucursal: dict, db: Session) -> None:
    db.scalars(select(Producto).filter_by(sku="CLI-0100")).one().estado = "inactivo"
    db.commit()
    skus = [p["sku"] for p in api.get("/api/productos", headers=sucursal).json()["items"]]
    assert "CLI-0100" not in skus and len(skus) == 6
    oficina = entrar(api, "admin.cedis")
    assert api.get("/api/productos", headers=oficina).json()["total"] == 7


def test_sucursal_no_administra_productos(api: TestClient, sucursal: dict, db: Session) -> None:
    pid = db.scalars(select(Producto.id).filter_by(sku="CLI-0100")).one()
    assert api.get(f"/api/productos/{pid}", headers=sucursal).json()["code"] == "sin_permiso"
    assert api.delete(f"/api/productos/{pid}", headers=sucursal).json()["code"] == "sin_permiso"


def test_producto_con_pedidos_se_desactiva(api: TestClient, sucursal: dict, db: Session) -> None:
    api.post(RUTA, json=CARRITO, headers=sucursal)
    pid = db.scalars(select(Producto.id).filter_by(sku="LAP-0012")).one()
    r = api.delete(f"/api/productos/{pid}", headers=entrar(api, "admin.cedis"))
    assert r.json()["resultado"] == "desactivado"
