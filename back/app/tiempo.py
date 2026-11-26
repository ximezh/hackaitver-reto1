"""Fechas de la operación en `America/Mexico_City` (S-06, BE-04).

En la base las fechas se guardan con zona (`timestamptz`); la conexión usa la zona de la
operación para que `now()::date` sea el día del CEDIS. En las respuestas, `FechaHora` sale
en ISO 8601 con el desfase de México: `2026-11-25T09:30:00-06:00`.
"""

from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import PlainSerializer

ZONA_NOMBRE = "America/Mexico_City"
ZONA = ZoneInfo(ZONA_NOMBRE)


def ahora() -> datetime:
    return datetime.now(ZONA)


def hoy() -> date:
    return ahora().date()


def a_local(momento: datetime) -> datetime:
    """Pasa a la zona de la operación. Una fecha sin zona se toma como UTC."""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=ZoneInfo("UTC"))
    return momento.astimezone(ZONA)


# Tipo para los esquemas de respuesta.
FechaHora = Annotated[
    datetime, PlainSerializer(lambda m: a_local(m).isoformat(timespec="seconds"), return_type=str)
]
