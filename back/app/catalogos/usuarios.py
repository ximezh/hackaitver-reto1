"""Usuarios · `/api/usuarios` (BE-14, contrato: docs/api/sprint-1.md · Usuarios).

- El rol sale de una lista fija y define el canal (R-01). Los roles de Android exigen su prefijo.
- Sucursal y proveedor se vinculan a su registro; los demás roles no llevan vínculo.
- Oficina no captura contraseñas: al crear o restablecer, el back genera una temporal que se
  devuelve una sola vez en `contrasena_generada` (R-17).
"""

import re
import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.auth.dependencias import Oficina, SesionDb
from app.catalogos.comun import Lista, eliminar_o_desactivar, falla, listar, obligatorio, obtener
from app.contrasenas import hashear
from app.errores import ErrorApi, validacion
from app.models import Proveedor, Sucursal, Usuario
from app.models.comun import CANAL_DE_ROL, PREFIJO_DE_ROL, Estado, Rol

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

ETIQUETA_DE_ROL = {
    Rol.CASETA: "Caseta",
    Rol.DESEMBARQUE: "Sup. desembarque",
    Rol.EMBARQUE: "Sup. embarque",
    Rol.SUCURSAL: "Sucursal",
    Rol.PROVEEDOR: "Proveedor",
    Rol.OFICINA: "Oficina",
}
# Sin 0/O, 1/l/I: la contraseña temporal se dicta o se copia a mano.
_ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"


def contrasena_temporal() -> str:
    """`Tmp-7Kq2-xW9p`: 8 caracteres aleatorios, unos 46 bits."""
    bloque = lambda: "".join(secrets.choice(_ALFABETO) for _ in range(4))  # noqa: E731
    return f"Tmp-{bloque()}-{bloque()}"


class _Reglas(BaseModel):
    @field_validator("usuario", mode="before", check_fields=False)
    @classmethod
    def _usuario(cls, v: Any) -> str:
        usuario = obligatorio(v, "Usuario").lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,39}", usuario):
            raise falla("El usuario admite de 3 a 40 letras, números, punto, guion o guion bajo")
        return usuario

    @field_validator("nombre", mode="before", check_fields=False)
    @classmethod
    def _nombre(cls, v: Any) -> str:
        nombre = obligatorio(v, "Nombre")
        if len(nombre) > 120:
            raise falla("Nombre admite hasta 120 caracteres")
        return nombre

    @field_validator("rol", mode="before", check_fields=False)
    @classmethod
    def _rol(cls, v: Any) -> Any:
        if v is None or v == "":
            raise falla("Completa Rol")
        if v not in {r.value for r in Rol}:
            raise falla("El rol no es válido")
        return v

    @field_validator("estado", mode="before", check_fields=False)
    @classmethod
    def _estado(cls, v: Any) -> Any:
        if v not in {e.value for e in Estado}:
            raise falla("El estado no es válido")
        return v


class UsuarioNuevo(_Reglas):
    usuario: str = Field(title="Usuario")
    nombre: str = Field(title="Nombre")
    rol: Rol = Field(title="Rol")
    sucursal_id: int | None = Field(None, title="Sucursal")
    proveedor_id: int | None = Field(None, title="Proveedor")
    estado: Estado = Field(Estado.ACTIVO, title="Estado")


class UsuarioCambios(_Reglas):
    usuario: str | None = Field(None, title="Usuario")
    nombre: str | None = Field(None, title="Nombre")
    rol: Rol | None = Field(None, title="Rol")
    sucursal_id: int | None = Field(None, title="Sucursal")
    proveedor_id: int | None = Field(None, title="Proveedor")
    estado: Estado | None = Field(None, title="Estado")


class Vinculo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario: str
    nombre: str
    rol: str
    canal: str
    sucursal_id: int | None
    sucursal: Vinculo | None
    proveedor_id: int | None
    proveedor: Vinculo | None
    contrasena_temporal: bool
    estado: str


class UsuarioConContrasena(UsuarioSalida):
    contrasena_generada: str


