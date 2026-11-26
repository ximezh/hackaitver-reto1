"""Dependencias para proteger rutas: sesión, contraseña temporal y rol (BE-10, BE-15).

    @router.get("/productos")
    def listar(oficina: Oficina) -> ...

- `usuario_en_sesion`: cualquier usuario con sesión vigente y activo, también con contraseña
  temporal. Solo la usan `GET /api/auth/me` y `POST /api/auth/contrasena`.
- `usuario_actual`: además exige que ya haya cambiado su contraseña temporal (R-17).
- `requiere_rol(...)`: además exige uno de los roles indicados.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.tokens import id_del_token
from app.db import get_session
from app.errores import CAMBIO_CONTRASENA, NO_AUTENTICADO, SIN_PERMISO, error
from app.models import Usuario
from app.models.comun import Estado, Rol

# `auto_error=False`: el 401 lo arma la API con el formato del contrato.
_bearer = HTTPBearer(auto_error=False, description="Token de `POST /api/auth/login`")

SesionDb = Annotated[Session, Depends(get_session)]


def usuario_en_sesion(
    session: SesionDb,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Usuario:
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise error(NO_AUTENTICADO)
    usuario = session.get(Usuario, id_del_token(credenciales.credentials))
    # Un usuario borrado o desactivado pierde la sesión aunque su token siga vigente.
    if usuario is None or usuario.estado != Estado.ACTIVO:
        raise error(NO_AUTENTICADO)
    return usuario


UsuarioEnSesion = Annotated[Usuario, Depends(usuario_en_sesion)]


def usuario_actual(usuario: UsuarioEnSesion) -> Usuario:
    """Mientras la contraseña sea temporal, solo se permiten el perfil y el cambio (R-17)."""
    if usuario.contrasena_temporal:
        raise error(CAMBIO_CONTRASENA)
    return usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]


def requiere_rol(*roles: Rol) -> Callable[[Usuario], Usuario]:
    permitidos = {r.value for r in roles}

    def dependencia(usuario: UsuarioActual) -> Usuario:
        if usuario.rol not in permitidos:
            raise error(SIN_PERMISO)
        return usuario

    return dependencia


Oficina = Annotated[Usuario, Depends(requiere_rol(Rol.OFICINA))]
