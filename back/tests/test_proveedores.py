"""BE-12: CRUD de proveedores, RFC válido y único, y suspensión."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalogos.proveedores import revisar_que_puede_agendar
from app.errores import ErrorApi
from app.models import Producto, Proveedor, Usuario
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("semillas")
RUTA = "/api/proveedores"
NUEVO = {"rfc": "pfo120304ab9", "nombre": "Papelería Fuentes", "contacto": "Eva Fuentes"}


@pytest.fixture
def oficina(api: TestClient) -> dict[str, str]:
    return entrar(api, "admin.cedis")


def proveedor(db: Session, rfc: str) -> Proveedor:
    return db.scalars(select(Proveedor).filter_by(rfc=rfc)).one()


def test_lista_como_el_prototipo(api: TestClient, oficina: dict) -> None:
    cuerpo = api.get(RUTA, headers=oficina).json()
    assert cuerpo["total"] == 4
    assert [(p["nombre"], p["estado"]) for p in cuerpo["items"]] == [
        ("Papelera del Golfo", "activo"),
        ("Distribuidora Atlas", "activo"),
        ("Grupo Escolar MX", "activo"),
        ("Útiles del Sureste", "suspendido"),
    ]
    assert {k: v for k, v in cuerpo["items"][0].items() if k != "id"} == {
        "rfc": "PGO090312AB1",
        "nombre": "Papelera del Golfo",
        "contacto": "Laura Pérez",
        "telefono": "229 555 0142",
        "estado": "activo",
    }


@pytest.mark.parametrize(("q", "esperados"), [("utiles", 1), ("hugo", 1), ("GEM15", 1), ("zzz", 0)])
def test_busqueda_por_rfc_nombre_y_contacto(
    api: TestClient, oficina: dict, q: str, esperados: int
) -> None:
    assert api.get(RUTA, params={"q": q}, headers=oficina).json()["total"] == esperados


def test_crear(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json=NUEVO | {"telefono": " "}, headers=oficina)
    assert r.status_code == 201
    assert {k: v for k, v in r.json().items() if k != "id"} == {
        "rfc": "PFO120304AB9",
        "nombre": "Papelería Fuentes",
        "contacto": "Eva Fuentes",
        "telefono": None,
        "estado": "activo",
    }


@pytest.mark.parametrize("rfc", ["PEGL800101AB1", "ÑAF090312AB1", "A&B090312XY9"])
def test_rfc_de_persona_moral_y_fisica(api: TestClient, oficina: dict, rfc: str) -> None:
    assert api.post(RUTA, json=NUEVO | {"rfc": rfc}, headers=oficina).status_code == 201


@pytest.mark.parametrize("rfc", ["PG090312AB1", "PGO0903AB1", "PGO090312AB", "PGO-090312-AB1"])
def test_rfc_invalido(api: TestClient, oficina: dict, rfc: str) -> None:
    r = api.post(RUTA, json=NUEVO | {"rfc": rfc}, headers=oficina)
    assert r.status_code == 422
    assert r.json()["campos"] == {"rfc": "El RFC no es válido"}


def test_rfc_duplicado(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json=NUEVO | {"rfc": "pgo090312ab1"}, headers=oficina)
    assert r.status_code == 409
    assert r.json()["code"] == "rfc_duplicado"
    assert r.json()["detail"] == "Este RFC ya está registrado"


def test_campos_obligatorios(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json={"rfc": "", "nombre": ""}, headers=oficina)
    assert r.json()["detail"] == "Completa RFC"
    assert r.json()["campos"] == {"rfc": "Completa RFC", "nombre": "Completa Proveedor"}


def test_estado_invalido(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json=NUEVO | {"estado": "baja"}, headers=oficina)
    assert r.json()["campos"] == {"estado": "El estado no es válido"}


def test_suspender_y_reactivar(api: TestClient, oficina: dict, db: Session) -> None:
    atlas = proveedor(db, "DAT110820KL3").id
    r = api.patch(f"{RUTA}/{atlas}", json={"estado": "suspendido"}, headers=oficina)
    assert r.json()["estado"] == "suspendido"
    r = api.patch(f"{RUTA}/{atlas}", json={"estado": "activo"}, headers=oficina)
    assert r.json()["estado"] == "activo"


def test_editar_contacto_y_vaciar_telefono(api: TestClient, oficina: dict, db: Session) -> None:
    atlas = proveedor(db, "DAT110820KL3").id
    r = api.patch(f"{RUTA}/{atlas}", json={"contacto": "Ana Ríos", "telefono": ""}, headers=oficina)
    assert (r.json()["contacto"], r.json()["telefono"], r.json()["nombre"]) == (
        "Ana Ríos",
        None,
        "Distribuidora Atlas",
    )


def test_un_suspendido_no_puede_agendar(db: Session) -> None:
    with pytest.raises(ErrorApi) as error:
        revisar_que_puede_agendar(proveedor(db, "USU180507ZX2"))
    assert (error.value.status, error.value.code) == (409, "proveedor_suspendido")
    revisar_que_puede_agendar(proveedor(db, "PGO090312AB1"))


def test_eliminar_sin_vinculos(api: TestClient, oficina: dict, db: Session) -> None:
    sureste = proveedor(db, "USU180507ZX2").id  # suspendido y sin productos ni usuarios
    assert api.delete(f"{RUTA}/{sureste}", headers=oficina).json() == {"resultado": "eliminado"}


def test_eliminar_con_productos_lo_desactiva(api: TestClient, oficina: dict, db: Session) -> None:
    atlas = proveedor(db, "DAT110820KL3")
    r = api.delete(f"{RUTA}/{atlas.id}", headers=oficina)
    assert r.json()["resultado"] == "desactivado"
    assert r.json()["registro"]["estado"] == "inactivo"
    # Sus productos siguen apuntando a él.
    eng = db.scalars(select(Producto).filter_by(sku="ENG-0020")).one()
    db.refresh(eng)
    assert eng.proveedor_id == atlas.id


def test_eliminar_con_usuarios_lo_desactiva(api: TestClient, oficina: dict, db: Session) -> None:
    golfo = proveedor(db, "PGO090312AB1")
    for p in db.scalars(select(Producto).filter_by(proveedor_id=golfo.id)):
        p.proveedor_id = None
    db.commit()
    r = api.delete(f"{RUTA}/{golfo.id}", headers=oficina)
    assert r.json()["resultado"] == "desactivado"
    assert db.scalars(select(Usuario).filter_by(usuario="pgolfo")).one().proveedor_id == golfo.id


def test_solo_oficina(api: TestClient) -> None:
    assert api.get(RUTA, headers=entrar(api, "pgolfo")).json()["code"] == "sin_permiso"
