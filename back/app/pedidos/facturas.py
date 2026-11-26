"""Facturas y bultos · `/api/facturas`, `/api/bultos` (BE-22, BE-23; docs/api/sprint-2.md).

- BE-22: verificación del folio antes de confirmar la cita (R-04).
- BE-23: factura desglosada por bulto. Cada bulto lleva un solo producto (R-05) y su folio `B-`.
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencias import SesionDb, requiere_rol
from app.catalogos.comun import Lista, falla
from app.catalogos.productos import KG_MAXIMO, M3_MAXIMO
from app.errores import NO_ENCONTRADO, error, validacion
from app.folios import folio_bulto
from app.models import Bulto, Factura, LineaOc, OrdenCompra, ParteOc, Usuario
from app.models.comun import Rol
from app.pedidos.citas import folio_registrado, normalizar_folio, problema_del_folio
from app.pedidos.esquemas import M3, Kg, ProveedorResumen, SucursalResumen, redondear
from app.pedidos.proveedor import parte_de

router = APIRouter(prefix="/facturas", tags=["facturas"])
bultos_router = APIRouter(prefix="/bultos", tags=["bultos"])
Proveedor = Annotated[Usuario, Depends(requiere_rol(Rol.PROVEEDOR))]
ProveedorUOficina = Annotated[Usuario, Depends(requiere_rol(Rol.PROVEEDOR, Rol.OFICINA))]
CANTIDAD_MAXIMA = 100


# --- BE-22 · Verificación del folio ----------------------------------------------------


class Verificacion(BaseModel):
    folio: str
    disponible: bool
    detail: str | None


@router.get("/verificar")
def verificar_folio(
    usuario: Proveedor,
    session: SesionDb,
    folio: Annotated[str, Query(title="Folio de factura")] = "",
    oc: Annotated[str, Query(title="Orden de compra")] = "",
) -> Verificacion:
    """Revisa el folio antes de confirmar la cita, para marcarlo en rojo (R-04)."""
    folio = normalizar_folio(folio)
    if (problema := problema_del_folio(folio)) is not None:
        return Verificacion(folio=folio, disponible=False, detail=problema)
    if not oc.strip():
        raise validacion({"oc": "Completa Orden de compra"})
    parte = parte_de(session, usuario.proveedor_id, oc)  # type: ignore[arg-type]
    if folio_registrado(session, folio, parte):
        return Verificacion(folio=folio, disponible=False, detail="Este folio ya está registrado")
    return Verificacion(folio=folio, disponible=True, detail=None)


# --- BE-23 · Factura desglosada por bulto ----------------------------------------------


def caja(kg: Decimal) -> str:
    """Caja de tarima por peso del bulto (R-08): ≥ 15 kg roja, ≥ 7 kg naranja, < 7 kg verde."""
    return "roja" if kg >= 15 else "naranja" if kg >= 7 else "verde"


def qr_texto(bulto: Bulto) -> str:
    """Texto del QR de la etiqueta (R-06): bulto, OC, sucursal destino, SKU y piezas."""
    oc = bulto.factura.parte.oc
    return (
        f"CEDIS1;B={bulto.folio};OC={oc.folio};SUC={oc.sucursal.clave};"
        f"SKU={bulto.producto.sku};PZ={bulto.piezas}"
    )


class ProductoDelBulto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    nombre: str
    ilustracion: str
    unidad: str


class BultoSalida(BaseModel):
    folio: str
    producto: ProductoDelBulto
    piezas: int
    kg: Kg
    m3: M3
    caja: str
    qr: str


class Totales(BaseModel):
    bultos: int
    kg: Kg
    m3: M3


class Diferencia(BaseModel):
    sku: str
    esperados: int
    capturados: int


class FacturaResumen(BaseModel):
    folio: str
    oc: str
    sucursal: SucursalResumen
    proveedor: ProveedorResumen
    bultos_esperados: int
    totales: Totales
    cuadra: bool
    diferencias: list[Diferencia]


class FacturaDetalle(FacturaResumen):
    bultos: list[BultoSalida]


class BultosCreados(BaseModel):
    bultos: list[BultoSalida]
    factura: FacturaResumen


class BultoNuevo(BaseModel):
    sku: str = Field(title="SKU", min_length=1)
    piezas: int = Field(title="Piezas")
    kg: Decimal = Field(title="Peso")
    m3: Decimal = Field(title="Volumen")
    cantidad: int = Field(1, title="Cantidad")

    @field_validator("piezas")
    @classmethod
    def _piezas(cls, v: int) -> int:
        if v < 1:
            raise falla("Las piezas deben ser al menos 1")
        return v

    @field_validator("kg")
    @classmethod
    def _kg(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise falla("El peso debe ser mayor a 0")
        if v > KG_MAXIMO:
            raise falla("El peso no puede pasar de 1,000 kg, la capacidad de una tarima")
        return v.quantize(Decimal("0.1"))

    @field_validator("m3")
    @classmethod
    def _m3(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise falla("El volumen debe ser mayor a 0")
        if v > M3_MAXIMO:
            raise falla("El volumen no puede pasar de 2.576 m³, la capacidad de una tarima")
        return v.quantize(Decimal("0.001"))

    @field_validator("cantidad")
    @classmethod
    def _cantidad(cls, v: int) -> int:
        if not 1 <= v <= CANTIDAD_MAXIMA:
            raise falla("La cantidad debe ser de 1 a 100 bultos")
        return v


def bulto_salida(bulto: Bulto) -> BultoSalida:
    return BultoSalida(
        folio=bulto.folio,
        producto=ProductoDelBulto.model_validate(bulto.producto),
        piezas=bulto.piezas,
        kg=bulto.kg,
        m3=bulto.m3,
        caja=caja(bulto.kg),
        qr=qr_texto(bulto),
    )


def factura_resumen(factura: Factura) -> FacturaResumen:
    parte = factura.parte
    esperados = {linea.producto.sku: linea.bultos for linea in parte.lineas}
    capturados: dict[str, int] = {}
    for b in factura.bultos:
        capturados[b.producto.sku] = capturados.get(b.producto.sku, 0) + 1
    skus = [*esperados, *(s for s in capturados if s not in esperados)]
    diferencias = [
        Diferencia(sku=s, esperados=esperados.get(s, 0), capturados=capturados.get(s, 0))
        for s in skus
        if esperados.get(s, 0) != capturados.get(s, 0)
    ]
    kg, m3 = redondear(
        sum((b.kg for b in factura.bultos), Decimal(0)),
        sum((b.m3 for b in factura.bultos), Decimal(0)),
    )
    return FacturaResumen(
        folio=factura.folio,
        oc=parte.oc.folio,
        sucursal=SucursalResumen.model_validate(parte.oc.sucursal),
        proveedor=ProveedorResumen.model_validate(parte.proveedor),
        bultos_esperados=sum(esperados.values()),
        totales=Totales(bultos=len(factura.bultos), kg=kg, m3=m3),
        cuadra=not diferencias,
        diferencias=diferencias,
    )


def _facturas() -> Select:
    return (
        select(Factura)
        .join(Factura.parte)
        .options(
            selectinload(Factura.parte).selectinload(ParteOc.oc).selectinload(OrdenCompra.sucursal),
            selectinload(Factura.parte).selectinload(ParteOc.proveedor),
            selectinload(Factura.parte).selectinload(ParteOc.lineas).selectinload(LineaOc.producto),
            selectinload(Factura.bultos).selectinload(Bulto.producto),
        )
    )


def factura_de(session: Session, usuario: Usuario, folio: str) -> Factura:
    """La factura con ese folio: del proveedor de la sesión, o cualquiera para Oficina.

    Si no existe o es de otro proveedor responde `404`, igual que si no existiera (R-16).
    """
    consulta = _facturas().where(Factura.folio == normalizar_folio(folio))
    if usuario.rol == Rol.PROVEEDOR:
        consulta = consulta.where(ParteOc.proveedor_id == usuario.proveedor_id)
    factura = session.scalars(consulta.order_by(Factura.id.desc())).first()
    if factura is None:
        raise error(NO_ENCONTRADO)
    return factura


@router.get("")
def listar_facturas(usuario: Proveedor, session: SesionDb) -> Lista[FacturaResumen]:
    consulta = _facturas().where(ParteOc.proveedor_id == usuario.proveedor_id)
    items = [factura_resumen(f) for f in session.scalars(consulta.order_by(Factura.id.desc()))]
    return Lista(items=items, total=len(items))


@router.get("/{folio}")
def ver_factura(folio: str, usuario: Proveedor, session: SesionDb) -> FacturaDetalle:
    factura = factura_de(session, usuario, folio)
    return FacturaDetalle(
        **factura_resumen(factura).model_dump(), bultos=[bulto_salida(b) for b in factura.bultos]
    )


@router.post("/{folio}/bultos", status_code=201)
def agregar_bultos(
    folio: str, datos: BultoNuevo, usuario: Proveedor, session: SesionDb
) -> BultosCreados:
    """El formulario «+ Bulto» (P-03). `cantidad` crea varios bultos iguales."""
    factura = factura_de(session, usuario, folio)
    sku = datos.sku.strip().upper()
    producto = next((x.producto for x in factura.parte.lineas if x.producto.sku == sku), None)
    if producto is None:
        raise validacion({"sku": "Ese producto no está en la orden"})
    folios = [folio_bulto(session) for _ in range(datos.cantidad)]
    nuevos = [
        Bulto(
            folio=folio,
            factura=factura,
            producto=producto,
            piezas=datos.piezas,
            kg=datos.kg,
            m3=datos.m3,
        )
        for folio in folios
    ]
    session.add_all(nuevos)
    session.commit()
    return BultosCreados(bultos=[bulto_salida(b) for b in nuevos], factura=factura_resumen(factura))


def bulto_de(session: Session, usuario: Usuario, folio: str) -> Bulto:
    """El bulto de una factura del proveedor de la sesión (u Oficina); `404` si es ajeno."""
    bulto = session.scalars(
        select(Bulto)
        .where(Bulto.folio == folio.strip().upper())
        .options(
            selectinload(Bulto.producto),
            selectinload(Bulto.factura)
            .selectinload(Factura.parte)
            .selectinload(ParteOc.oc)
            .selectinload(OrdenCompra.sucursal),
        )
    ).one_or_none()
    if bulto is None or (
        usuario.rol == Rol.PROVEEDOR and bulto.factura.parte.proveedor_id != usuario.proveedor_id
    ):
        raise error(NO_ENCONTRADO)
    return bulto


@bultos_router.delete("/{folio}")
def quitar_bulto(folio: str, usuario: Proveedor, session: SesionDb) -> dict:
    """Quita un bulto capturado por error. Desde el sprint 3, no si ya se recibió."""
    session.delete(bulto_de(session, usuario, folio))
    session.commit()
    return {"resultado": "eliminado"}
