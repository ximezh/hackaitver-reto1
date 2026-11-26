"""Días hábiles del CEDIS: de lunes a sábado (R-02)."""

from datetime import date, timedelta

DOMINGO = 6


def es_habil(dia: date) -> bool:
    return dia.weekday() != DOMINGO


def dias_habiles_despues(desde: date, n: int) -> date:
    """El día hábil número `n` después de `desde` (sin contar `desde`)."""
    dia = desde
    while n > 0:
        dia += timedelta(days=1)
        if es_habil(dia):
            n -= 1
    return dia


# Estimación de «Llega …» antes del embarque (contrato C2-02).
DIAS_HABILES_AL_CREAR = 3
