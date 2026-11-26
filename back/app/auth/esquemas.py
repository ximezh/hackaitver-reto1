"""Cuerpos y respuestas de `/api/auth` (contrato: docs/api/sprint-1.md · Autenticación)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import Usuario
from app.models.comun import Canal


class LoginEntrada(BaseModel):
    # Vacíos por omisión: la ruta responde «Revisa usuario y contraseña» para cualquier falta.
    usuario: str = Field("", title="Usuario")
    contrasena: str = Field("", title="Contraseña")
    canal: Canal | None = Field(None, title="Canal")


class SucursalDelPerfil(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    clave: str
    nombre: str


class ProveedorDelPerfil(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rfc: str
    nombre: str


class Perfil(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario: str
    nombre: str
    rol: str
    canal: str
    contrasena_temporal: bool
    sucursal: SucursalDelPerfil | None
    proveedor: ProveedorDelPerfil | None


class Sesion(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expira_en: int
    contrasena_temporal: bool
    usuario: Perfil

    @classmethod
    def de(cls, usuario: Usuario, token: str, expira_en: int) -> "Sesion":
        return cls(
            access_token=token,
            expira_en=expira_en,
            contrasena_temporal=usuario.contrasena_temporal,
            usuario=Perfil.model_validate(usuario),
        )


class CambioContrasena(BaseModel):
    actual: str = Field(title="Contraseña actual", min_length=1)
    nueva: str = Field(title="Contraseña nueva", min_length=1)
