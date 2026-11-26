"""Facturas · `/api/facturas` (BE-22: verificación del folio; contrato docs/api/sprint-2.md)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth.dependencias import SesionDb, requiere_rol
from app.errores import validacion
from app.models import Usuario
from app.models.comun import Rol
from app.pedidos.citas import folio_registrado, normalizar_folio, problema_del_folio
from app.pedidos.proveedor import parte_de

router = APIRouter(prefix="/facturas", tags=["facturas"])
Proveedor = Annotated[Usuario, Depends(requiere_rol(Rol.PROVEEDOR))]


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
