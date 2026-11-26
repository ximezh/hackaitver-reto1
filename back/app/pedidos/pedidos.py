"""Pedidos de sucursal · `/api/pedidos` (BE-20, contrato: docs/api/sprint-2.md · Pedidos).

El pedido genera una OC. Cada línea toma el proveedor principal del producto (A-16) y las líneas
de un mismo proveedor forman su parte de la OC (R-16).
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import tiempo
from app.auth.dependencias import SesionDb, requiere_rol
from app.catalogos.comun import Lista
from app.errores import NO_ENCONTRADO, error, validacion
from app.folios import folio_oc
from app.models import LineaOc, OrdenCompra, ParteOc, Producto, Usuario
from app.models.comun import Estado, EstadoProveedor, Rol
from app.models.pedidos import PASOS
from app.pedidos.esquemas import (
    M3,
    Kg,
    ProductoResumen,
    ProveedorResumen,
    SucursalResumen,
    redondear,
)
from app.pedidos.fechas import DIAS_HABILES_AL_CREAR, dias_habiles_despues
from app.tiempo import FechaHora

router = APIRouter(prefix="/pedidos", tags=["pedidos"])
Sucursal = Annotated[Usuario, Depends(requiere_rol(Rol.SUCURSAL))]

MAX_BULTOS_POR_LINEA = 999


class LineaPedido(BaseModel):
    sku: str = Field(title="SKU")
    bultos: int = Field(title="Bultos")


class PedidoNuevo(BaseModel):
    lineas: list[LineaPedido] = Field(default_factory=list, title="Productos")


class CitaResumen(BaseModel):
    anden: str
    dia: date
    inicio: str
    fin: str


class ParteSalida(BaseModel):
    proveedor: ProveedorResumen
    bultos: int
    cita: CitaResumen | None


class LineaSalida(BaseModel):
    producto: ProductoResumen
    proveedor: ProveedorResumen
    bultos: int
    piezas: int
    kg: Kg
    m3: M3


class PedidoSalida(BaseModel):
    folio: str
    creado_en: FechaHora
    sucursal: SucursalResumen
    paso: str
    paso_indice: int
    llega_estimado: date | None
    embarque: str | None
    bultos: int
    kg: Kg
    m3: M3
    lineas: list[LineaSalida]
    partes: list[ParteSalida]


def cita_de(parte: ParteOc) -> CitaResumen | None:
    """La cita de la parte, si ya tiene (BE-22)."""
    return None


def pedido_salida(oc: OrdenCompra) -> PedidoSalida:
    lineas: list[LineaSalida] = []
    partes: list[ParteSalida] = []
    for parte in oc.partes:
        proveedor = ProveedorResumen.model_validate(parte.proveedor)
        for linea in parte.lineas:
            p = linea.producto
            kg, m3 = redondear(p.kg * linea.bultos, p.m3 * linea.bultos)
            lineas.append(
                LineaSalida(
                    producto=ProductoResumen.model_validate(p),
                    proveedor=proveedor,
                    bultos=linea.bultos,
                    piezas=linea.bultos * p.piezas_por_bulto,
                    kg=kg,
                    m3=m3,
                )
            )
        partes.append(
            ParteSalida(
                proveedor=proveedor,
                bultos=sum(linea.bultos for linea in parte.lineas),
                cita=cita_de(parte),
            )
        )
    kg, m3 = redondear(
        sum((x.kg for x in lineas), Decimal(0)), sum((x.m3 for x in lineas), Decimal(0))
    )
    return PedidoSalida(
        folio=oc.folio,
        creado_en=oc.creado_en,
        sucursal=SucursalResumen.model_validate(oc.sucursal),
        paso=oc.paso,
        paso_indice=PASOS.index(oc.paso),
        llega_estimado=oc.llega_estimado,
        embarque=None,
        bultos=sum(x.bultos for x in lineas),
        kg=kg,
        m3=m3,
        lineas=lineas,
        partes=partes,
    )


def _con_detalle():
    return select(OrdenCompra).options(
        selectinload(OrdenCompra.sucursal),
        selectinload(OrdenCompra.partes).selectinload(ParteOc.proveedor),
        selectinload(OrdenCompra.partes)
        .selectinload(ParteOc.lineas)
        .selectinload(LineaOc.producto),
    )


def _productos_del_pedido(session: Session, datos: PedidoNuevo) -> dict[Producto, int]:
    """Valida las líneas y suma los bultos de cada SKU. Los errores van en `campos.lineas`."""
    if not datos.lineas:
        raise validacion({"lineas": "Agrega productos"})
    bultos: dict[str, int] = defaultdict(int)
    for linea in datos.lineas:
        if linea.bultos < 1:
            raise validacion({"lineas": "Los bultos deben ser al menos 1"})
        bultos[linea.sku.strip().upper()] += linea.bultos
    if max(bultos.values()) > MAX_BULTOS_POR_LINEA:
        raise validacion({"lineas": "Un pedido admite hasta 999 bultos por producto"})

    encontrados = {
        p.sku: p
        for p in session.scalars(
            select(Producto)
            .where(Producto.sku.in_(bultos))
            .options(selectinload(Producto.proveedor))
        )
    }
    resultado: dict[Producto, int] = {}
    for sku, n in bultos.items():
        producto = encontrados.get(sku)
        if producto is None or producto.estado != Estado.ACTIVO:
            raise validacion({"lineas": f"El producto {sku} no está disponible"})
        if producto.proveedor is None:
            raise validacion(
                {"lineas": f"El producto {sku} no tiene proveedor asignado. Comunícate con Oficina"}
            )
        if producto.proveedor.estado != EstadoProveedor.ACTIVO:
            raise validacion(
                {"lineas": f"El proveedor de {sku} está suspendido. Comunícate con Oficina"}
            )
        resultado[producto] = n
    return resultado


@router.post("", status_code=201)
def crear_pedido(datos: PedidoNuevo, usuario: Sucursal, session: SesionDb) -> PedidoSalida:
    productos = _productos_del_pedido(session, datos)
    oc = OrdenCompra(
        folio=folio_oc(session),
        sucursal_id=usuario.sucursal_id,
        llega_estimado=dias_habiles_despues(tiempo.hoy(), DIAS_HABILES_AL_CREAR),
    )
    partes: dict[int, ParteOc] = {}
    for producto, bultos in productos.items():
        parte = partes.get(producto.proveedor_id)  # type: ignore[arg-type]
        if parte is None:
            parte = partes[producto.proveedor_id] = ParteOc(proveedor=producto.proveedor)  # type: ignore[index]
            oc.partes.append(parte)
        parte.lineas.append(LineaOc(producto=producto, bultos=bultos))
    session.add(oc)
    session.commit()
    return pedido_salida(session.scalars(_con_detalle().where(OrdenCompra.id == oc.id)).one())


@router.get("")
def listar_pedidos(
    usuario: Sucursal,
    session: SesionDb,
    en_curso: Annotated[bool, Query(title="En curso")] = False,
) -> Lista[PedidoSalida]:
    consulta = _con_detalle().where(OrdenCompra.sucursal_id == usuario.sucursal_id)
    if en_curso:
        consulta = consulta.where(OrdenCompra.paso != "recibido")
    ocs = session.scalars(consulta.order_by(OrdenCompra.creado_en.desc(), OrdenCompra.id.desc()))
    items = [pedido_salida(oc) for oc in ocs]
    return Lista(items=items, total=len(items))


@router.get("/{folio}")
def ver_pedido(folio: str, usuario: Sucursal, session: SesionDb) -> PedidoSalida:
    oc = session.scalars(
        _con_detalle().where(
            OrdenCompra.folio == folio.upper(), OrdenCompra.sucursal_id == usuario.sucursal_id
        )
    ).one_or_none()
    if oc is None:
        raise error(NO_ENCONTRADO)
    return pedido_salida(oc)
