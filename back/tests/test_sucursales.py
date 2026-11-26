"""BE-13: CRUD de sucursales con su rack R-<clave> (R-15)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Rack, Sucursal, Usuario
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("semillas")
RUTA = "/api/sucursales"
NUEVA = {"clave": "09", "nombre": "Suc. 09 Veracruz Puerto", "ciudad": "Veracruz"}


@pytest.fixture
def oficina(api: TestClient) -> dict[str, str]:
    return entrar(api, "admin.cedis")


def sucursal(db: Session, clave: str) -> Sucursal:
    return db.scalars(select(Sucursal).filter_by(clave=clave)).one()


def test_lista_como_el_prototipo(api: TestClient, oficina: dict) -> None:
    cuerpo = api.get(RUTA, headers=oficina).json()
    assert cuerpo["total"] == 6
    assert [(s["clave"], s["nombre"], s["rack"]) for s in cuerpo["items"]] == [
        ("01", "Suc. 01 Centro", "R-01"),
        ("04", "Suc. 04 Xalapa", "R-04"),
        ("07", "Suc. 07 Boca del Río", "R-07"),
        ("12", "Suc. 12 Córdoba", "R-12"),
        ("18", "Suc. 18 Orizaba", "R-18"),
        ("21", "Suc. 21 Tuxpan", "R-21"),
    ]
    assert {k: v for k, v in cuerpo["items"][2].items() if k != "id"} == {
        "clave": "07",
        "nombre": "Suc. 07 Boca del Río",
        "ciudad": "Boca del Río",
        "rack": "R-07",
        "estado": "activo",
    }


@pytest.mark.parametrize(
    ("q", "claves"), [("cordoba", ["12"]), ("21", ["21"]), ("SUC. 0", ["01", "04", "07"])]
)
def test_busqueda(api: TestClient, oficina: dict, q: str, claves: list[str]) -> None:
    r = api.get(RUTA, params={"q": q}, headers=oficina)
    assert [s["clave"] for s in r.json()["items"]] == claves


def test_crear_asigna_el_rack_de_su_clave(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json=NUEVA, headers=oficina)
    assert r.status_code == 201
    assert {k: v for k, v in r.json().items() if k != "id"} == NUEVA | {
        "rack": "R-09",
        "estado": "activo",
    }


def test_crea_el_rack_si_no_existe(api: TestClient, oficina: dict, db: Session) -> None:
    db.execute(delete(Rack).where(Rack.clave == "R-09"))
    db.commit()
    assert api.post(RUTA, json=NUEVA, headers=oficina).json()["rack"] == "R-09"


def test_clave_duplicada(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json=NUEVA | {"clave": "07"}, headers=oficina)
    assert r.status_code == 409
    assert r.json() == {
        "detail": "Esta clave ya está registrada",
        "code": "clave_duplicada",
        "campos": {"clave": "Esta clave ya está registrada"},
    }


def test_no_se_asignan_dos_sucursales_al_mismo_rack(
    api: TestClient, oficina: dict, db: Session
) -> None:
    # Si el rack R-09 quedara apuntado por otra sucursal (por ejemplo, datos viejos).
    otra = sucursal(db, "21")
    otra.rack = db.scalars(select(Rack).filter_by(clave="R-09")).one()
    db.commit()
    r = api.post(RUTA, json=NUEVA, headers=oficina)
    assert r.status_code == 409
    assert r.json()["code"] == "rack_ocupado"


@pytest.mark.parametrize("clave", ["00", "33", "7", "A1", "100"])
def test_clave_de_01_a_32(api: TestClient, oficina: dict, clave: str) -> None:
    r = api.post(RUTA, json=NUEVA | {"clave": clave}, headers=oficina)
    assert r.status_code == 422
    assert r.json()["campos"] == {"clave": "La clave debe ser de 01 a 32"}


def test_campos_obligatorios(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json={}, headers=oficina)
    assert r.json()["campos"] == {
        "clave": "Completa Clave",
        "nombre": "Completa Sucursal",
        "ciudad": "Completa Ciudad",
    }


def test_editar_nombre_y_ciudad(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.patch(
        f"{RUTA}/{sucursal(db, '01').id}",
        json={"nombre": "Suc. 01 Centro Histórico", "ciudad": "Veracruz"},
        headers=oficina,
    )
    assert (r.json()["nombre"], r.json()["ciudad"], r.json()["rack"]) == (
        "Suc. 01 Centro Histórico",
        "Veracruz",
        "R-01",
    )


@pytest.mark.parametrize("campo", ["clave", "rack"])
def test_la_clave_y_el_rack_no_se_cambian(
    api: TestClient, oficina: dict, db: Session, campo: str
) -> None:
    r = api.patch(f"{RUTA}/{sucursal(db, '01').id}", json={campo: "09"}, headers=oficina)
    assert r.status_code == 422
    assert r.json()["campos"] == {campo: "La clave no se puede cambiar"}


def test_eliminar_sin_usuarios_libera_el_rack(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.delete(f"{RUTA}/{sucursal(db, '21').id}", headers=oficina)
    assert r.json() == {"resultado": "eliminado"}
    nueva = api.post(
        RUTA, json=NUEVA | {"clave": "21", "nombre": "Suc. 21 Tuxpan Norte"}, headers=oficina
    )
    assert nueva.json()["rack"] == "R-21"


def test_eliminar_con_usuarios_la_desactiva(api: TestClient, oficina: dict, db: Session) -> None:
    suc07 = sucursal(db, "07")
    r = api.delete(f"{RUTA}/{suc07.id}", headers=oficina)
    assert r.json()["resultado"] == "desactivado"
    assert r.json()["registro"] | {"id": 0} == {
        "id": 0,
        "clave": "07",
        "nombre": "Suc. 07 Boca del Río",
        "ciudad": "Boca del Río",
        "rack": "R-07",
        "estado": "inactivo",
    }
    assert db.scalars(select(Usuario).filter_by(usuario="suc07")).one().sucursal_id == suc07.id


def test_solo_oficina(api: TestClient) -> None:
    assert api.get(RUTA, headers=entrar(api, "suc07")).json()["code"] == "sin_permiso"
