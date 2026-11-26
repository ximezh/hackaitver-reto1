"""BE-15: contraseña temporal obligatoria de cambiar en el primer inicio de sesión (R-17)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencias import UsuarioActual
from app.contrasenas import hashear, verificar
from app.models import Usuario

TEMPORAL = "Tmp-7Kq2-xW9p"

pytestmark = pytest.mark.usefixtures("semillas")


@pytest.fixture
def nuevo(db: Session) -> Usuario:
    """Usuario recién creado por Oficina, con contraseña temporal."""
    usuario = Usuario(
        usuario="caseta.rgomez",
        nombre="Rosa Gómez",
        rol="caseta",
        canal="android",
        contrasena_hash=hashear(TEMPORAL),
        contrasena_temporal=True,
    )
    db.add(usuario)
    db.flush()
    return usuario


def entrar_temporal(api: TestClient) -> tuple[dict, dict[str, str]]:
    r = api.post(
        "/api/auth/login",
        json={"usuario": "caseta.rgomez", "contrasena": TEMPORAL, "canal": "android"},
    )
    assert r.status_code == 200
    return r.json(), {"Authorization": f"Bearer {r.json()['access_token']}"}


def cambiar(api: TestClient, encabezado: dict[str, str], actual: str, nueva: str):
    return api.post(
        "/api/auth/contrasena", headers=encabezado, json={"actual": actual, "nueva": nueva}
    )


@pytest.fixture
def ruta_protegida(api: TestClient) -> str:
    @api.app.get("/api/prueba/protegida")  # type: ignore[attr-defined]
    def protegida(usuario: UsuarioActual) -> dict[str, str]:
        return {"usuario": usuario.usuario}

    return "/api/prueba/protegida"


@pytest.mark.usefixtures("nuevo")
def test_el_login_avisa_que_la_contrasena_es_temporal(api: TestClient) -> None:
    sesion, _ = entrar_temporal(api)
    assert sesion["contrasena_temporal"] is True
    assert sesion["usuario"]["contrasena_temporal"] is True


@pytest.mark.usefixtures("nuevo")
def test_con_contrasena_temporal_solo_perfil_y_cambio(api: TestClient, ruta_protegida: str) -> None:
    _, encabezado = entrar_temporal(api)
    r = api.get(ruta_protegida, headers=encabezado)
    assert r.status_code == 403
    assert r.json() == {
        "detail": "Cambia tu contraseña para continuar",
        "code": "cambio_contrasena_requerido",
    }
    perfil = api.get("/api/auth/me", headers=encabezado)
    assert perfil.status_code == 200
    assert {k: perfil.json()[k] for k in ("nombre", "usuario", "rol")} == {
        "nombre": "Rosa Gómez",
        "usuario": "caseta.rgomez",
        "rol": "caseta",
    }


def test_cambiar_la_contrasena_temporal(
    api: TestClient, db: Session, nuevo: Usuario, ruta_protegida: str
) -> None:
    _, encabezado = entrar_temporal(api)
    r = cambiar(api, encabezado, TEMPORAL, "MiClaveSegura26")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["contrasena_temporal"] is False
    assert cuerpo["usuario"]["contrasena_temporal"] is False

    db.refresh(nuevo)
    assert verificar(nuevo.contrasena_hash, "MiClaveSegura26")
    assert not verificar(nuevo.contrasena_hash, TEMPORAL)

    nuevo_token = {"Authorization": f"Bearer {cuerpo['access_token']}"}
    assert api.get(ruta_protegida, headers=nuevo_token).json() == {"usuario": "caseta.rgomez"}
    # La temporal ya no sirve para entrar.
    viejo = api.post(
        "/api/auth/login",
        json={"usuario": "caseta.rgomez", "contrasena": TEMPORAL, "canal": "android"},
    )
    assert viejo.json()["code"] == "credenciales_invalidas"


@pytest.mark.usefixtures("nuevo")
def test_contrasena_actual_incorrecta(api: TestClient) -> None:
    _, encabezado = entrar_temporal(api)
    r = cambiar(api, encabezado, "otra", "MiClaveSegura26")
    assert r.status_code == 400
    assert r.json() == {
        "detail": "La contraseña actual no coincide",
        "code": "contrasena_actual_incorrecta",
    }


@pytest.mark.usefixtures("nuevo")
@pytest.mark.parametrize(
    ("nueva", "mensaje"),
    [
        ("corta7!", "La contraseña debe tener al menos 8 caracteres"),
        (TEMPORAL, "La contraseña nueva debe ser distinta de la actual"),
    ],
)
def test_reglas_de_la_contrasena_nueva(api: TestClient, nueva: str, mensaje: str) -> None:
    _, encabezado = entrar_temporal(api)
    r = cambiar(api, encabezado, TEMPORAL, nueva)
    assert r.status_code == 422
    assert r.json() == {"detail": mensaje, "code": "validacion", "campos": {"nueva": mensaje}}


@pytest.mark.usefixtures("nuevo")
def test_campos_vacios(api: TestClient) -> None:
    _, encabezado = entrar_temporal(api)
    r = cambiar(api, encabezado, "", "")
    assert r.json()["campos"] == {
        "actual": "Completa Contraseña actual",
        "nueva": "Completa Contraseña nueva",
    }


def test_cambio_voluntario_sin_temporal(api: TestClient, db: Session) -> None:
    from tests.conftest import entrar

    encabezado = entrar(api, "admin.cedis")
    assert cambiar(api, encabezado, "cedis2026", "OtraClave2026").status_code == 200
    admin = db.scalars(select(Usuario).filter_by(usuario="admin.cedis")).one()
    assert verificar(admin.contrasena_hash, "OtraClave2026")


def test_cambio_requiere_sesion(api: TestClient) -> None:
    r = api.post("/api/auth/contrasena", json={"actual": "a", "nueva": "bbbbbbbb"})
    assert r.json()["code"] == "no_autenticado"


def test_restablecer_bloquea_la_sesion_abierta(
    api: TestClient, db: Session, ruta_protegida: str
) -> None:
    from tests.conftest import entrar

    encabezado = entrar(api, "suc07")
    db.scalars(select(Usuario).filter_by(usuario="suc07")).one().contrasena_temporal = True
    db.flush()
    assert api.get(ruta_protegida, headers=encabezado).json()["code"] == (
        "cambio_contrasena_requerido"
    )
