"""busqueda sin acentos

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-25 20:00:00

`unaccent` permite que `?q=cordoba` encuentre «Córdoba» en los catálogos (contrato · Listas).
Es una extensión de confianza: la puede crear el dueño de la base, sin superusuario.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
