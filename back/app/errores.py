"""Errores uniformes de la API: `{ "detail": "...", "code": "..." }` (BE-04).

- `detail` es el texto que ve el usuario; `code` es estable y es con lo que decide el front.
- Los errores de validación agregan `campos` y usan el `title` de cada campo como etiqueta:
  un campo obligatorio vacío responde «Completa <etiqueta>», como el prototipo.
- Las violaciones de restricciones de PostgreSQL se traducen por el nombre de la restricción.

Contrato: docs/api/README.md · Errores.
"""

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger(__name__)


# Mismo nombre que en el front (front/src/api/errores.js), por eso no termina en «Error».
class ErrorApi(Exception):  # noqa: N818
    """Error que la API responde tal cual. Se lanza desde cualquier ruta o servicio."""

    def __init__(
        self, status: int, code: str, detail: str, campos: dict[str, str] | None = None
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail
        self.campos = campos

    def cuerpo(self) -> dict[str, Any]:
        cuerpo: dict[str, Any] = {"detail": self.detail, "code": self.code}
        if self.campos is not None:
            cuerpo["campos"] = self.campos
        return cuerpo


def validacion(campos: dict[str, str]) -> ErrorApi:
    """422 con los mensajes por campo; `detail` repite el del primero."""
    return ErrorApi(422, "validacion", next(iter(campos.values())), campos)


# --- Errores generales del contrato -----------------------------------------------------

NO_AUTENTICADO = (401, "no_autenticado", "Inicia sesión para continuar")
TOKEN_EXPIRADO = (401, "token_expirado", "Tu sesión terminó. Inicia sesión de nuevo")
SIN_PERMISO = (403, "sin_permiso", "No tienes acceso a esta sección")
CAMBIO_CONTRASENA = (403, "cambio_contrasena_requerido", "Cambia tu contraseña para continuar")
NO_ENCONTRADO = (404, "no_encontrado", "No encontramos el registro")
ERROR_INTERNO = (500, "error_interno", "Algo salió mal. Intenta de nuevo")


def error(general: tuple[int, str, str]) -> ErrorApi:
    return ErrorApi(*general)


_POR_ESTADO: dict[int, tuple[int, str, str]] = {
    401: NO_AUTENTICADO,
    403: SIN_PERMISO,
    404: NO_ENCONTRADO,
    405: (405, "metodo_no_permitido", "Esta acción no está disponible"),
}

# --- Restricciones de PostgreSQL --------------------------------------------------------


@dataclass(frozen=True)
class Restriccion:
    status: int
    code: str
    detail: str
    campo: str | None = None


def _unico(code: str, detail: str, campo: str) -> Restriccion:
    return Restriccion(409, code, detail, campo)


def _formato(detail: str, campo: str) -> Restriccion:
    return Restriccion(422, "validacion", detail, campo)


# Nombre de la restricción (ver `NAMING_CONVENTION` en app/db.py) → error del contrato.
# Es una red de seguridad: los esquemas y servicios validan antes de llegar a la base.
RESTRICCIONES: dict[str, Restriccion] = {
    "uq_productos_sku": _unico("sku_duplicado", "Este SKU ya está registrado", "sku"),
    "uq_proveedores_rfc": _unico("rfc_duplicado", "Este RFC ya está registrado", "rfc"),
    "uq_sucursales_clave": _unico("clave_duplicada", "Esta clave ya está registrada", "clave"),
    "uq_sucursales_rack_id": _unico("rack_ocupado", "Ese rack ya está asignado", "clave"),
    "uq_usuarios_usuario": _unico(
        "usuario_duplicado", "Este usuario ya está registrado", "usuario"
    ),
    "ck_productos_sku_formato": _formato("El SKU no es válido", "sku"),
    "ck_productos_piezas_positivas": _formato(
        "Las piezas por bulto deben ser mayores a 0", "piezas_por_bulto"
    ),
    "ck_productos_kg_positivo": _formato("El peso debe ser mayor a 0", "kg"),
    "ck_productos_m3_positivo": _formato("El volumen debe ser mayor a 0", "m3"),
    "ck_proveedores_rfc_formato": _formato("El RFC no es válido", "rfc"),
    "ck_sucursales_clave_formato": _formato("La clave debe ser de 01 a 32", "clave"),
    "ck_usuarios_rol": _formato("El rol no es válido", "rol"),
    "ck_usuarios_prefijo_de_rol": _formato(
        "El prefijo del usuario no corresponde a su rol", "usuario"
    ),
}

CONFLICTO = (409, "conflicto", "No se pudo guardar porque choca con otro registro")


def desde_integridad(exc: IntegrityError) -> ErrorApi:
    nombre = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
    r = RESTRICCIONES.get(nombre or "")
    if r is None:
        log.warning("Restricción sin traducción: %s", nombre or exc.orig)
        return error(CONFLICTO)
    return ErrorApi(r.status, r.code, r.detail, {r.campo: r.detail} if r.campo else None)


# --- Validación de FastAPI y Pydantic ---------------------------------------------------


def _titulos(request: Request) -> dict[tuple[str, str], str]:
    """`(ubicación, campo) → title` de los parámetros y del cuerpo de la ruta."""
    route = request.scope.get("route")
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        return {}
    titulos: dict[tuple[str, str], str] = {}
    for ubicacion, params in (
        ("query", dependant.query_params),
        ("path", dependant.path_params),
        ("header", dependant.header_params),
    ):
        for p in params:
            if p.field_info.title:
                titulos[(ubicacion, p.alias)] = p.field_info.title
    for p in dependant.body_params:
        modelo = p.field_info.annotation
        if isinstance(modelo, type) and issubclass(modelo, BaseModel):
            for nombre, campo in modelo.model_fields.items():
                titulos[("body", campo.alias or nombre)] = campo.title or nombre
    return titulos


def _mensaje(err: dict[str, Any], etiqueta: str) -> str:
    tipo, ctx = err["type"], err.get("ctx") or {}
    if tipo == "missing" or (tipo == "string_too_short" and ctx.get("min_length") == 1):
        return f"Completa {etiqueta}"
    if tipo == "validacion":
        # Mensaje propio de un validador: `PydanticCustomError("validacion", "…")`.
        return err["msg"]
    mensajes = {
        "greater_than": f"{etiqueta} debe ser mayor a {ctx.get('gt')}",
        "greater_than_equal": f"{etiqueta} debe ser mayor o igual a {ctx.get('ge')}",
        "less_than_equal": f"{etiqueta} debe ser menor o igual a {ctx.get('le')}",
        "string_too_long": f"{etiqueta} admite hasta {ctx.get('max_length')} caracteres",
        "string_too_short": f"{etiqueta} necesita al menos {ctx.get('min_length')} caracteres",
        "string_pattern_mismatch": f"{etiqueta} no es válido",
        "enum": f"{etiqueta} no es válido",
        "literal_error": f"{etiqueta} no es válido",
        "int_parsing": f"{etiqueta} debe ser un número entero",
        "int_from_float": f"{etiqueta} debe ser un número entero",
        "float_parsing": f"{etiqueta} debe ser un número",
        "decimal_parsing": f"{etiqueta} debe ser un número",
        "bool_parsing": f"{etiqueta} debe ser sí o no",
        "string_type": f"{etiqueta} debe ser texto",
        "json_invalid": "El cuerpo de la petición no es JSON válido",
        "model_attributes_type": "El cuerpo de la petición no es válido",
        "dict_type": "El cuerpo de la petición no es válido",
        "extra_forbidden": f"{etiqueta} no se puede enviar",
    }
    return mensajes.get(tipo, f"Revisa {etiqueta}")


def _campo(loc: Sequence[Any]) -> tuple[str, str]:
    """`('body', 'sku')` → `('body', 'sku')`; `('body',)` → `('body', 'general')`."""
    ubicacion = str(loc[0]) if loc else "general"
    nombres = [str(x) for x in loc[1:] if not isinstance(x, int)]
    return ubicacion, nombres[-1] if nombres else "general"


def desde_validacion(errores: Iterable[dict[str, Any]], request: Request) -> ErrorApi:
    titulos = _titulos(request)
    campos: dict[str, str] = {}
    for err in errores:
        ubicacion, nombre = _campo(err.get("loc", ()))
        if nombre not in campos:  # el primer error de cada campo es el que se muestra
            campos[nombre] = _mensaje(err, titulos.get((ubicacion, nombre), nombre))
    return validacion(campos or {"general": "Revisa los datos"})


# --- Registro en la app -----------------------------------------------------------------


def _respuesta(err: ErrorApi, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(err.cuerpo(), status_code=err.status, headers=headers)


async def _error_api(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ErrorApi)
    return _respuesta(exc)


async def _http(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    general = _POR_ESTADO.get(exc.status_code)
    if general is None:
        # Otros estados de Starlette o FastAPI (413, 415…): se conserva el estado.
        general = (exc.status_code, f"http_{exc.status_code}", "No se pudo completar la acción")
    return _respuesta(error(general), getattr(exc, "headers", None))


async def _validacion(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return _respuesta(desde_validacion(exc.errors(), request))


async def _integridad(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, IntegrityError)
    return _respuesta(desde_integridad(exc))


async def _interno(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Error no previsto en %s %s", request.method, request.url.path, exc_info=exc)
    return _respuesta(error(ERROR_INTERNO))


def registrar(app: FastAPI) -> None:
    app.add_exception_handler(ErrorApi, _error_api)
    app.add_exception_handler(StarletteHTTPException, _http)
    app.add_exception_handler(RequestValidationError, _validacion)
    app.add_exception_handler(IntegrityError, _integridad)
    app.add_exception_handler(Exception, _interno)
