from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.db import get_session
from app.main import create_app


class FakeSession:
    def __init__(self, fails: bool) -> None:
        self.fails = fails

    def execute(self, _statement: object) -> None:
        if self.fails:
            raise OperationalError("SELECT 1", {}, Exception("sin servidor"))


def client_with(fails: bool) -> TestClient:
    app = create_app()

    def session() -> Iterator[FakeSession]:
        yield FakeSession(fails)

    app.dependency_overrides[get_session] = session
    return TestClient(app)


def test_health_reports_database_ok() -> None:
    response = client_with(fails=False).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_database_down() -> None:
    response = client_with(fails=True).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "sin conexión"}


@pytest.mark.parametrize("prefix", ["postgres://", "postgresql://"])
def test_settings_use_psycopg_driver(prefix: str) -> None:
    settings = Settings(database_url=f"{prefix}u:p@h:5432/db")
    assert settings.database_url == "postgresql+psycopg://u:p@h:5432/db"
