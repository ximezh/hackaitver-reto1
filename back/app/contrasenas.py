"""Hash y verificación de contraseñas con Argon2id (A-09)."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def hashear(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def verificar(contrasena_hash: str, contrasena: str) -> bool:
    try:
        return _hasher.verify(contrasena_hash, contrasena)
    except (VerificationError, InvalidHashError):
        return False
