"""Piezas de respuesta que comparten pedidos, órdenes, citas y facturas (docs/api/sprint-2.md)."""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer

ComoNumero = PlainSerializer(float, return_type=float)
Kg = Annotated[Decimal, ComoNumero]
M3 = Annotated[Decimal, ComoNumero]


class _DeOrm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SucursalResumen(_DeOrm):
    id: int
    clave: str
    nombre: str


class ProveedorResumen(_DeOrm):
    id: int
    nombre: str


class ProductoResumen(_DeOrm):
    id: int
    sku: str
    nombre: str
    ilustracion: str
    unidad: str
    piezas_por_bulto: int


class ProductoConMedidas(ProductoResumen):
    kg: Kg
    m3: M3


def redondear(kg: Decimal, m3: Decimal) -> tuple[Decimal, Decimal]:
    return kg.quantize(Decimal("0.1")), m3.quantize(Decimal("0.001"))
