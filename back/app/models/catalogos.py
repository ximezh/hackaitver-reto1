"""Catálogos de Oficina e instalaciones del CEDIS (BE-02)."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.comun import ConFechas, Estado, EstadoProveedor, TipoAnden, en_lista

# Claves de 01 a 32: el CEDIS tiene 32 racks y cada sucursal ocupa el de su clave (R-15).
CLAVE_01_32 = "(0[1-9]|[12][0-9]|3[0-2])"
ILUSTRACIONES_DE_PRODUCTO = ("bulto", "hojas", "lapices", "clips")


class Proveedor(ConFechas, Base):
    __tablename__ = "proveedores"
    __table_args__ = (
        # Formato del SAT: 3 letras (moral) o 4 (física), fecha AAMMDD y homoclave.
        CheckConstraint("rfc ~ '^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$'", name="rfc_formato"),
        en_lista("estado", EstadoProveedor, "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rfc: Mapped[str] = mapped_column(String(13), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    contacto: Mapped[str | None] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(12), default=EstadoProveedor.ACTIVO)

    productos: Mapped[list["Producto"]] = relationship(back_populates="proveedor")


class Producto(ConFechas, Base):
    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint("sku ~ '^[A-Z0-9-]{3,20}$'", name="sku_formato"),
        CheckConstraint("piezas_por_bulto > 0", name="piezas_positivas"),
        CheckConstraint("kg > 0", name="kg_positivo"),
        CheckConstraint("m3 > 0", name="m3_positivo"),
        CheckConstraint(
            "ilustracion IN (" + ", ".join(f"'{i}'" for i in ILUSTRACIONES_DE_PRODUCTO) + ")",
            name="ilustracion",
        ),
        en_lista("estado", Estado, "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    ilustracion: Mapped[str] = mapped_column(String(20), default="bulto")
    unidad: Mapped[str] = mapped_column(String(30), default="piezas")
    piezas_por_bulto: Mapped[int]
    # Peso y volumen de un bulto: un decimal en kg y tres en m³, como el prototipo.
    kg: Mapped[Decimal] = mapped_column(Numeric(7, 1))
    m3: Mapped[Decimal] = mapped_column(Numeric(6, 3))
    # Proveedor principal: el que se usa al crear la OC (A-16).
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id"), index=True)
    estado: Mapped[str] = mapped_column(String(10), default=Estado.ACTIVO)

    proveedor: Mapped[Proveedor | None] = relationship(back_populates="productos")


class Rack(Base):
    __tablename__ = "racks"
    __table_args__ = (CheckConstraint(f"clave ~ '^R-{CLAVE_01_32}$'", name="clave_formato"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(4), unique=True)

    sucursal: Mapped["Sucursal | None"] = relationship(back_populates="rack")


class Sucursal(ConFechas, Base):
    __tablename__ = "sucursales"
    __table_args__ = (
        CheckConstraint(f"clave ~ '^{CLAVE_01_32}$'", name="clave_formato"),
        en_lista("estado", Estado, "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(2), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    ciudad: Mapped[str] = mapped_column(String(80))
    # `unique`: dos sucursales no comparten rack.
    rack_id: Mapped[int] = mapped_column(ForeignKey("racks.id"), unique=True)
    estado: Mapped[str] = mapped_column(String(10), default=Estado.ACTIVO)

    rack: Mapped[Rack] = relationship(back_populates="sucursal")


class Anden(Base):
    """Andenes de recibo R1 a R4 y de embarque E1 a E3 (R-13)."""

    __tablename__ = "andenes"
    __table_args__ = (
        en_lista("tipo", TipoAnden, "tipo"),
        CheckConstraint(
            "(tipo = 'recibo' AND clave ~ '^R[1-4]$') "
            "OR (tipo = 'embarque' AND clave ~ '^E[1-3]$')",
            name="clave_de_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(2), unique=True)
    tipo: Mapped[str] = mapped_column(String(10))
