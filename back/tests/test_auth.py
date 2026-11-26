"""BE-10: login por rol y canal, perfil y protección de rutas por rol."""

from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import tokens
from app.auth.dependencias import Oficina
from app.config import JWT_SECRET_DESARROLLO, Settings, get_settings
from app.models import Usuario
from app.tiempo import ahora
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("semillas")


def login(api: TestClient, usuario: str, contrasena: str = "cedis2026", canal: str = "web"):
    return api.post(
        "/api/auth/login", json={"usuario": usuario, "contrasena": contrasena, "canal": canal}
    )


# --- Login -----------------------------------------------------------------------------


def test_login_de_oficina_como_el_contrato(api: TestClient) -> None:
    r = login(api, "admin.cedis")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["expira_en"] == 43200
    assert cuerpo["contrasena_temporal"] is False
    assert {k: v for k, v in cuerpo["usuario"].items() if k != "id"} == {
        "usuario": "admin.cedis",
        "nombre": "Ana Domínguez",
        "rol": "oficina",
        "canal": "web",
        "contrasena_temporal": False,
        "sucursal": None,
        "proveedor": None,
    }


@pytest.mark.parametrize(
    ("usuario", "rol"),
    [("caseta.jlopez", "caseta"), ("desem.mruiz", "desembarque"), ("embar.acruz", "embarque")],
)
def test_roles_de_android_entran_por_el_telefono(api: TestClient, usuario: str, rol: str) -> None:
    r = login(api, usuario, canal="android")
    assert r.status_code == 200
    assert (r.json()["usuario"]["rol"], r.json()["usuario"]["canal"]) == (rol, "android")


def test_usuario_sin_distinguir_mayusculas_ni_espacios(api: TestClient) -> None:
    assert login(api, "  Admin.CEDIS ").status_code == 200


def test_el_rol_sale_de_la_base_y_no_del_token(api: TestClient) -> None:
    claims = jwt.decode(
        login(api, "suc07").json()["access_token"], options={"verify_signature": False}
    )
    assert claims["rol"] == "sucursal"
    assert claims["canal"] == "web"


@pytest.mark.parametrize(
    ("usuario", "contrasena"),
    [("admin.cedis", "otra"), ("nadie", "cedis2026"), ("caseta.jlopez", "")],
)
def test_credenciales_invalidas(api: TestClient, usuario: str, contrasena: str) -> None:
    r = login(api, usuario, contrasena, canal="android" if "." in usuario else "web")
    if contrasena:
        assert r.status_code == 401
        assert r.json() == {
            "detail": "Revisa usuario y contraseña",
            "code": "credenciales_invalidas",
        }
    else:
        assert r.status_code == 422
        assert r.json()["detail"] == "Revisa usuario y contraseña"


def test_campos_faltantes(api: TestClient) -> None:
    r = api.post("/api/auth/login", json={})
    assert r.status_code == 422
    assert r.json() == {
        "detail": "Revisa usuario y contraseña",
        "code": "validacion",
        "campos": {
            "usuario": "Revisa usuario y contraseña",
            "contrasena": "Revisa usuario y contraseña",
            "canal": "Revisa usuario y contraseña",
        },
    }


def test_rol_de_android_no_entra_por_la_web(api: TestClient) -> None:
    r = login(api, "caseta.jlopez", canal="web")
    assert r.status_code == 403
    assert r.json() == {
        "detail": "Este usuario entra desde el teléfono",
        "code": "canal_incorrecto",
    }


def test_rol_web_no_entra_por_el_telefono(api: TestClient) -> None:
    r = login(api, "pgolfo", canal="android")
    assert r.status_code == 403
    assert r.json() == {"detail": "Este usuario entra desde la web", "code": "canal_incorrecto"}


def test_usuario_inactivo_no_entra(api: TestClient, db: Session) -> None:
    db.scalars(select(Usuario).filter_by(usuario="suc07")).one().estado = "inactivo"
    db.flush()
    r = login(api, "suc07")
    assert r.status_code == 403
    assert r.json()["code"] == "usuario_inactivo"


