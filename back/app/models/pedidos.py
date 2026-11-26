"""Pedido de sucursal y su OC, dividida en partes por proveedor (BE-20, R-16).

OrdenCompra (OC-26-…) ── sucursal
  └── ParteOc (OC por proveedor)    cada proveedor agenda, factura y entrega su parte
        └── LineaOc (producto, bultos)
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.catalogos import Anden, Producto, Proveedor, Sucursal

# Seguimiento en 6 pasos (R-14). El índice es el que pinta el front.
PASOS = ("oc_emitida", "proveedor", "en_cedis", "en_tarima", "en_camino", "recibido")
ESTADOS_CITA = ("programada",)


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
    cita: Mapped["Cita | None"] = relationship(back_populates="parte")
    factura: Mapped["Factura | None"] = relationship(back_populates="parte")


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


class Cita(Base):
    __tablename__ = "citas"
    __table_args__ = (
        CheckConstraint("fin > inicio", name="fin_despues_de_inicio"),
        CheckConstraint(
            "estado IN (" + ", ".join(f"'{e}'" for e in ESTADOS_CITA) + ")", name="estado"
        ),
        # Dos citas no se empalman en el mismo andén (R-03, A-08), aunque se confirmen al mismo
        # tiempo. `[)`: una cita puede empezar justo cuando termina la anterior.
        ExcludeConstraint(
            ("anden_id", "="),
            (func.tstzrange(text("inicio"), text("fin"), text("'[)'")), "&&"),
            name="ex_citas_sin_empalme",
            using="gist",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # `unique`: una parte de OC tiene una sola cita.
    parte_id: Mapped[int] = mapped_column(ForeignKey("partes_oc.id"), unique=True)
    anden_id: Mapped[int] = mapped_column(ForeignKey("andenes.id"))
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(12), default="programada")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parte: Mapped[ParteOc] = relationship(back_populates="cita")
    anden: Mapped[Anden] = relationship()


class Factura(Base):
    """La factura del proveedor para su parte de la OC. El folio lo captura él (R-04)."""

    __tablename__ = "facturas"
    __table_args__ = (CheckConstraint("folio ~ '^FAC-'", name="folio_prefijo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    folio: Mapped[str] = mapped_column(String(30), index=True)
    parte_id: Mapped[int] = mapped_column(ForeignKey("partes_oc.id"), unique=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parte: Mapped[ParteOc] = relationship(back_populates="factura")
    productos: Mapped[list["FacturaProducto"]] = relationship(
        back_populates="factura", cascade="all, delete-orphan"
    )


class FacturaProducto(Base):
    """El folio queda registrado para cada producto de la parte (R-04, P-02).

    Una factura cubre varios productos, pero el mismo folio no se registra dos veces para el
    mismo producto, sea del proveedor que sea.
    """

    __tablename__ = "factura_productos"
    __table_args__ = (
        UniqueConstraint("folio", "producto_id"),
        UniqueConstraint("factura_id", "producto_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"))
    folio: Mapped[str] = mapped_column(String(30))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))

    factura: Mapped[Factura] = relationship(back_populates="productos")
