"""Elige y valida la base de PostgreSQL en la que corren las pruebas."""

from pydantic_settings import BaseSettings
from sqlalchemy.engine import make_url

from app.config import BACK_DIR, usar_psycopg


class BaseDePruebasError(Exception):
    """La configuración no permite correr las pruebas sin riesgo para la base de desarrollo."""


class _Urls(BaseSettings):
    # Mismo origen que la app: variables de entorno y luego `back/.env`.
    model_config = {"env_file": BACK_DIR / ".env", "extra": "ignore"}

    database_url: str | None = None
    test_database_url: str | None = None


def _misma_base(a: str, b: str) -> bool:
    ua, ub = make_url(a), make_url(b)
    return (ua.host, ua.port or 5432, ua.database) == (ub.host, ub.port or 5432, ub.database)


def url_de_pruebas(database_url: str | None, test_database_url: str | None) -> str:
    """Devuelve la URL de pruebas, o falla si falta o apunta a la base de desarrollo."""
    if not test_database_url:
        raise BaseDePruebasError(
            "Falta TEST_DATABASE_URL. Agrégala a back/.env (ver back/.env.example) "
            "con una base exclusiva para pruebas, por ejemplo "
            "postgresql://reto1:reto1@localhost:5432/reto1_test"
        )
    test_url = usar_psycopg(test_database_url)
    if database_url and _misma_base(usar_psycopg(database_url), test_url):
        raise BaseDePruebasError(
            "TEST_DATABASE_URL apunta a la misma base que DATABASE_URL. "
            "Las pruebas migran y escriben datos: usa una base distinta, como reto1_test."
        )
    return test_url


def url_de_pruebas_del_entorno() -> tuple[str | None, str]:
    """Lee las dos URL del entorno y devuelve `(DATABASE_URL, TEST_DATABASE_URL)` validadas."""
    urls = _Urls()
    return urls.database_url, url_de_pruebas(urls.database_url, urls.test_database_url)