def test_inactivo_o_canal_solo_con_la_contrasena_correcta(api: TestClient, db: Session) -> None:
    db.scalars(select(Usuario).filter_by(usuario="suc07")).one().estado = "inactivo"
    db.flush()
    assert login(api, "suc07", "mal").json()["code"] == "credenciales_invalidas"
    assert login(api, "caseta.jlopez", "mal", "web").json()["code"] == "credenciales_invalidas"


# --- Perfil y sesión -------------------------------------------------------------------


def test_perfil_de_sucursal(api: TestClient) -> None:
    r = api.get("/api/auth/me", headers=entrar(api, "suc07"))
    assert r.status_code == 200
    assert r.json()["sucursal"] | {"id": 0} == {
        "id": 0,
        "clave": "07",
        "nombre": "Suc. 07 Boca del Río",
    }
    assert r.json()["proveedor"] is None


def test_perfil_de_proveedor(api: TestClient) -> None:
    r = api.get("/api/auth/me", headers=entrar(api, "pgolfo"))
    proveedor = r.json()["proveedor"]
    assert (proveedor["rfc"], proveedor["nombre"]) == ("PGO090312AB1", "Papelera del Golfo")


def test_sin_token(api: TestClient) -> None:
    r = api.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json() == {"detail": "Inicia sesión para continuar", "code": "no_autenticado"}


@pytest.mark.parametrize("valor", ["Bearer basura", "Basic abc", "Bearer "])
def test_token_invalido(api: TestClient, valor: str) -> None:
    r = api.get("/api/auth/me", headers={"Authorization": valor})
    assert r.status_code == 401
    assert r.json()["code"] == "no_autenticado"


def test_token_firmado_con_otro_secreto(api: TestClient, db: Session) -> None:
    usuario = db.scalars(select(Usuario).filter_by(usuario="admin.cedis")).one()
    falso = jwt.encode({"sub": str(usuario.id), "exp": ahora() + timedelta(hours=1)}, "x" * 40)
    r = api.get("/api/auth/me", headers={"Authorization": f"Bearer {falso}"})
    assert r.json()["code"] == "no_autenticado"


def test_token_expirado(api: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tokens, "DURACION", timedelta(seconds=-1))
    encabezado = entrar(api, "admin.cedis")
    r = api.get("/api/auth/me", headers=encabezado)
    assert r.status_code == 401
    assert r.json() == {
        "detail": "Tu sesión terminó. Inicia sesión de nuevo",
        "code": "token_expirado",
    }


def test_desactivar_cierra_la_sesion_al_momento(api: TestClient, db: Session) -> None:
    encabezado = entrar(api, "suc07")
    db.scalars(select(Usuario).filter_by(usuario="suc07")).one().estado = "inactivo"
    db.flush()
    assert api.get("/api/auth/me", headers=encabezado).json()["code"] == "no_autenticado"


# --- requiere_rol ----------------------------------------------------------------------


def test_requiere_rol(api: TestClient) -> None:
    @api.app.get("/api/prueba/solo-oficina")  # type: ignore[attr-defined]
    def solo_oficina(usuario: Oficina) -> dict[str, str]:
        return {"usuario": usuario.usuario}

    sin = api.get("/api/prueba/solo-oficina")
    assert sin.json()["code"] == "no_autenticado"
    otro = api.get("/api/prueba/solo-oficina", headers=entrar(api, "suc07"))
    assert otro.status_code == 403
    assert otro.json() == {"detail": "No tienes acceso a esta sección", "code": "sin_permiso"}
    ok = api.get("/api/prueba/solo-oficina", headers=entrar(api, "admin.cedis"))
    assert ok.json() == {"usuario": "admin.cedis"}


# --- Secreto de los tokens -------------------------------------------------------------


def test_produccion_exige_jwt_secret() -> None:
    url = "postgresql://u:p@h/db"
    with pytest.raises(ValueError, match="JWT_SECRET es obligatorio"):
        Settings(app_env="production", database_url=url)
    with pytest.raises(ValueError, match="al menos 32"):
        Settings(app_env="production", database_url=url, jwt_secret="corto")
    Settings(app_env="production", database_url=url, jwt_secret="s" * 32)


def test_desarrollo_usa_el_secreto_de_desarrollo() -> None:
    assert get_settings().jwt_secret == JWT_SECRET_DESARROLLO
