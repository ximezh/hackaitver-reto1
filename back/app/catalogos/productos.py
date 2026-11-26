"""Productos · `/api/productos` (BE-11, contrato: docs/api/sprint-1.md · Productos)."""

import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

from app.auth.dependencias import SesionDb, requiere_rol
from app.catalogos.comun import Lista, eliminar_o_desactivar, falla, listar, obligatorio, obtener
from app.errores import validacion
from app.models import Producto, Proveedor, Usuario
from app.models.catalogos import ILUSTRACIONES_DE_PRODUCTO
from app.models.comun import Estado, Rol

router = APIRouter(prefix="/productos", tags=["productos"])
# Oficina administra el catálogo; Sucursal solo lo lee para pedir (sprint 2).
SOLO_OFICINA = [Depends(requiere_rol(Rol.OFICINA))]
Lector = Annotated[Usuario, Depends(requiere_rol(Rol.OFICINA, Rol.SUCURSAL))]

# Un bulto que no cabe en una tarima nunca se podría almacenar (R-09).
KG_MAXIMO = Decimal("1000")
M3_MAXIMO = Decimal("2.576")

ComoNumero = PlainSerializer(float, return_type=float)  # el contrato los pide como números


class _Reglas(BaseModel):
    @field_validator("sku", mode="before", check_fields=False)
    @classmethod
    def _sku(cls, v: Any) -> str:
        sku = obligatorio(v, "SKU").upper()
        if not re.fullmatch(r"[A-Z0-9-]{3,20}", sku):
            raise falla("El SKU no es válido")
        return sku

    @field_validator("nombre", mode="before", check_fields=False)
    @classmethod
    def _nombre(cls, v: Any) -> str:
        nombre = obligatorio(v, "Producto")
        if len(nombre) > 120:
            raise falla("Producto admite hasta 120 caracteres")
        return nombre

    @field_validator("ilustracion", mode="before", check_fields=False)
    @classmethod
    def _ilustracion(cls, v: Any) -> str:
        if v not in ILUSTRACIONES_DE_PRODUCTO:
            raise falla("La ilustración no es válida")
        return v

    @field_validator("unidad", mode="before", check_fields=False)
    @classmethod
    def _unidad(cls, v: Any) -> str:
        unidad = obligatorio(v, "Unidad")
        if len(unidad) > 30:
            raise falla("Unidad admite hasta 30 caracteres")
        return unidad

    @field_validator("piezas_por_bulto", check_fields=False)
    @classmethod
    def _piezas(cls, v: int | None) -> int:
        if v is None:
            raise falla("Completa Piezas/bulto")
        if v <= 0:
            raise falla("Las piezas por bulto deben ser mayores a 0")
        return v

    @field_validator("kg", check_fields=False)
    @classmethod
    def _kg(cls, v: Decimal | None) -> Decimal:
        if v is None:
            raise falla("Completa Peso bulto (kg)")
        if v <= 0:
            raise falla("El peso debe ser mayor a 0")
        if v > KG_MAXIMO:
            raise falla("El peso no puede pasar de 1,000 kg, la capacidad de una tarima")
        return v.quantize(Decimal("0.1"), ROUND_HALF_UP)

    @field_validator("m3", check_fields=False)
    @classmethod
    def _m3(cls, v: Decimal | None) -> Decimal:
        if v is None:
            raise falla("Completa Volumen (m³)")
        if v <= 0:
            raise falla("El volumen debe ser mayor a 0")
        if v > M3_MAXIMO:
            raise falla("El volumen no puede pasar de 2.576 m³, la capacidad de una tarima")
        return v.quantize(Decimal("0.001"), ROUND_HALF_UP)


class ProductoNuevo(_Reglas):
    sku: str = Field(title="SKU")
    nombre: str = Field(title="Producto")
    ilustracion: str = Field("bulto", title="Ilustración")
    unidad: str = Field("piezas", title="Unidad")
    piezas_por_bulto: int = Field(title="Piezas/bulto")
    kg: Decimal = Field(title="Peso bulto (kg)")
    m3: Decimal = Field(title="Volumen (m³)")
    proveedor_id: int | None = Field(None, title="Proveedor")
    estado: Estado = Field(Estado.ACTIVO, title="Estado")


class ProductoCambios(_Reglas):
    sku: str | None = Field(None, title="SKU")
    nombre: str | None = Field(None, title="Producto")
    ilustracion: str | None = Field(None, title="Ilustración")
    unidad: str | None = Field(None, title="Unidad")
    piezas_por_bulto: int | None = Field(None, title="Piezas/bulto")
    kg: Decimal | None = Field(None, title="Peso bulto (kg)")
    m3: Decimal | None = Field(None, title="Volumen (m³)")
    proveedor_id: int | None = Field(None, title="Proveedor")
    estado: Estado | None = Field(None, title="Estado")


class ProveedorDelProducto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class ProductoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    nombre: str
    ilustracion: str
    unidad: str
    piezas_por_bulto: int
    kg: Annotated[Decimal, ComoNumero]
    m3: Annotated[Decimal, ComoNumero]
    proveedor_id: int | None
    proveedor: ProveedorDelProducto | None
    estado: str


def _revisar_proveedor(session: SesionDb, proveedor_id: int | None) -> None:
    if proveedor_id is not None and session.get(Proveedor, proveedor_id) is None:
        raise validacion({"proveedor_id": "El proveedor no existe"})


@router.get("")
def listar_productos(
    usuario: Lector, session: SesionDb, q: Annotated[str | None, Query(title="Búsqueda")] = None
) -> Lista[ProductoSalida]:
    items = listar(session, Producto, q, Producto.sku, Producto.nombre)
    if usuario.rol == Rol.SUCURSAL:
        items = [p for p in items if p.estado == Estado.ACTIVO]
    return Lista(items=[ProductoSalida.model_validate(p) for p in items], total=len(items))


@router.get("/{id_}", dependencies=SOLO_OFICINA)
def ver_producto(id_: int, session: SesionDb) -> ProductoSalida:
    return ProductoSalida.model_validate(obtener(session, Producto, id_))


@router.post("", status_code=201, dependencies=SOLO_OFICINA)
def crear_producto(datos: ProductoNuevo, session: SesionDb) -> ProductoSalida:
    _revisar_proveedor(session, datos.proveedor_id)
    producto = Producto(**datos.model_dump())
    session.add(producto)
    session.commit()
    return ProductoSalida.model_validate(producto)


@router.patch("/{id_}", dependencies=SOLO_OFICINA)
def editar_producto(id_: int, cambios: ProductoCambios, session: SesionDb) -> ProductoSalida:
    producto = obtener(session, Producto, id_)
    valores = cambios.model_dump(exclude_unset=True)
    if "proveedor_id" in valores:
        _revisar_proveedor(session, valores["proveedor_id"])
    for campo, valor in valores.items():
        setattr(producto, campo, valor)
    session.commit()
    session.refresh(producto)
    return ProductoSalida.model_validate(producto)


@router.delete("/{id_}", dependencies=SOLO_OFICINA)
def eliminar_producto(id_: int, session: SesionDb) -> dict:
    return eliminar_o_desactivar(session, obtener(session, Producto, id_), ProductoSalida)
