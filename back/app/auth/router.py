"""Rutas de `/api/auth`: login, perfil y cambio de contraseña (BE-10, BE-15)."""

from fastapi import APIRouter
from sqlalchemy import func, select

from app.auth.dependencias import SesionDb, UsuarioEnSesion
from app.auth.esquemas import CambioContrasena, LoginEntrada, Perfil, Sesion
from app.auth.tokens import crear_token, segundos_de_vida
from app.contrasenas import hashear, verificar
from app.errores import ErrorApi, validacion
from app.models import Usuario
from app.models.comun import PREFIJO_DE_ROL, Estado, Rol

router = APIRouter(prefix="/auth", tags=["sesión"])

LONGITUD_MINIMA = 8
REVISA = "Revisa usuario y contraseña"

# Se verifica contra este hash cuando el usuario no existe, para que la respuesta tarde lo
# mismo y no revele qué usuarios existen.
_HASH_DE_RELLENO = hashear("relleno-para-usuarios-que-no-existen")


def _sesion(usuario: Usuario) -> Sesion:
    return Sesion.de(usuario, crear_token(usuario), segundos_de_vida())


@router.post("/login")
def login(datos: LoginEntrada, session: SesionDb) -> Sesion:
    nombre = datos.usuario.strip().lower()
    faltan = {
        campo: REVISA
        for campo, valor in (("usuario", nombre), ("contrasena", datos.contrasena))
        if not valor
    }
    if datos.canal is None:
        faltan["canal"] = REVISA
    if faltan:
        raise validacion(faltan)

    usuario = session.scalars(select(Usuario).where(func.lower(Usuario.usuario) == nombre)).first()
    if not verificar(usuario.contrasena_hash if usuario else _HASH_DE_RELLENO, datos.contrasena):
        raise ErrorApi(401, "credenciales_invalidas", REVISA)
    assert usuario is not None

    # Solo con la contraseña correcta se dice por qué no puede entrar.
    if usuario.estado != Estado.ACTIVO:
        raise ErrorApi(403, "usuario_inactivo", "Tu usuario está inactivo. Comunícate con Oficina")
    if usuario.canal != datos.canal:
        donde = "el teléfono" if Rol(usuario.rol) in PREFIJO_DE_ROL else "la web"
        raise ErrorApi(403, "canal_incorrecto", f"Este usuario entra desde {donde}")
    return _sesion(usuario)


@router.get("/me")
def perfil(usuario: UsuarioEnSesion) -> Perfil:
    """Perfil (P-10): quién es y su usuario. Responde también con contraseña temporal."""
    return Perfil.model_validate(usuario)


@router.post("/contrasena")
def cambiar_contrasena(
    datos: CambioContrasena, usuario: UsuarioEnSesion, session: SesionDb
) -> Sesion:
    """Cambia la contraseña y entrega un token nuevo, ya sin contraseña temporal (R-17)."""
    if not verificar(usuario.contrasena_hash, datos.actual):
        raise ErrorApi(400, "contrasena_actual_incorrecta", "La contraseña actual no coincide")
    if len(datos.nueva) < LONGITUD_MINIMA:
        raise validacion(
            {"nueva": f"La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres"}
        )
    if datos.nueva == datos.actual:
        raise validacion({"nueva": "La contraseña nueva debe ser distinta de la actual"})

    usuario.contrasena_hash = hashear(datos.nueva)
    usuario.contrasena_temporal = False
    session.commit()
    return _sesion(usuario)
