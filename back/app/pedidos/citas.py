"""Citas por andén · `/api/citas` (BE-22, contrato: docs/api/sprint-2.md · Citas por andén).

- R-02: lunes a sábado, andenes de recibo R1 a R4, de 8:00 a 18:00 en bloques de 30 minutos,
  de 1, 1.5, 2 o 3 h, sin pasar de las 18:00, hasta 2 semanas adelante.
- R-03 y A-08: dos citas no se empalman en el mismo andén; lo garantiza el EXCLUDE de la base.
- R-04: el folio de factura es obligatorio y no se repite para el mismo producto.
"""

import re
from datetime import date, datetime, time, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import tiempo
from app.auth.dependencias import SesionDb, requiere_rol
from app.catalogos.comun import falla
from app.catalogos.proveedores import revisar_que_puede_agendar
from app.errores import ErrorApi, validacion
from app.models import Anden, Cita, Factura, FacturaProducto, OrdenCompra, ParteOc, Usuario
from app.models.comun import Rol, TipoAnden
from app.pedidos.esquemas import ProveedorResumen, SucursalResumen
from app.pedidos.fechas import dias_habiles_despues, es_habil
from app.pedidos.proveedor import parte_de
from app.tiempo import ZONA, FechaHora, a_local

router = APIRouter(prefix="/citas", tags=["citas"])
Proveedor = Annotated[Usuario, Depends(requiere_rol(Rol.PROVEEDOR))]

ABRE, CIERRA = time(8, 0), time(18, 0)
BLOQUE_MIN = 30
DURACIONES_MIN = (60, 90, 120, 180)
DIAS_ADELANTE = 14
FOLIO_MAXIMO = 30


# --- Reglas ----------------------------------------------------------------------------


def revisar_dia(dia: date | None) -> date:
    if dia is None:
        raise validacion({"dia": "Completa Día"})
    hoy = tiempo.hoy()
    if not es_habil(dia):
        raise validacion({"dia": "Las citas son de lunes a sábado"})
    if dia < hoy:
        raise validacion({"dia": "Ese día ya pasó"})
    if dia > hoy + timedelta(days=DIAS_ADELANTE):
        raise validacion({"dia": "Solo se agenda hasta 2 semanas adelante"})
    return dia


def normalizar_folio(folio: str | None) -> str:
    return (folio or "").strip().upper()


def problema_del_folio(folio: str) -> str | None:
    """Errores de forma del folio de factura (R-04, R-12)."""
    if not folio:
        return "El folio es obligatorio"
    if not folio.startswith("FAC-"):
        return "El folio debe empezar con FAC-"
    if len(folio) > FOLIO_MAXIMO:
        return "El folio admite hasta 30 caracteres"
    return None


def folio_registrado(session: Session, folio: str, parte: ParteOc) -> bool:
    """¿El folio ya existe para alguno de los productos de la parte, de cualquier proveedor?"""
    productos = [linea.producto_id for linea in parte.lineas]
    return (
        session.scalars(
            select(FacturaProducto.id).where(
                FacturaProducto.folio == folio, FacturaProducto.producto_id.in_(productos)
            )
        ).first()
        is not None
    )


class CitaNueva(BaseModel):
    oc: str = Field(title="Orden de compra", min_length=1)
    folio_factura: str = Field("", title="Folio de factura")
    anden: str = Field(title="Andén", min_length=1)
    dia: date = Field(title="Día")
    inicio: str = Field(title="Horario", min_length=1)
    duracion_min: int = Field(title="Tiempo estimado de descarga")

    @field_validator("inicio")
    @classmethod
    def _inicio(cls, v: Any) -> str:
        m = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", v.strip())
        if not m or int(m[2]) % BLOQUE_MIN or not (ABRE <= time(int(m[1]), int(m[2])) < CIERRA):
            raise falla("Elige un horario de 8:00 a 18:00 en bloques de 30 minutos")
        return f"{int(m[1]):02d}:{m[2]}"

    @field_validator("duracion_min")
    @classmethod
    def _duracion(cls, v: int) -> int:
        if v not in DURACIONES_MIN:
            raise falla("Elige una duración de 1, 1.5, 2 o 3 h")
        return v


class CitaSalida(BaseModel):
    id: int
    oc: str
    sucursal: SucursalResumen
    proveedor: ProveedorResumen
    folio_factura: str
    anden: str
    dia: date
    inicio: str
    fin: str
    duracion_min: int
    bultos: int
    estado: str
    creado_en: FechaHora


def horario(cita: Cita) -> tuple[date, str, str]:
    """Día, inicio y fin de la cita en la hora de la operación, como `HH:MM`."""
    inicio, fin = a_local(cita.inicio), a_local(cita.fin)
    return inicio.date(), f"{inicio:%H:%M}", f"{fin:%H:%M}"


