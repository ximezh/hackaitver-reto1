import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.config import get_settings
from app.db import get_engine
from app.main import create_app
from tests.base_de_pruebas import BaseDePruebasError, url_de_pruebas

DEV = "postgresql://reto1:reto1@localhost:5432/reto1"
TEST = "postgresql://reto1:reto1@localhost:5432/reto1_test"


def test_falla_si_falta_test_database_url() -> None:
    with pytest.raises(BaseDePruebasError, match="Falta TEST_DATABASE_URL"):
        url_de_pruebas(DEV, None)


@pytest.mark.parametrize(
    "test_url",
    [
        DEV,
        "postgres://otro:clave@localhost/reto1",  # mismo servidor y base con otro usuario
        "postgresql+psycopg://reto1:reto1@localhost:5432/reto1",
    ],
)
def test_falla_si_apunta_a_la_base_de_desarrollo(test_url: str) -> None:
    with pytest.raises(BaseDePruebasError, match="misma base que DATABASE_URL"):
        url_de_pruebas(DEV, test_url)


def test_acepta_una_base_distinta_y_usa_psycopg() -> None:
    assert url_de_pruebas(DEV, TEST) == "postgresql+psycopg://reto1:reto1@localhost:5432/reto1_test"


def test_acepta_test_database_url_sin_database_url() -> None:
    # En CI puede existir solo la base de pruebas.
    assert url_de_pruebas(None, TEST).endswith("/reto1_test")


def test_las_pruebas_usan_la_base_de_pruebas_migrada() -> None:
    assert get_settings().app_env == "test"
    with get_engine().connect() as conn:
        assert conn.execute(text("SELECT current_database()")).scalar_one().endswith("_test")
        assert "alembic_version" in inspect(conn).get_table_names()


def test_health_con_postgresql_real() -> None:
    response = TestClient(create_app()).get("/api/health")
    assert response.json() == {"status": "ok", "database": "ok"}
