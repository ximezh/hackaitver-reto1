"""Proveedores · `/api/proveedores` (BE-12, contrato: docs/api/sprint-1.md · Proveedores)."""

import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.auth.dependencias import SesionDb, requiere_rol
from app.catalogos.comun import (
    Lista,
    eliminar_o_desactivar,
    falla,
    listar,
    obligatorio,
    obtener,
    opcional,
)
from app.errores import ErrorApi
from app.models import Proveedor
from app.models.comun import EstadoProveedor, Rol

router = APIRouter(
    prefix="/proveedores", tags=["proveedores"], dependencies=[Depends(requiere_rol(Rol.OFICINA))]
)

# Formato del SAT: 3 letras (persona moral) o 4 (física), fecha AAMMDD y homoclave.
RFC = re.compile(r"[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}")


def revisar_que_puede_agendar(proveedor: Proveedor) -> None:
    """Un proveedor suspendido o inactivo no agenda citas (BE-12). La usa BE-22."""
    if proveedor.estado != EstadoProveedor.ACTIVO:
        raise ErrorApi(
            409,
            "proveedor_suspendido",
            "Tu cuenta de proveedor está suspendida. Comunícate con Oficina",
        )


class _Reglas(BaseModel):
    @field_validator("rfc", mode="before", check_fields=False)
    @classmethod
    def _rfc(cls, v: Any) -> str:
        rfc = obligatorio(v, "RFC").upper()
        if not RFC.fullmatch(rfc):
            raise falla("El RFC no es válido")
        return rfc

    @field_validator("nombre", mode="before", check_fields=False)
    @classmethod
    def _nombre(cls, v: Any) -> str:
        nombre = obligatorio(v, "Proveedor")
        if len(nombre) > 120:
            raise falla("Proveedor admite hasta 120 caracteres")
        return nombre

    @field_validator("contacto", mode="before", check_fields=False)
    @classmethod
    def _contacto(cls, v: Any) -> str | None:
        contacto = opcional(v)
        if contacto is not None and len(contacto) > 120:
            raise falla("Contacto admite hasta 120 caracteres")
        return contacto

    @field_validator("telefono", mode="before", check_fields=False)
    @classmethod
    def _telefono(cls, v: Any) -> str | None:
        telefono = opcional(v)
        if telefono is not None and len(telefono) > 20:
            raise falla("Teléfono admite hasta 20 caracteres")
        return telefono

    @field_validator("estado", mode="before", check_fields=False)
    @classmethod
    def _estado(cls, v: Any) -> Any:
        if v is None:
            raise falla("Completa Estado")
        if v not in {e.value for e in EstadoProveedor}:
            raise falla("El estado no es válido")
        return v


class ProveedorNuevo(_Reglas):
    rfc: str = Field(title="RFC")
    nombre: str = Field(title="Proveedor")
    contacto: str | None = Field(None, title="Contacto")
    telefono: str | None = Field(None, title="Teléfono")
    estado: EstadoProveedor = Field(EstadoProveedor.ACTIVO, title="Estado")


class ProveedorCambios(_Reglas):
    rfc: str | None = Field(None, title="RFC")
    nombre: str | None = Field(None, title="Proveedor")
    contacto: str | None = Field(None, title="Contacto")
    telefono: str | None = Field(None, title="Teléfono")
    estado: EstadoProveedor | None = Field(None, title="Estado")


class ProveedorSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rfc: str
    nombre: str
    contacto: str | None
    telefono: str | None
    estado: str


@router.get("")
def listar_proveedores(
    session: SesionDb, q: Annotated[str | None, Query(title="Búsqueda")] = None
) -> Lista[ProveedorSalida]:
    items = listar(session, Proveedor, q, Proveedor.rfc, Proveedor.nombre, Proveedor.contacto)
    return Lista(items=[ProveedorSalida.model_validate(p) for p in items], total=len(items))


@router.get("/{id_}")
def ver_proveedor(id_: int, session: SesionDb) -> ProveedorSalida:
    return ProveedorSalida.model_validate(obtener(session, Proveedor, id_))


@router.post("", status_code=201)
def crear_proveedor(datos: ProveedorNuevo, session: SesionDb) -> ProveedorSalida:
    proveedor = Proveedor(**datos.model_dump())
    session.add(proveedor)
    session.commit()
    return ProveedorSalida.model_validate(proveedor)


@router.patch("/{id_}")
def editar_proveedor(id_: int, cambios: ProveedorCambios, session: SesionDb) -> ProveedorSalida:
    proveedor = obtener(session, Proveedor, id_)
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        setattr(proveedor, campo, valor)
    session.commit()
    session.refresh(proveedor)
    return ProveedorSalida.model_validate(proveedor)


@router.delete("/{id_}")
def eliminar_proveedor(id_: int, session: SesionDb) -> dict:
    """Con productos o usuarios vinculados queda inactivo en lugar de borrarse (H-11)."""
    return eliminar_o_desactivar(session, obtener(session, Proveedor, id_), ProveedorSalida)
