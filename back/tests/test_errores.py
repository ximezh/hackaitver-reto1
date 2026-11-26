"""BE-04: todos los errores responden `{ detail, code }` con los textos del contrato."""

from collections.abc import Iterator
from decimal import Decimal
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError
from sqlalchemy.orm import Session

from app.db import get_session
from app.errores import NO_ENCONTRADO, ErrorApi, error
from app.main import create_app
from app.models import Producto


class ProductoNuevo(BaseModel):
    sku: str = Field(title="SKU", min_length=1, max_length=20)
    nombre: str = Field(title="Producto", min_length=1)
    piezas_por_bulto: int = Field(title="Piezas/bulto", gt=0)
    kg: Decimal = Field(title="Peso bulto (kg)")

    @field_validator("kg")
    @classmethod
    def kg_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise PydanticCustomError("validacion", "El peso debe ser mayor a 0")
        return v


def app_de_prueba(db: Session | None = None) -> FastAPI:
    app = create_app()

    @app.post("/api/prueba/productos")
    def crear(datos: ProductoNuevo, session: Annotated[Session, Depends(get_session)]) -> dict:
        session.add(Producto(**datos.model_dump(), m3=Decimal("0.010")))
        session.flush()
        return {"ok": True}

    @app.get("/api/prueba/buscar")
    def buscar(q: Annotated[str, Query(title="Búsqueda", min_length=1)]) -> dict:
        return {"q": q}

    @app.get("/api/prueba/error-api")
    def error_api() -> None:
        raise error(NO_ENCONTRADO)

    @app.get("/api/prueba/explota")
    def explota() -> None:
        raise RuntimeError("detalle interno que no debe salir")

    if db is not None:

        def sesion() -> Iterator[Session]:
            yield db

        app.dependency_overrides[get_session] = sesion
    return app


@pytest.fixture
def cliente(db: Session) -> TestClient:
    return TestClient(app_de_prueba(db), raise_server_exceptions=False)


VALIDO = {"sku": "RES-0500", "nombre": "Resma", "piezas_por_bulto": 10, "kg": "25.0"}


def test_error_api_responde_tal_cual(cliente: TestClient) -> None:
    r = cliente.get("/api/prueba/error-api")
    assert r.status_code == 404
    assert r.json() == {"detail": "No encontramos el registro", "code": "no_encontrado"}


def test_campo_faltante_usa_la_etiqueta_del_prototipo(cliente: TestClient) -> None:
    r = cliente.post("/api/prueba/productos", json={k: v for k, v in VALIDO.items() if k != "sku"})
    assert r.status_code == 422
    assert r.json() == {
        "detail": "Completa SKU",
        "code": "validacion",
        "campos": {"sku": "Completa SKU"},
    }


def test_campo_vacio_cuenta_como_faltante(cliente: TestClient) -> None:
    r = cliente.post("/api/prueba/productos", json=VALIDO | {"nombre": ""})
    assert r.json()["campos"] == {"nombre": "Completa Producto"}


def test_varios_campos_y_detail_del_primero(cliente: TestClient) -> None:
    r = cliente.post("/api/prueba/productos", json={"piezas_por_bulto": 0, "kg": "-1"})
    cuerpo = r.json()
    assert cuerpo["code"] == "validacion"
    assert cuerpo["campos"] == {
        "sku": "Completa SKU",
        "nombre": "Completa Producto",
        "piezas_por_bulto": "Piezas/bulto debe ser mayor a 0",
        "kg": "El peso debe ser mayor a 0",
    }
    assert cuerpo["detail"] == "Completa SKU"


def test_mensajes_en_espanol_para_tipos(cliente: TestClient) -> None:
    r = cliente.post("/api/prueba/productos", json=VALIDO | {"piezas_por_bulto": "diez"})
    assert r.json()["campos"] == {"piezas_por_bulto": "Piezas/bulto debe ser un número entero"}
    r = cliente.post("/api/prueba/productos", json=VALIDO | {"sku": "X" * 21})
    assert r.json()["campos"] == {"sku": "SKU admite hasta 20 caracteres"}


def test_cuerpo_que_no_es_json(cliente: TestClient) -> None:
    r = cliente.post(
        "/api/prueba/productos", content="{no es json", headers={"content-type": "application/json"}
    )
    assert r.status_code == 422
    assert r.json()["detail"] == "El cuerpo de la petición no es JSON válido"


def test_parametro_de_consulta_con_titulo(cliente: TestClient) -> None:
    r = cliente.get("/api/prueba/buscar")
    assert r.json() == {
        "detail": "Completa Búsqueda",
        "code": "validacion",
        "campos": {"q": "Completa Búsqueda"},
    }


def test_restriccion_unica_de_postgresql(cliente: TestClient) -> None:
    assert cliente.post("/api/prueba/productos", json=VALIDO).status_code == 200
    r = cliente.post("/api/prueba/productos", json=VALIDO)
    assert r.status_code == 409
    assert r.json() == {
        "detail": "Este SKU ya está registrado",
        "code": "sku_duplicado",
        "campos": {"sku": "Este SKU ya está registrado"},
    }


def test_restriccion_check_de_postgresql(cliente: TestClient) -> None:
    # El esquema de prueba no revisa el formato del SKU: lo detiene la base.
    r = cliente.post("/api/prueba/productos", json=VALIDO | {"sku": "res 0500"})
    assert r.status_code == 422
    assert r.json() == {
        "detail": "El SKU no es válido",
        "code": "validacion",
        "campos": {"sku": "El SKU no es válido"},
    }


def test_ruta_inexistente(cliente: TestClient) -> None:
    r = cliente.get("/api/no-existe")
    assert r.status_code == 404
    assert r.json() == {"detail": "No encontramos el registro", "code": "no_encontrado"}


def test_metodo_no_permitido(cliente: TestClient) -> None:
    r = cliente.delete("/api/health")
    assert r.status_code == 405
    assert r.json()["code"] == "metodo_no_permitido"


def test_error_no_previsto_no_filtra_detalles(
    cliente: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    r = cliente.get("/api/prueba/explota")
    assert r.status_code == 500
    assert r.json() == {"detail": "Algo salió mal. Intenta de nuevo", "code": "error_interno"}
    assert "detalle interno" not in r.text
    assert "detalle interno que no debe salir" in caplog.text


def test_error_api_con_campos() -> None:
    err = ErrorApi(409, "rack_ocupado", "Ese rack ya está asignado", {"clave": "Ese rack…"})
    assert err.cuerpo() == {
        "detail": "Ese rack ya está asignado",
        "code": "rack_ocupado",
        "campos": {"clave": "Ese rack…"},
    }
