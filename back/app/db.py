from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings
from app.tiempo import ZONA_NOMBRE

# Nombres fijos para índices y restricciones: Alembic los genera igual en cada máquina y la API
# puede reconocer qué regla falló (por ejemplo `uq_productos_sku`).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base de los modelos. Alembic lee su `metadata` para generar migraciones."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


@lru_cache
def get_engine(url: str | None = None) -> Engine:
    return create_engine(
        url or get_settings().database_url,
        pool_pre_ping=True,
        # La sesión usa la zona de la operación: `now()::date` es el día del CEDIS.
        connect_args={"options": f"-c timezone={ZONA_NOMBRE}"},
    )


def get_session() -> Iterator[Session]:
    factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    with factory() as session:
        yield session
