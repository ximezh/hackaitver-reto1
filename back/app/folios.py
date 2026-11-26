"""Folios con prefijo respaldados por secuencias de PostgreSQL (R-12, BE-04).

| Folio | Formato | Ejemplo del prototipo | Secuencia |
|---|---|---|---|
| Orden de compra | `OC-<aa>-<n>` | `OC-26-1182` | `folio_oc` |
| Bulto | `B-<n>` | `B-0003` | `folio_bulto` |
| Tarima | `T-<clave de sucursal>-<n>` | `T-07-03` | `folio_tarima_<clave>`, una por sucursal |
| Embarque | `EMB-<n>` | `EMB-0412` | `folio_embarque` |

Las secuencias no se repiten aunque dos peticiones pidan folio al mismo tiempo, y no se
reutilizan si una transacción se deshace: puede haber huecos, pero nunca duplicados.
Cuando el número supera los dígitos del formato, el folio crece (`B-10000`).

`FAC-` no se genera: el folio de factura lo captura el proveedor (R-04).
"""

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import tiempo

CLAVES_DE_SUCURSAL = [f"{n:02d}" for n in range(1, 33)]  # una por rack (R-15)
SECUENCIAS = [
    "folio_oc",
    "folio_bulto",
    "folio_embarque",
    *(f"folio_tarima_{c}" for c in CLAVES_DE_SUCURSAL),
]


def _siguiente(session: Session, secuencia: str) -> int:
    return session.execute(select(func.nextval(secuencia))).scalar_one()


def folio_oc(session: Session) -> str:
    """`OC-<aa>-<n>`: el año es el de la operación en México; el número no se reinicia."""
    return f"OC-{tiempo.ahora():%y}-{_siguiente(session, 'folio_oc'):04d}"


def folio_bulto(session: Session) -> str:
    return f"B-{_siguiente(session, 'folio_bulto'):04d}"


def folio_embarque(session: Session) -> str:
    return f"EMB-{_siguiente(session, 'folio_embarque'):04d}"


def folio_tarima(session: Session, clave_sucursal: str) -> str:
    """`T-<clave>-<n>`: cada sucursal numera sus tarimas por separado."""
    if not re.fullmatch(r"0[1-9]|[12][0-9]|3[0-2]", clave_sucursal):
        raise ValueError(f"Clave de sucursal inválida: {clave_sucursal!r}")
    n = _siguiente(session, f"folio_tarima_{clave_sucursal}")
    return f"T-{clave_sucursal}-{n:02d}"
