"""Modelos de SQLAlchemy. Cada modelo nuevo se importa aquí para que Alembic lo detecte."""

from app.models.catalogos import Anden, Producto, Proveedor, Rack, Sucursal
from app.models.pedidos import Bulto, Cita, Factura, FacturaProducto, LineaOc, OrdenCompra, ParteOc
from app.models.usuarios import Usuario

__all__ = [
    "Anden",
    "Bulto",
    "Cita",
    "Factura",
    "FacturaProducto",
    "LineaOc",
    "OrdenCompra",
    "ParteOc",
    "Producto",
    "Proveedor",
    "Rack",
    "Sucursal",
    "Usuario",
]
