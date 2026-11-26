"""Tokens de sesión firmados con HS256 (A-09).

El token solo identifica al usuario: el rol, el estado y la contraseña temporal se leen de la
base en cada petición. Así, desactivar a alguien o restablecer su contraseña surte efecto al
momento, aunque tenga un token vigente.
"""

from datetime import timedelta

import jwt

from app.config import get_settings
from app.errores import NO_AUTENTICADO, TOKEN_EXPIRADO, error
from app.models import Usuario
from app.tiempo import ahora

DURACION = timedelta(hours=12)  # un turno
ALGORITMO = "HS256"


def crear_token(usuario: Usuario) -> str:
    emitido = ahora()
    claims = {
        "sub": str(usuario.id),
        "rol": usuario.rol,
        "canal": usuario.canal,
        "iat": emitido,
        "exp": emitido + DURACION,
    }
    return jwt.encode(claims, get_settings().jwt_secret, algorithm=ALGORITMO)


def id_del_token(token: str) -> int:
    """Devuelve el id del usuario, o lanza `token_expirado` / `no_autenticado`."""
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[ALGORITMO],
            options={"require": ["sub", "exp"]},
        )
        return int(claims["sub"])
    except jwt.ExpiredSignatureError:
        raise error(TOKEN_EXPIRADO) from None
    except (jwt.InvalidTokenError, ValueError):
        raise error(NO_AUTENTICADO) from None


def segundos_de_vida() -> int:
    return int(DURACION.total_seconds())
