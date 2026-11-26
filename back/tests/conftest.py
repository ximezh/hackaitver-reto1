"""Las pruebas corren contra PostgreSQL real, en la base de TEST_DATABASE_URL.

Antes de recolectar las pruebas se valida la URL, la app se apunta a esa base y se aplica la
última migración. `app.main` no se importa aquí: debe importarse ya con la URL de pruebas.
"""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.config import BACK_DIR, get_settings
from app.db import get_engine
from tests.base_de_pruebas import BaseDePruebasError, url_de_pruebas_del_entorno


def pytest_sessionstart(session: pytest.Session) -> None:
    try:
        _, test_url = url_de_pruebas_del_entorno()
    except BaseDePruebasError as error:
        pytest.exit(str(error), returncode=pytest.ExitCode.USAGE_ERROR)

    # Desde aquí la app, Alembic y las pruebas solo ven la base de pruebas.
    os.environ["DATABASE_URL"] = test_url
    os.environ["APP_ENV"] = "test"
    get_settings.cache_clear()
    get_engine.cache_clear()

    # Sin límite, psycopg puede esperar indefinidamente a un servidor que no responde.
    sonda = create_engine(test_url, connect_args={"connect_timeout": 5}, poolclass=NullPool)
    try:
        with sonda.connect():
            pass
    except OperationalError as error:
        pytest.exit(
            "No se pudo conectar a la base de pruebas. ¿Está corriendo "
            f"`podman compose up -d` y existe la base?\n{error.orig}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    finally:
        sonda.dispose()

    command.upgrade(Config(BACK_DIR / "alembic.ini"), "head")


@pytest.fixture
def db() -> Iterator[Session]:
    """Sesión dentro de una transacción que se deshace al final: cada prueba empieza limpia.

    `create_savepoint` permite que el código probado haga `commit()` sin escapar de ella.
    """
    with get_engine().connect() as conn, conn.begin() as trans:
        session = Session(bind=conn, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            trans.rollback()
