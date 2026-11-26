"""BE-21: cada proveedor ve solo su parte de cada OC (R-16)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contrasenas import hashear
from app.models import Proveedor, Usuario
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("semillas")
RUTA = "/api/proveedor/ordenes"
# OC con productos de dos proveedores: hojas y resmas de Papelera del Golfo, lápices de Atlas.
PEDIDO = {
    "lineas": [
        {"sku": "PAP-0100", "bultos": 14},
        {"sku": "RES-0500", "bultos": 10},
        {"sku": "LAP-0012", "bultos": 2},
    ]
}


@pytest.fixture
def oc(api: TestClient, semillas: None) -> str:
    return api.post("/api/pedidos", json=PEDIDO, headers=entrar(api, "suc07")).json()["folio"]


@pytest.fixture
def atlas(api: TestClient, db: Session, semillas: None) -> dict[str, str]:
    prov = db.scalars(select(Proveedor).filter_by(rfc="DAT110820KL3")).one()
    db.add(Usuario(usuario="datlas", nombre="Distribuidora Atlas", rol="proveedor", canal="web",
                   contrasena_hash=hashear("cedis2026"), contrasena_temporal=False,
                   proveedor_id=prov.id))  # fmt: skip
    db.commit()
    return entrar(api, "datlas")


def test_golfo_ve_solo_su_parte(api: TestClient, oc: str) -> None:
    cuerpo = api.get(RUTA, headers=entrar(api, "pgolfo")).json()
    assert cuerpo["total"] == 1
    orden = cuerpo["items"][0]
    assert orden["oc"] == oc
    assert orden["sucursal"] | {"id": 0} == {
        "id": 0,
        "clave": "07",
        "nombre": "Suc. 07 Boca del Río",
    }
    # 14 * 5.1 + 10 * 25.0 = 321.4 kg; 14 * 0.018 + 10 * 0.032 = 0.572 m³ (sin los lápices).
    assert (orden["bultos"], orden["kg"], orden["m3"]) == (24, 321.4, 0.572)
    assert [(x["producto"]["sku"], x["bultos"], x["piezas"]) for x in orden["lineas"]] == [
        ("PAP-0100", 14, 140),
        ("RES-0500", 10, 100),
    ]
    # El formulario «+ Bulto» parte del peso y volumen del catálogo (P-03).
    assert (orden["lineas"][0]["producto"]["kg"], orden["lineas"][0]["producto"]["m3"]) == (
        5.1,
        0.018,
    )
    assert (orden["cita"], orden["factura"]) == (None, None)


def test_atlas_ve_su_parte_de_la_misma_oc(api: TestClient, oc: str, atlas: dict) -> None:
    orden = api.get(RUTA, headers=atlas).json()["items"][0]
    assert orden["oc"] == oc
    assert [(x["producto"]["sku"], x["bultos"]) for x in orden["lineas"]] == [("LAP-0012", 2)]
    assert (orden["bultos"], orden["kg"]) == (2, 4.8)


def test_proveedor_sin_ordenes(api: TestClient) -> None:
    assert api.get(RUTA, headers=entrar(api, "pgolfo")).json() == {"items": [], "total": 0}


def test_de_la_mas_nueva_a_la_mas_antigua(api: TestClient) -> None:
    suc = entrar(api, "suc07")
    a = api.post("/api/pedidos", json={"lineas": [{"sku": "PAP-0100", "bultos": 1}]}, headers=suc)
    b = api.post("/api/pedidos", json={"lineas": [{"sku": "RES-0500", "bultos": 1}]}, headers=suc)
    folios = [o["oc"] for o in api.get(RUTA, headers=entrar(api, "pgolfo")).json()["items"]]
    assert folios == [b.json()["folio"], a.json()["folio"]]


@pytest.mark.usefixtures("oc")
def test_sin_cita_por_ahora_son_todas(api: TestClient) -> None:
    r = api.get(RUTA, params={"sin_cita": "true"}, headers=entrar(api, "pgolfo"))
    assert r.json()["total"] == 1


@pytest.mark.parametrize("usuario", ["suc07", "admin.cedis"])
def test_solo_proveedor(api: TestClient, usuario: str) -> None:
    assert api.get(RUTA, headers=entrar(api, usuario)).json()["code"] == "sin_permiso"
