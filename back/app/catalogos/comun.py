"""Piezas que comparten los cuatro catálogos (contrato: docs/api/sprint-1.md · Catálogos)."""

import re
from typing import Any

from pydantic import BaseModel
from pydantic_core import PydanticCustomError
from sqlalchemy import ColumnElement, Select, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.errores import NO_ENCONTRADO, error

FK_VIOLADA = "23503"  # foreign_key_violation


class Lista[T](BaseModel):
    items: list[T]
    total: int


def falla(mensaje: str) -> PydanticCustomError:
    """Error de validación con el texto exacto del contrato."""
    return PydanticCustomError("validacion", mensaje)


def obligatorio(valor: Any, etiqueta: str) -> str:
    """Recorta el texto y falla con «Completa <etiqueta>» si queda vacío."""
    texto = valor.strip() if isinstance(valor, str) else valor
    if texto is None or texto == "":
        raise falla(f"Completa {etiqueta}")
    if not isinstance(texto, str):
        raise falla(f"{etiqueta} debe ser texto")
    return texto


def opcional(valor: Any) -> Any:
    """Recorta el texto; una cadena vacía se guarda como `None`."""
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


def _escapar(texto: str) -> str:
    return re.sub(r"([\\%_])", r"\\\1", texto)


def buscar(consulta: Select, q: str | None, *columnas: InstrumentedAttribute) -> Select:
    """Filtra por `q` en las columnas de texto, sin distinguir mayúsculas ni acentos."""
    if not q or not q.strip():
        return consulta
    patron = func.unaccent(f"%{_escapar(q.strip())}%")
    condiciones: list[ColumnElement[bool]] = [
        func.unaccent(c).ilike(patron, escape="\\") for c in columnas
    ]
    return consulta.where(or_(*condiciones))


def listar[M](session: Session, modelo: type[M], q: str | None, *columnas: Any) -> list[M]:
    consulta = buscar(select(modelo), q, *columnas).order_by(modelo.id)  # type: ignore[attr-defined]
    return list(session.scalars(consulta))


def obtener[M](session: Session, modelo: type[M], id_: int) -> M:
    registro = session.get(modelo, id_)
    if registro is None:
        raise error(NO_ENCONTRADO)
    return registro


def eliminar_o_desactivar(session: Session, registro: Any, esquema: type[BaseModel]) -> dict:
    """Borra el registro; si otro registro depende de él (historial), lo deja inactivo (H-11).

    Se borra con un DELETE directo y no con `session.delete()`: el ORM pondría en NULL las
    llaves de los registros relacionados (por ejemplo, los productos de un proveedor) antes de
    borrar, y la base nunca avisaría que el registro tiene dependientes.
    """
    modelo = type(registro)
    try:
        with session.begin_nested():
            session.execute(delete(modelo).where(modelo.id == registro.id))
    except IntegrityError as exc:
        if getattr(exc.orig, "sqlstate", None) != FK_VIOLADA:
            raise
        session.refresh(registro)
        registro.estado = "inactivo"
        session.commit()
        return {
            "resultado": "desactivado",
            "registro": esquema.model_validate(registro).model_dump(mode="json"),
        }
    session.expunge(registro)
    session.commit()
    return {"resultado": "eliminado"}
