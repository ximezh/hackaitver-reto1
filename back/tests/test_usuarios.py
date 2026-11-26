"""BE-14: usuarios con rol de lista fija, prefijo de Android, vínculo y contraseña temporal."""

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalogos.usuarios import contrasena_temporal
from app.contrasenas import verificar
from app.models import Proveedor, Sucursal, Usuario
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("semillas")
RUTA = "/api/usuarios"


@pytest.fixture
def oficina(api: TestClient) -> dict[str, str]:
    return entrar(api, "admin.cedis")


def usuario(db: Session, nombre: str) -> Usuario:
    return db.scalars(select(Usuario).filter_by(usuario=nombre)).one()


def id_sucursal(db: Session, clave: str) -> int:
    return db.scalars(select(Sucursal.id).filter_by(clave=clave)).one()


def id_proveedor(db: Session, rfc: str) -> int:
    return db.scalars(select(Proveedor.id).filter_by(rfc=rfc)).one()


def test_lista_como_el_contrato(api: TestClient, oficina: dict, db: Session) -> None:
    cuerpo = api.get(RUTA, headers=oficina).json()
    assert cuerpo["total"] == 6
    assert [(u["usuario"], u["rol"], u["canal"]) for u in cuerpo["items"]] == [
        ("caseta.jlopez", "caseta", "android"),
        ("desem.mruiz", "desembarque", "android"),
        ("embar.acruz", "embarque", "android"),
        ("suc07", "sucursal", "web"),
        ("pgolfo", "proveedor", "web"),
        ("admin.cedis", "oficina", "web"),
    ]
    suc07 = cuerpo["items"][3]
    assert suc07["sucursal"] == {"id": id_sucursal(db, "07"), "nombre": "Suc. 07 Boca del Río"}
    assert suc07["proveedor"] is None
    assert "contrasena_hash" not in suc07 and "contrasena_generada" not in suc07


def test_busqueda(api: TestClient, oficina: dict) -> None:
    r = api.get(RUTA, params={"q": "maria"}, headers=oficina)
    assert [u["usuario"] for u in r.json()["items"]] == ["desem.mruiz"]


