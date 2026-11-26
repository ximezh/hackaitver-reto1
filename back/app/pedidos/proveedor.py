"""Orden de requerimiento · `/api/proveedor/ordenes` (BE-21, docs/api/sprint-2.md).

El proveedor ve solo **su parte** de cada OC: sus productos, bultos, peso y volumen (R-16).
"""

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencias import SesionDb, requiere_rol
from app.catalogos.comun import Lista
from app.errores import NO_ENCONTRADO, error
from app.models import LineaOc, OrdenCompra, ParteOc, Usuario
from app.models.comun import Rol
from app.pedidos.esquemas import M3, Kg, ProductoConMedidas, SucursalResumen, redondear
from app.tiempo import FechaHora, a_local

router = APIRouter(prefix="/proveedor", tags=["proveedor"])
Proveedor = Annotated[Usuario, Depends(requiere_rol(Rol.PROVEEDOR))]


class LineaDeLaParte(BaseModel):
    producto: ProductoConMedidas
    bultos: int
    piezas: int


class CitaDeLaParte(BaseModel):
    id: int
    anden: str
    dia: date
    inicio: str
    fin: str
    estado: str


class FacturaDeLaParte(BaseModel):
    folio: str
    bultos_capturados: int


class OrdenDelProveedor(BaseModel):
    oc: str
    creado_en: FechaHora
    sucursal: SucursalResumen
    bultos: int
    kg: Kg
    m3: M3
    lineas: list[LineaDeLaParte]
    cita: CitaDeLaParte | None
    factura: FacturaDeLaParte | None


def cita_de_la_parte(parte: ParteOc) -> CitaDeLaParte | None:
    if parte.cita is None:
        return None
    inicio, fin = a_local(parte.cita.inicio), a_local(parte.cita.fin)
    return CitaDeLaParte(
        id=parte.cita.id,
        anden=parte.cita.anden.clave,
        dia=inicio.date(),
        inicio=f"{inicio:%H:%M}",
        fin=f"{fin:%H:%M}",
        estado=parte.cita.estado,
    )


def bultos_capturados(factura: object) -> int:
    """Se completa en BE-23, cuando la factura tiene bultos."""
    return 0


def factura_de_la_parte(parte: ParteOc) -> FacturaDeLaParte | None:
    if parte.factura is None:
        return None
    return FacturaDeLaParte(
        folio=parte.factura.folio, bultos_capturados=bultos_capturados(parte.factura)
    )


def orden_del_proveedor(parte: ParteOc) -> OrdenDelProveedor:
    lineas = [
        LineaDeLaParte(
            producto=ProductoConMedidas.model_validate(linea.producto),
            bultos=linea.bultos,
            piezas=linea.bultos * linea.producto.piezas_por_bulto,
        )
        for linea in parte.lineas
    ]
    kg, m3 = redondear(
        sum((x.producto.kg * x.bultos for x in lineas), Decimal(0)),
        sum((x.producto.m3 * x.bultos for x in lineas), Decimal(0)),
    )
    return OrdenDelProveedor(
        oc=parte.oc.folio,
        creado_en=parte.oc.creado_en,
        sucursal=SucursalResumen.model_validate(parte.oc.sucursal),
        bultos=sum(x.bultos for x in lineas),
        kg=kg,
        m3=m3,
        lineas=lineas,
        cita=cita_de_la_parte(parte),
        factura=factura_de_la_parte(parte),
    )


def partes_del_proveedor(session: Session, proveedor_id: int):
    return (
        select(ParteOc)
        .join(ParteOc.oc)
        .where(ParteOc.proveedor_id == proveedor_id)
        .options(
            selectinload(ParteOc.oc).selectinload(OrdenCompra.sucursal),
            selectinload(ParteOc.lineas).selectinload(LineaOc.producto),
            selectinload(ParteOc.cita),
            selectinload(ParteOc.factura),
        )
    )


def parte_de(session: Session, proveedor_id: int, folio_oc: str) -> ParteOc:
    """La parte del proveedor en esa OC; `404` si no existe o no es suya (R-16)."""
    parte = session.scalars(
        partes_del_proveedor(session, proveedor_id).where(OrdenCompra.folio == folio_oc.upper())
    ).one_or_none()
    if parte is None:
        raise error(NO_ENCONTRADO)
    return parte


@router.get("/ordenes")
def listar_ordenes(
    usuario: Proveedor,
    session: SesionDb,
    sin_cita: Annotated[bool, Query(title="Sin cita")] = False,
) -> Lista[OrdenDelProveedor]:
    consulta = partes_del_proveedor(session, usuario.proveedor_id).order_by(  # type: ignore[arg-type]
        OrdenCompra.creado_en.desc(), OrdenCompra.id.desc()
    )
    items = [orden_del_proveedor(p) for p in session.scalars(consulta)]
    if sin_cita:
        items = [o for o in items if o.cita is None]
    return Lista(items=items, total=len(items))
