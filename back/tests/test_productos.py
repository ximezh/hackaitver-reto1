"""BE-11: CRUD de productos para Oficina, con búsqueda y desactivación con historial."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Producto, Proveedor
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("semillas")
RUTA = "/api/productos"
NUEVO = {
    "sku": "bor-0010",
    "nombre": "Borrador blanco, caja 10",
    "piezas_por_bulto": 30,
    "kg": 3.2,
    "m3": 0.006,
}


@pytest.fixture
def oficina(api: TestClient) -> dict[str, str]:
    return entrar(api, "admin.cedis")


def id_de(db: Session, sku: str) -> int:
    return db.scalars(select(Producto.id).filter_by(sku=sku)).one()


def test_lista_los_productos_del_prototipo(api: TestClient, oficina: dict) -> None:
    r = api.get(RUTA, headers=oficina)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == 7
    assert [p["sku"] for p in cuerpo["items"]] == [
        "RES-0500",
        "CUA-0100",
        "FOL-0100",
        "ENG-0020",
        "PAP-0100",
        "LAP-0012",
        "CLI-0100",
    ]
    resma = cuerpo["items"][0]
    assert {k: v for k, v in resma.items() if k not in ("id", "proveedor_id")} == {
        "sku": "RES-0500",
        "nombre": "Resma carta 500 hojas",
        "ilustracion": "hojas",
        "unidad": "resmas",
        "piezas_por_bulto": 10,
        "kg": 25.0,
        "m3": 0.032,
        "proveedor": {"id": resma["proveedor_id"], "nombre": "Papelera del Golfo"},
        "estado": "activo",
    }


@pytest.mark.parametrize(
    ("q", "skus"),
    [
        ("lapiz", ["LAP-0012"]),  # sin acento encuentra «Lápiz»
        ("CARTA", ["RES-0500", "FOL-0100", "PAP-0100"]),
        ("cli-", ["CLI-0100"]),
        ("100%", []),  # el % se busca literal
        (
            "  ",
            ["RES-0500", "CUA-0100", "FOL-0100", "ENG-0020", "PAP-0100", "LAP-0012", "CLI-0100"],
        ),
    ],
)
def test_busqueda(api: TestClient, oficina: dict, q: str, skus: list[str]) -> None:
    r = api.get(RUTA, params={"q": q}, headers=oficina)
    assert [p["sku"] for p in r.json()["items"]] == skus
    assert r.json()["total"] == len(skus)


def test_crear_con_valores_por_omision(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json=NUEVO, headers=oficina)
    assert r.status_code == 201
    assert {k: v for k, v in r.json().items() if k != "id"} == {
        "sku": "BOR-0010",
        "nombre": "Borrador blanco, caja 10",
        "ilustracion": "bulto",
        "unidad": "piezas",
        "piezas_por_bulto": 30,
        "kg": 3.2,
        "m3": 0.006,
        "proveedor_id": None,
        "proveedor": None,
        "estado": "activo",
    }


def test_crear_con_proveedor_principal(api: TestClient, oficina: dict, db: Session) -> None:
    atlas = db.scalars(select(Proveedor.id).filter_by(nombre="Distribuidora Atlas")).one()
    r = api.post(RUTA, json=NUEVO | {"proveedor_id": atlas}, headers=oficina)
    assert r.json()["proveedor"] == {"id": atlas, "nombre": "Distribuidora Atlas"}


def test_redondea_peso_y_volumen(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json=NUEVO | {"kg": 3.26, "m3": 0.0064}, headers=oficina)
    assert (r.json()["kg"], r.json()["m3"]) == (3.3, 0.006)


def test_sku_duplicado(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json=NUEVO | {"sku": "res-0500"}, headers=oficina)
    assert r.status_code == 409
    assert r.json()["code"] == "sku_duplicado"
    assert r.json()["detail"] == "Este SKU ya está registrado"
    # La sesión sigue sirviendo después del error.
    assert api.get(RUTA, headers=oficina).json()["total"] == 7


@pytest.mark.parametrize(
    ("cambio", "campo", "mensaje"),
    [
        ({"sku": ""}, "sku", "Completa SKU"),
        ({"sku": "R 1"}, "sku", "El SKU no es válido"),
        ({"nombre": "  "}, "nombre", "Completa Producto"),
        ({"piezas_por_bulto": 0}, "piezas_por_bulto", "Las piezas por bulto deben ser mayores a 0"),
        ({"kg": 0}, "kg", "El peso debe ser mayor a 0"),
        ({"m3": -1}, "m3", "El volumen debe ser mayor a 0"),
        ({"kg": 1000.1}, "kg", "El peso no puede pasar de 1,000 kg, la capacidad de una tarima"),
        ({"m3": 3}, "m3", "El volumen no puede pasar de 2.576 m³, la capacidad de una tarima"),
        ({"kg": "diez"}, "kg", "Peso bulto (kg) debe ser un número"),
        ({"ilustracion": "camion"}, "ilustracion", "La ilustración no es válida"),
        ({"proveedor_id": 999999}, "proveedor_id", "El proveedor no existe"),
    ],
)
def test_validaciones(
    api: TestClient, oficina: dict, cambio: dict, campo: str, mensaje: str
) -> None:
    r = api.post(RUTA, json=NUEVO | cambio, headers=oficina)
    assert r.status_code == 422
    assert r.json()["code"] == "validacion"
    assert r.json()["campos"] == {campo: mensaje}


def test_faltan_campos_con_la_etiqueta_de_oficina(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json={}, headers=oficina)
    assert r.json()["detail"] == "Completa SKU"
    assert r.json()["campos"] == {
        "sku": "Completa SKU",
        "nombre": "Completa Producto",
        "piezas_por_bulto": "Completa Piezas/bulto",
        "kg": "Completa Peso bulto (kg)",
        "m3": "Completa Volumen (m³)",
    }


def test_ver_y_no_encontrado(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.get(f"{RUTA}/{id_de(db, 'CLI-0100')}", headers=oficina)
    assert r.json()["nombre"] == "Clip #1, caja 100"
    assert api.get(f"{RUTA}/999999", headers=oficina).json()["code"] == "no_encontrado"


def test_editar_solo_lo_que_cambia(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.patch(f"{RUTA}/{id_de(db, 'CLI-0100')}", json={"kg": 1.2}, headers=oficina)
    assert r.status_code == 200
    assert (r.json()["kg"], r.json()["nombre"], r.json()["piezas_por_bulto"]) == (
        1.2,
        "Clip #1, caja 100",
        40,
    )


def test_editar_no_acepta_vaciar_obligatorios(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.patch(f"{RUTA}/{id_de(db, 'CLI-0100')}", json={"kg": None}, headers=oficina)
    assert r.json()["campos"] == {"kg": "Completa Peso bulto (kg)"}


def test_editar_a_sku_ocupado(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.patch(f"{RUTA}/{id_de(db, 'CLI-0100')}", json={"sku": "LAP-0012"}, headers=oficina)
    assert r.json()["code"] == "sku_duplicado"


def test_quitar_el_proveedor(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.patch(f"{RUTA}/{id_de(db, 'CLI-0100')}", json={"proveedor_id": None}, headers=oficina)
    assert r.json()["proveedor"] is None


def test_eliminar_sin_historial(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.delete(f"{RUTA}/{id_de(db, 'CLI-0100')}", headers=oficina)
    assert r.json() == {"resultado": "eliminado"}
    assert db.scalars(select(Producto).filter_by(sku="CLI-0100")).first() is None


def test_eliminar_con_historial_desactiva(api: TestClient, oficina: dict, db: Session) -> None:
    # Hasta el sprint 2 nada apunta a productos: se simula el historial con una tabla que se
    # deshace junto con la transacción de la prueba.
    from sqlalchemy import text

    db.execute(text("CREATE TABLE historial_prueba (producto_id int REFERENCES productos(id))"))
    producto = id_de(db, "CLI-0100")
    db.execute(text("INSERT INTO historial_prueba VALUES (:p)"), {"p": producto})
    r = api.delete(f"{RUTA}/{producto}", headers=oficina)
    assert r.status_code == 200
    assert r.json()["resultado"] == "desactivado"
    assert r.json()["registro"]["estado"] == "inactivo"
    assert r.json()["registro"]["sku"] == "CLI-0100"


# Sucursal sí lee la lista desde el sprint 2 (ver tests/test_pedidos.py).
@pytest.mark.parametrize("usuario", ["pgolfo", "caseta.jlopez"])
def test_solo_oficina(api: TestClient, usuario: str) -> None:
    r = api.get(RUTA, headers=entrar(api, usuario))
    assert r.status_code == 403
    assert r.json()["code"] == "sin_permiso"


def test_sin_sesion(api: TestClient) -> None:
    assert api.get(RUTA).json()["code"] == "no_autenticado"
