from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACK_DIR = Path(__file__).resolve().parent.parent


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
        # Los servicios administrados entregan `postgres://` o `postgresql://`.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
