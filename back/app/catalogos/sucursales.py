"""Sucursales · `/api/sucursales` (BE-13, contrato: docs/api/sprint-1.md · Sucursales).

Cada sucursal ocupa el rack de su clave (`R-<clave>`), que se asigna al crearla (R-15). Por eso
la clave va de 01 a 32 —el CEDIS tiene 32 racks— y no se cambia después.
"""

import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select

from app.auth.dependencias import SesionDb, requiere_rol
from app.catalogos.comun import Lista, eliminar_o_desactivar, falla, listar, obligatorio, obtener
from app.errores import ErrorApi
from app.models import Rack, Sucursal
from app.models.comun import Estado, Rol

router = APIRouter(
    prefix="/sucursales", tags=["sucursales"], dependencies=[Depends(requiere_rol(Rol.OFICINA))]
)

NO_SE_CAMBIA = "La clave no se puede cambiar"


class _Reglas(BaseModel):
    @field_validator("nombre", mode="before", check_fields=False)
    @classmethod
    def _nombre(cls, v: Any) -> str:
        nombre = obligatorio(v, "Sucursal")
        if len(nombre) > 120:
            raise falla("Sucursal admite hasta 120 caracteres")
        return nombre

    @field_validator("ciudad", mode="before", check_fields=False)
    @classmethod
    def _ciudad(cls, v: Any) -> str:
        ciudad = obligatorio(v, "Ciudad")
        if len(ciudad) > 80:
            raise falla("Ciudad admite hasta 80 caracteres")
        return ciudad

    @field_validator("estado", mode="before", check_fields=False)
    @classmethod
    def _estado(cls, v: Any) -> Any:
        if v not in {e.value for e in Estado}:
            raise falla("El estado no es válido")
        return v


class SucursalNueva(_Reglas):
    clave: str = Field(title="Clave")
    nombre: str = Field(title="Sucursal")
    ciudad: str = Field(title="Ciudad")
    estado: Estado = Field(Estado.ACTIVO, title="Estado")

    @field_validator("clave", mode="before")
    @classmethod
    def _clave(cls, v: Any) -> str:
        clave = obligatorio(v, "Clave")
        if not re.fullmatch(r"0[1-9]|[12][0-9]|3[0-2]", clave):
            raise falla("La clave debe ser de 01 a 32")
        return clave


class SucursalCambios(_Reglas):
    nombre: str | None = Field(None, title="Sucursal")
    ciudad: str | None = Field(None, title="Ciudad")
    estado: Estado | None = Field(None, title="Estado")
    # Se declaran solo para rechazarlas con un mensaje claro.
    clave: Any = Field(None, title="Clave")
    rack: Any = Field(None, title="Rack")

    @field_validator("clave", "rack", mode="before")
    @classmethod
    def _no_se_cambian(cls, _: Any) -> None:
        raise falla(NO_SE_CAMBIA)


class SucursalSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    clave: str
    nombre: str
    ciudad: str
    rack: str
    estado: str

    @field_validator("rack", mode="before")
    @classmethod
    def _rack(cls, rack: Any) -> Any:
        return rack.clave if isinstance(rack, Rack) else rack


def _rack_libre(session: SesionDb, clave: str) -> Rack:
    """El rack `R-<clave>`; se crea si las semillas aún no cargaron los 32."""
    rack = session.scalars(select(Rack).filter_by(clave=f"R-{clave}")).one_or_none()
    if rack is None:
        rack = Rack(clave=f"R-{clave}")
        session.add(rack)
        session.flush()
    elif rack.sucursal is not None:
        detalle = "Ese rack ya está asignado"
        raise ErrorApi(409, "rack_ocupado", detalle, {"clave": detalle})
    return rack


@router.get("")
def listar_sucursales(
    session: SesionDb, q: Annotated[str | None, Query(title="Búsqueda")] = None
) -> Lista[SucursalSalida]:
    items = listar(session, Sucursal, q, Sucursal.clave, Sucursal.nombre, Sucursal.ciudad)
    return Lista(items=[SucursalSalida.model_validate(s) for s in items], total=len(items))


@router.get("/{id_}")
def ver_sucursal(id_: int, session: SesionDb) -> SucursalSalida:
    return SucursalSalida.model_validate(obtener(session, Sucursal, id_))


@router.post("", status_code=201)
def crear_sucursal(datos: SucursalNueva, session: SesionDb) -> SucursalSalida:
    if session.scalars(select(Sucursal.id).filter_by(clave=datos.clave)).first() is not None:
        detalle = "Esta clave ya está registrada"
        raise ErrorApi(409, "clave_duplicada", detalle, {"clave": detalle})
    sucursal = Sucursal(**datos.model_dump(), rack=_rack_libre(session, datos.clave))
    session.add(sucursal)
    session.commit()
    return SucursalSalida.model_validate(sucursal)


@router.patch("/{id_}")
def editar_sucursal(id_: int, cambios: SucursalCambios, session: SesionDb) -> SucursalSalida:
    sucursal = obtener(session, Sucursal, id_)
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        setattr(sucursal, campo, valor)
    session.commit()
    session.refresh(sucursal)
    return SucursalSalida.model_validate(sucursal)


@router.delete("/{id_}")
def eliminar_sucursal(id_: int, session: SesionDb) -> dict:
    """Con usuarios vinculados queda inactiva y conserva su rack (H-11). Si se borra, lo libera."""
    return eliminar_o_desactivar(session, obtener(session, Sucursal, id_), SucursalSalida)