def test_crear_genera_contrasena_temporal(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.post(
        RUTA,
        json={"usuario": "Caseta.RGomez", "nombre": "Rosa Gómez", "rol": "caseta"},
        headers=oficina,
    )
    assert r.status_code == 201
    cuerpo = r.json()
    generada = cuerpo.pop("contrasena_generada")
    assert re.fullmatch(r"Tmp-[A-Za-z2-9]{4}-[A-Za-z2-9]{4}", generada)
    assert {k: v for k, v in cuerpo.items() if k != "id"} == {
        "usuario": "caseta.rgomez",
        "nombre": "Rosa Gómez",
        "rol": "caseta",
        "canal": "android",
        "sucursal_id": None,
        "sucursal": None,
        "proveedor_id": None,
        "proveedor": None,
        "contrasena_temporal": True,
        "estado": "activo",
    }
    guardado = usuario(db, "caseta.rgomez")
    assert guardado.contrasena_hash != generada
    assert verificar(guardado.contrasena_hash, generada)
    # La contraseña generada solo se devuelve una vez.
    assert "contrasena_generada" not in api.get(f"{RUTA}/{guardado.id}", headers=oficina).json()


def test_el_usuario_nuevo_entra_y_debe_cambiarla(api: TestClient, oficina: dict) -> None:
    generada = api.post(
        RUTA,
        json={"usuario": "desem.lsoto", "nombre": "Luis Soto", "rol": "desembarque"},
        headers=oficina,
    ).json()["contrasena_generada"]
    sesion = api.post(
        "/api/auth/login",
        json={"usuario": "desem.lsoto", "contrasena": generada, "canal": "android"},
    ).json()
    assert sesion["contrasena_temporal"] is True


def test_crear_usuario_de_sucursal(api: TestClient, oficina: dict, db: Session) -> None:
    suc = id_sucursal(db, "12")
    r = api.post(
        RUTA,
        json={
            "usuario": "suc12",
            "nombre": "Suc. 12 Córdoba",
            "rol": "sucursal",
            "sucursal_id": suc,
        },
        headers=oficina,
    )
    assert r.status_code == 201
    assert (r.json()["canal"], r.json()["sucursal"]) == (
        "web",
        {"id": suc, "nombre": "Suc. 12 Córdoba"},
    )


def test_crear_usuario_de_proveedor(api: TestClient, oficina: dict, db: Session) -> None:
    atlas = id_proveedor(db, "DAT110820KL3")
    r = api.post(
        RUTA,
        json={
            "usuario": "datlas",
            "nombre": "Distribuidora Atlas",
            "rol": "proveedor",
            "proveedor_id": atlas,
        },
        headers=oficina,
    )
    assert r.json()["proveedor"] == {"id": atlas, "nombre": "Distribuidora Atlas"}


def test_otros_roles_no_guardan_vinculo(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.post(
        RUTA,
        json={
            "usuario": "ofi.lruiz",
            "nombre": "Lía Ruiz",
            "rol": "oficina",
            "sucursal_id": id_sucursal(db, "07"),
        },
        headers=oficina,
    )
    assert (r.json()["sucursal_id"], r.json()["sucursal"]) == (None, None)


@pytest.mark.parametrize(
    ("datos", "campo", "mensaje"),
    [
        (
            {"rol": "caseta", "usuario": "rgomez"},
            "usuario",
            "El usuario de Caseta debe empezar con caseta.",
        ),
        (
            {"rol": "desembarque", "usuario": "embar.x1"},
            "usuario",
            "El usuario de Sup. desembarque debe empezar con desem.",
        ),
        (
            {"rol": "embarque", "usuario": "emb.x1"},
            "usuario",
            "El usuario de Sup. embarque debe empezar con embar.",
        ),
        (
            {"rol": "oficina", "usuario": "caseta.ana"},
            "usuario",
            "Ese prefijo es solo para usuarios de Android",
        ),
        ({"rol": "sucursal", "usuario": "suc99"}, "sucursal_id", "Elige la sucursal"),
        (
            {"rol": "sucursal", "usuario": "suc99", "sucursal_id": 999999},
            "sucursal_id",
            "Elige la sucursal",
        ),
        ({"rol": "proveedor", "usuario": "prov1"}, "proveedor_id", "Elige el proveedor"),
        ({"rol": "admin", "usuario": "root1"}, "rol", "El rol no es válido"),
        (
            {"rol": "oficina", "usuario": "a b"},
            "usuario",
            "El usuario admite de 3 a 40 letras, números, punto, guion o guion bajo",
        ),
    ],
)
def test_validaciones(
    api: TestClient, oficina: dict, datos: dict, campo: str, mensaje: str
) -> None:
    r = api.post(RUTA, json={"nombre": "Prueba"} | datos, headers=oficina)
    assert r.status_code == 422
    assert r.json()["campos"] == {campo: mensaje}


def test_campos_obligatorios(api: TestClient, oficina: dict) -> None:
    r = api.post(RUTA, json={}, headers=oficina)
    assert r.json()["campos"] == {
        "usuario": "Completa Usuario",
        "nombre": "Completa Nombre",
        "rol": "Completa Rol",
    }


def test_usuario_duplicado(api: TestClient, oficina: dict) -> None:
    r = api.post(
        RUTA, json={"usuario": "PGOLFO", "nombre": "Otro", "rol": "oficina"}, headers=oficina
    )
    assert r.status_code == 409
    assert r.json()["code"] == "usuario_duplicado"


def test_cambiar_rol_revalida_el_prefijo(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.patch(
        f"{RUTA}/{usuario(db, 'caseta.jlopez').id}", json={"rol": "embarque"}, headers=oficina
    )
    assert r.json()["campos"] == {"usuario": "El usuario de Sup. embarque debe empezar con embar."}
    r = api.patch(
        f"{RUTA}/{usuario(db, 'caseta.jlopez').id}",
        json={"rol": "embarque", "usuario": "embar.jlopez"},
        headers=oficina,
    )
    assert (r.json()["usuario"], r.json()["rol"], r.json()["canal"]) == (
        "embar.jlopez",
        "embarque",
        "android",
    )


def test_cambiar_de_sucursal_a_otro_rol_quita_el_vinculo(
    api: TestClient, oficina: dict, db: Session
) -> None:
    r = api.patch(f"{RUTA}/{usuario(db, 'suc07').id}", json={"rol": "oficina"}, headers=oficina)
    assert (r.json()["rol"], r.json()["canal"], r.json()["sucursal_id"]) == ("oficina", "web", None)


def test_cambiar_la_sucursal_del_usuario(api: TestClient, oficina: dict, db: Session) -> None:
    suc = id_sucursal(db, "01")
    r = api.patch(f"{RUTA}/{usuario(db, 'suc07').id}", json={"sucursal_id": suc}, headers=oficina)
    assert r.json()["sucursal"]["nombre"] == "Suc. 01 Centro"


def test_desactivar_a_otro(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.patch(
        f"{RUTA}/{usuario(db, 'pgolfo').id}", json={"estado": "inactivo"}, headers=oficina
    )
    assert r.json()["estado"] == "inactivo"


def test_restablecer(api: TestClient, oficina: dict, db: Session) -> None:
    pgolfo = usuario(db, "pgolfo")
    r = api.post(f"{RUTA}/{pgolfo.id}/restablecer", headers=oficina)
    assert r.status_code == 200
    generada = r.json()["contrasena_generada"]
    assert r.json()["contrasena_temporal"] is True
    db.refresh(pgolfo)
    assert verificar(pgolfo.contrasena_hash, generada)
    assert not verificar(pgolfo.contrasena_hash, "cedis2026")


def test_eliminar(api: TestClient, oficina: dict, db: Session) -> None:
    r = api.delete(f"{RUTA}/{usuario(db, 'embar.acruz').id}", headers=oficina)
    assert r.json() == {"resultado": "eliminado"}


@pytest.mark.parametrize(
    ("metodo", "cuerpo", "code"),
    [
        ("delete", None, "no_puedes_eliminarte"),
        ("patch", {"estado": "inactivo"}, "no_puedes_eliminarte"),
        ("patch", {"rol": "sucursal"}, "no_puedes_cambiar_tu_rol"),
    ],
)
def test_oficina_no_se_elimina_ni_se_quita_el_rol(
    api: TestClient, oficina: dict, db: Session, metodo: str, cuerpo: dict | None, code: str
) -> None:
    ruta = f"{RUTA}/{usuario(db, 'admin.cedis').id}"
    r = api.request(metodo.upper(), ruta, json=cuerpo, headers=oficina)
    assert r.status_code == 409
    assert r.json()["code"] == code


def test_oficina_si_edita_su_nombre(api: TestClient, oficina: dict, db: Session) -> None:
    ruta = f"{RUTA}/{usuario(db, 'admin.cedis').id}"
    r = api.patch(ruta, json={"nombre": "Ana Domínguez R.", "rol": "oficina"}, headers=oficina)
    assert r.json()["nombre"] == "Ana Domínguez R."


def test_solo_oficina(api: TestClient) -> None:
    assert api.get(RUTA, headers=entrar(api, "caseta.jlopez")).json()["code"] == "sin_permiso"


def test_contrasenas_temporales_distintas() -> None:
    assert len({contrasena_temporal() for _ in range(200)}) == 200
