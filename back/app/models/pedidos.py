"""Pedido de sucursal y su OC, dividida en partes por proveedor (BE-20, R-16).

OrdenCompra (OC-26-…) ── sucursal
  └── ParteOc (OC por proveedor)    cada proveedor agenda, factura y entrega su parte
        └── LineaOc (producto, bultos)
"""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.catalogos import Producto, Proveedor, Sucursal

# Seguimiento en 6 pasos (R-14). El índice es el que pinta el front.
PASOS = ("oc_emitida", "proveedor", "en_cedis", "en_tarima", "en_camino", "recibido")


class OrdenCompra(Base):
    __tablename__ = "ordenes_compra"
    __table_args__ = (
        CheckConstraint("folio ~ '^OC-[0-9]{2}-[0-9]{4,}$'", name="folio_formato"),
        CheckConstraint("paso IN (" + ", ".join(f"'{p}'" for p in PASOS) + ")", name="paso"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    folio: Mapped[str] = mapped_column(String(16), unique=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id"), index=True)
    paso: Mapped[str] = mapped_column(String(12), default="oc_emitida")
    llega_estimado: Mapped[date | None]
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sucursal: Mapped[Sucursal] = relationship()
    partes: Mapped[list["ParteOc"]] = relationship(
        back_populates="oc", order_by="ParteOc.id", cascade="all, delete-orphan"
    )


class ParteOc(Base):
    """Lo que le toca a un proveedor dentro de una OC (relación muchos a muchos, R-16)."""

    __tablename__ = "partes_oc"
    __table_args__ = (UniqueConstraint("oc_id", "proveedor_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    oc_id: Mapped[int] = mapped_column(ForeignKey("ordenes_compra.id"), index=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), index=True)

    oc: Mapped[OrdenCompra] = relationship(back_populates="partes")
    proveedor: Mapped[Proveedor] = relationship()
    lineas: Mapped[list["LineaOc"]] = relationship(
        back_populates="parte", order_by="LineaOc.id", cascade="all, delete-orphan"
    )


class LineaOc(Base):
    __tablename__ = "lineas_oc"
    __table_args__ = (
        UniqueConstraint("parte_id", "producto_id"),
        CheckConstraint("bultos > 0", name="bultos_positivos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parte_id: Mapped[int] = mapped_column(ForeignKey("partes_oc.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    bultos: Mapped[int]

    parte: Mapped[ParteOc] = relationship(back_populates="lineas")
    producto: Mapped[Producto] = relationship()
