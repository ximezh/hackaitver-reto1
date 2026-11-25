from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACK_DIR = Path(__file__).resolve().parent.parent


def usar_psycopg(url: str) -> str:
    """Los servicios administrados entregan `postgres://` o `postgresql://`; se usa psycopg 3."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


class Settings(BaseSettings):
    """Configuración leída de variables de entorno o de `back/.env`.

    `DATABASE_URL` no tiene valor por omisión: sin ella la API no arranca.
    """

    model_config = SettingsConfigDict(env_file=BACK_DIR / ".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("database_url")
    @classmethod
    def use_psycopg(cls, value: str) -> str:
        return usar_psycopg(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