def _aplicar_rol(session: Session, usuario: Usuario) -> None:
    """Revisa prefijo y vínculo del rol sobre el estado combinado y fija el canal."""
    rol = Rol(usuario.rol)
    errores: dict[str, str] = {}

    prefijo = PREFIJO_DE_ROL.get(rol)
    if prefijo and not usuario.usuario.startswith(prefijo):
        errores["usuario"] = f"El usuario de {ETIQUETA_DE_ROL[rol]} debe empezar con {prefijo}"
    elif not prefijo and usuario.usuario.startswith(tuple(PREFIJO_DE_ROL.values())):
        errores["usuario"] = "Ese prefijo es solo para usuarios de Android"

    if rol == Rol.SUCURSAL:
        if usuario.sucursal_id is None or session.get(Sucursal, usuario.sucursal_id) is None:
            errores["sucursal_id"] = "Elige la sucursal"
    else:
        usuario.sucursal_id = None
    if rol == Rol.PROVEEDOR:
        if usuario.proveedor_id is None or session.get(Proveedor, usuario.proveedor_id) is None:
            errores["proveedor_id"] = "Elige el proveedor"
    else:
        usuario.proveedor_id = None

    if errores:
        raise validacion(errores)
    usuario.canal = CANAL_DE_ROL[rol]


def _con_contrasena(usuario: Usuario, contrasena: str) -> UsuarioConContrasena:
    return UsuarioConContrasena(
        **UsuarioSalida.model_validate(usuario).model_dump(), contrasena_generada=contrasena
    )


def _no_a_si_mismo(usuario: Usuario, oficina: Usuario, mensaje: str, code: str) -> None:
    if usuario.id == oficina.id:
        raise ErrorApi(409, code, mensaje)


@router.get("")
def listar_usuarios(
    _: Oficina, session: SesionDb, q: Annotated[str | None, Query(title="Búsqueda")] = None
) -> Lista[UsuarioSalida]:
    items = listar(session, Usuario, q, Usuario.usuario, Usuario.nombre)
    return Lista(items=[UsuarioSalida.model_validate(u) for u in items], total=len(items))


@router.get("/{id_}")
def ver_usuario(id_: int, _: Oficina, session: SesionDb) -> UsuarioSalida:
    return UsuarioSalida.model_validate(obtener(session, Usuario, id_))


@router.post("", status_code=201)
def crear_usuario(datos: UsuarioNuevo, _: Oficina, session: SesionDb) -> UsuarioConContrasena:
    contrasena = contrasena_temporal()
    usuario = Usuario(
        **datos.model_dump(), contrasena_hash=hashear(contrasena), contrasena_temporal=True
    )
    _aplicar_rol(session, usuario)
    session.add(usuario)
    session.commit()
    return _con_contrasena(usuario, contrasena)


@router.patch("/{id_}")
def editar_usuario(
    id_: int, cambios: UsuarioCambios, oficina: Oficina, session: SesionDb
) -> UsuarioSalida:
    usuario = obtener(session, Usuario, id_)
    valores = cambios.model_dump(exclude_unset=True)
    if valores.get("estado") == Estado.INACTIVO:
        _no_a_si_mismo(
            usuario, oficina, "No puedes eliminar tu propio usuario", "no_puedes_eliminarte"
        )
    if "rol" in valores and valores["rol"] != usuario.rol:
        _no_a_si_mismo(
            usuario, oficina, "No puedes cambiar tu propio rol", "no_puedes_cambiar_tu_rol"
        )
    with session.no_autoflush:
        for campo, valor in valores.items():
            setattr(usuario, campo, valor)
        _aplicar_rol(session, usuario)
    session.commit()
    session.refresh(usuario)
    return UsuarioSalida.model_validate(usuario)


@router.post("/{id_}/restablecer")
def restablecer_contrasena(id_: int, _: Oficina, session: SesionDb) -> UsuarioConContrasena:
    """Contraseña temporal nueva; la anterior deja de servir y debe cambiarla al entrar."""
    usuario = obtener(session, Usuario, id_)
    contrasena = contrasena_temporal()
    usuario.contrasena_hash = hashear(contrasena)
    usuario.contrasena_temporal = True
    session.commit()
    return _con_contrasena(usuario, contrasena)


@router.delete("/{id_}")
def eliminar_usuario(id_: int, oficina: Oficina, session: SesionDb) -> dict:
    usuario = obtener(session, Usuario, id_)
    _no_a_si_mismo(usuario, oficina, "No puedes eliminar tu propio usuario", "no_puedes_eliminarte")
    return eliminar_o_desactivar(session, usuario, UsuarioSalida)