def cita_salida(cita: Cita) -> CitaSalida:
    parte = cita.parte
    dia, inicio, fin = horario(cita)
    return CitaSalida(
        id=cita.id,
        oc=parte.oc.folio,
        sucursal=SucursalResumen.model_validate(parte.oc.sucursal),
        proveedor=ProveedorResumen.model_validate(parte.proveedor),
        folio_factura=parte.factura.folio if parte.factura else "",
        anden=cita.anden.clave,
        dia=dia,
        inicio=inicio,
        fin=fin,
        duracion_min=int((cita.fin - cita.inicio).total_seconds() // 60),
        bultos=sum(linea.bultos for linea in parte.lineas),
        estado=cita.estado,
        creado_en=cita.creado_en,
    )


def _actualizar_oc(session: Session, oc: OrdenCompra) -> None:
    """Primer cita: pasa a «Proveedor» (C2-01). Todas con cita: «Llega» al día hábil siguiente."""
    if oc.paso == "oc_emitida":
        oc.paso = "proveedor"
    citas = [p.cita for p in oc.partes]
    if all(c is not None for c in citas):
        ultima = max(a_local(c.fin).date() for c in citas if c is not None)
        oc.llega_estimado = dias_habiles_despues(ultima, 1)


# --- Rutas -----------------------------------------------------------------------------


class Ocupado(BaseModel):
    inicio: str
    fin: str
    etiqueta: str
    propia: bool


class AndenDelDia(BaseModel):
    anden: str
    ocupados: list[Ocupado]


class Disponibilidad(BaseModel):
    dia: date
    abre: str = f"{ABRE:%H:%M}"
    cierra: str = f"{CIERRA:%H:%M}"
    bloque_min: int = BLOQUE_MIN
    andenes: list[AndenDelDia]


@router.get("/disponibilidad")
def disponibilidad(
    usuario: Proveedor,
    session: SesionDb,
    dia: Annotated[date | None, Query(title="Día")] = None,
) -> Disponibilidad:
    dia = revisar_dia(dia)
    desde = datetime.combine(dia, time(0), ZONA)
    andenes = session.scalars(
        select(Anden).where(Anden.tipo == TipoAnden.RECIBO).order_by(Anden.clave)
    ).all()
    citas = session.scalars(
        select(Cita)
        .where(Cita.inicio >= desde, Cita.inicio < desde + timedelta(days=1))
        .options(
            selectinload(Cita.parte).selectinload(ParteOc.oc),
            selectinload(Cita.parte).selectinload(ParteOc.proveedor),
        )
        .order_by(Cita.inicio)
    ).all()
    por_anden: dict[int, list[Ocupado]] = {a.id: [] for a in andenes}
    for cita in citas:
        propia = cita.parte.proveedor_id == usuario.proveedor_id
        _, inicio, fin = horario(cita)
        por_anden.setdefault(cita.anden_id, []).append(
            Ocupado(
                inicio=inicio,
                fin=fin,
                # Como el prototipo: las propias con su OC y las ajenas con el proveedor (C2-03).
                etiqueta=cita.parte.oc.folio if propia else cita.parte.proveedor.nombre,
                propia=propia,
            )
        )
    return Disponibilidad(
        dia=dia,
        andenes=[AndenDelDia(anden=a.clave, ocupados=por_anden[a.id]) for a in andenes],
    )


@router.post("", status_code=201)
def crear_cita(datos: CitaNueva, usuario: Proveedor, session: SesionDb) -> CitaSalida:
    revisar_que_puede_agendar(usuario.proveedor)  # type: ignore[arg-type]
    folio = normalizar_folio(datos.folio_factura)
    if (problema := problema_del_folio(folio)) is not None:
        raise validacion({"folio_factura": problema})
    dia = revisar_dia(datos.dia)

    anden = session.scalars(
        select(Anden).filter_by(clave=datos.anden.strip().upper(), tipo=TipoAnden.RECIBO)
    ).one_or_none()
    if anden is None:
        raise validacion({"anden": "Elige un andén de recibo, de R1 a R4"})

    h, m = map(int, datos.inicio.split(":"))
    inicio = datetime.combine(dia, time(h, m), ZONA)
    fin = inicio + timedelta(minutes=datos.duracion_min)
    if fin > datetime.combine(dia, CIERRA, ZONA):
        raise validacion({"inicio": "La cita debe terminar a más tardar a las 18:00"})
    if inicio < tiempo.ahora():
        raise validacion({"inicio": "Ese horario ya pasó"})

    parte = parte_de(session, usuario.proveedor_id, datos.oc)  # type: ignore[arg-type]
    if parte.cita is not None:
        raise ErrorApi(409, "cita_existente", "Esta orden ya tiene cita")
    if folio_registrado(session, folio, parte):
        detalle = "Este folio ya está registrado"
        raise ErrorApi(409, "folio_registrado", detalle, {"folio_factura": detalle})

    # Revisión previa del empalme para responder rápido; el EXCLUDE de la base decide si dos
    # proveedores confirman al mismo tiempo (y el manejador de errores lo traduce igual).
    choca = session.scalars(
        select(Cita.id).where(Cita.anden_id == anden.id, Cita.inicio < fin, Cita.fin > inicio)
    ).first()
    if choca is not None:
        detalle = "Ese andén ya está ocupado"
        raise ErrorApi(409, "anden_ocupado", detalle, {"anden": detalle})

    factura = Factura(folio=folio, parte=parte)
    factura.productos = [
        FacturaProducto(folio=folio, producto_id=linea.producto_id) for linea in parte.lineas
    ]
    cita = Cita(parte=parte, anden=anden, inicio=inicio, fin=fin)
    session.add_all([factura, cita])
    session.flush()
    _actualizar_oc(session, parte.oc)
    session.commit()
    session.refresh(cita)
    return cita_salida(cita)
