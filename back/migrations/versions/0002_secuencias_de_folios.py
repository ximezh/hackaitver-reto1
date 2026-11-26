"""secuencias de folios

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-25 19:00:00

Una secuencia por tipo de folio y una por sucursal para las tarimas (ver app/folios.py).
Se listan aquí y no se importan de la app: una migración no cambia si la app cambia después.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SECUENCIAS = [
    "folio_oc",
    "folio_bulto",
    "folio_embarque",
    *(f"folio_tarima_{n:02d}" for n in range(1, 33)),
]


def upgrade() -> None:
    for nombre in SECUENCIAS:
        op.execute(f"CREATE SEQUENCE {nombre} START 1")


def downgrade() -> None:
    for nombre in SECUENCIAS:
        op.execute(f"DROP SEQUENCE {nombre}")
