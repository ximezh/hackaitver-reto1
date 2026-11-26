"""BE-04: folios con prefijo respaldados por secuencias y fechas en America/Mexico_City."""

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import folios, tiempo
from app.db import get_engine
from app.tiempo import FechaHora, a_local, ahora


def test_formatos_del_prototipo(db: Session) -> None:
    assert re.fullmatch(r"OC-\d{2}-\d{4,}", folios.folio_oc(db))
    assert re.fullmatch(r"B-\d{4,}", folios.folio_bulto(db))
    assert re.fullmatch(r"EMB-\d{4,}", folios.folio_embarque(db))
    assert re.fullmatch(r"T-07-\d{2,}", folios.folio_tarima(db, "07"))


def test_oc_lleva_el_anio_de_la_operacion(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    # 05:30 UTC del 1 de enero de 2027 son las 23:30 del 31 de diciembre de 2026 en México.
    monkeypatch.setattr(tiempo, "ahora", lambda: a_local(datetime(2027, 1, 1, 5, 30, tzinfo=UTC)))
    assert folios.folio_oc(db).startswith("OC-26-")


def test_folios_consecutivos(db: Session) -> None:
    a, b = folios.folio_bulto(db), folios.folio_bulto(db)
    assert int(b.removeprefix("B-")) == int(a.removeprefix("B-")) + 1


def test_cada_sucursal_numera_sus_tarimas(db: Session) -> None:
    t07a, t12, t07b = (folios.folio_tarima(db, c) for c in ("07", "12", "07"))
    n = lambda f: int(f.rsplit("-", 1)[1])  # noqa: E731
    assert n(t07b) == n(t07a) + 1
    assert t12.startswith("T-12-")


@pytest.mark.parametrize("clave", ["00", "33", "7", "07; DROP SEQUENCE folio_oc"])
def test_tarima_rechaza_claves_invalidas(db: Session, clave: str) -> None:
    with pytest.raises(ValueError, match="Clave de sucursal"):
        folios.folio_tarima(db, clave)


def test_existen_todas_las_secuencias(db: Session) -> None:
    existentes = set(
        db.scalars(text("SELECT sequence_name FROM information_schema.sequences")).all()
    )
    assert set(folios.SECUENCIAS) <= existentes
    assert len(folios.SECUENCIAS) == 35


def test_folios_concurrentes_no_se_repiten() -> None:
    # Cada hilo con su propia conexión, como dos peticiones al mismo tiempo.
    def pedir(_: int) -> list[str]:
        with Session(get_engine()) as s:
            return [folios.folio_embarque(s) for _ in range(20)]

    with ThreadPoolExecutor(max_workers=4) as pool:
        todos = [f for lote in pool.map(pedir, range(4)) for f in lote]
    assert len(todos) == len(set(todos)) == 80


def test_ahora_en_la_zona_de_la_operacion() -> None:
    assert str(ahora().tzinfo) == "America/Mexico_City"
    assert ahora().utcoffset().total_seconds() == -6 * 3600  # type: ignore[union-attr]


def test_la_sesion_de_postgresql_usa_la_zona(db: Session) -> None:
    assert db.scalar(text("SHOW timezone")) == "America/Mexico_City"


def test_fechahora_sale_con_desfase_de_mexico() -> None:
    class Respuesta(BaseModel):
        creado_en: FechaHora

    r = Respuesta(creado_en=datetime(2026, 11, 25, 15, 30, tzinfo=UTC))
    assert r.model_dump(mode="json") == {"creado_en": "2026-11-25T09:30:00-06:00"}


def test_fecha_sin_zona_se_toma_como_utc() -> None:
    assert a_local(datetime(2026, 11, 25, 15, 30)).isoformat() == "2026-11-25T09:30:00-06:00"
