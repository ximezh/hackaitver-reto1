"""Piezas que comparten los modelos: valores fijos y marcas de tiempo."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class Rol(StrEnum):
    CASETA = "caseta"
    DESEMBARQUE = "desembarque"
    EMBARQUE = "embarque"
    SUCURSAL = "sucursal"
    PROVEEDOR = "proveedor"
    OFICINA = "oficina"


class Canal(StrEnum):
    ANDROID = "android"
    WEB = "web"


# El rol define el canal y, en Android, el prefijo obligatorio del usuario (R-01).
CANAL_DE_ROL: dict[Rol, Canal] = {
    Rol.CASETA: Canal.ANDROID,
    Rol.DESEMBARQUE: Canal.ANDROID,
    Rol.EMBARQUE: Canal.ANDROID,
    Rol.SUCURSAL: Canal.WEB,
    Rol.PROVEEDOR: Canal.WEB,
    Rol.OFICINA: Canal.WEB,
}
PREFIJO_DE_ROL: dict[Rol, str] = {
    Rol.CASETA: "caseta.",
    Rol.DESEMBARQUE: "desem.",
    Rol.EMBARQUE: "embar.",
}


class EstadoProveedor(StrEnum):
    ACTIVO = "activo"
    SUSPENDIDO = "suspendido"
    INACTIVO = "inactivo"


class Estado(StrEnum):
    """Estado de productos, sucursales y usuarios. `inactivo` reemplaza al borrado (H-11)."""

    ACTIVO = "activo"
    INACTIVO = "inactivo"


class TipoAnden(StrEnum):
    RECIBO = "recibo"
    EMBARQUE = "embarque"


def en_lista(columna: str, valores: type[StrEnum], nombre: str) -> CheckConstraint:
    """`CHECK (columna IN (...))`. Se usa texto en lugar de ENUM nativo para migrar sin dolor."""
    lista = ", ".join(f"'{v.value}'" for v in valores)
    return CheckConstraint(f"{columna} IN ({lista})", name=nombre)


class ConFechas:
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
