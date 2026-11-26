"""Semillas con los datos de ejemplo del prototipo (BE-03).

    uv run python -m app.seeds

Fuentes: `design/CEDIS Flow/components/bundle.js` (productos, sucursales y proveedores),
`Oficina/preview.html` (RFC, contactos y usuarios) y `LoginWeb/preview.html` (`admin.cedis`).

Es idempotente: solo agrega lo que falta, identificado por su clave natural (SKU, RFC, clave,
usuario). No sobrescribe lo que Oficina haya editado. En producción no corre sin
`--permitir-produccion`.
"""

import argparse
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contrasenas import hashear
from app.db import get_engine
from app.models import Anden, Producto, Proveedor, Rack, Sucursal, Usuario
from app.models.comun import CANAL_DE_ROL, EstadoProveedor, Rol, TipoAnden

CONTRASENA_DEMO = "cedis2026"

GOLFO, ATLAS, ESCOLAR, SURESTE = "PGO090312AB1", "DAT110820KL3", "GEM150101QW8", "USU180507ZX2"

PROVEEDORES = [
    (GOLFO, "Papelera del Golfo", "Laura Pérez", "229 555 0142", EstadoProveedor.ACTIVO),
    (ATLAS, "Distribuidora Atlas", "Hugo Ríos", "228 555 0193", EstadoProveedor.ACTIVO),
    (ESCOLAR, "Grupo Escolar MX", "Sofía Lara", "55 5555 0110", EstadoProveedor.ACTIVO),
    (SURESTE, "Útiles del Sureste", "Iván Cruz", "999 555 0177", EstadoProveedor.SUSPENDIDO),
]

# (sku, nombre, ilustración, unidad, piezas por bulto, kg, m³, RFC del proveedor principal).
# El proveedor de cada producto es provisional: el prototipo no lo dice (contrato C1-02).
PRODUCTOS = [
    ("RES-0500", "Resma carta 500 hojas", "hojas", "resmas", 10, "25.0", "0.032", GOLFO),
    ("CUA-0100", "Cuaderno profesional 100 h", "bulto", "cuadernos", 24, "16.8", "0.030", ESCOLAR),
    ("FOL-0100", "Folder carta crema", "bulto", "folders", 100, "9.6", "0.024", ESCOLAR),
    ("ENG-0020", "Engrapadora metálica", "bulto", "piezas", 20, "8.2", "0.020", ATLAS),
    ("PAP-0100", "Hojas carta, paquete 100", "hojas", "paquetes", 10, "5.1", "0.018", GOLFO),
    ("LAP-0012", "Lápiz HB, caja 12", "lapices", "cajas", 24, "2.4", "0.008", ATLAS),
    ("CLI-0100", "Clip #1, caja 100", "clips", "cajas", 40, "1.0", "0.004", ATLAS),
]  # fmt: skip

# (clave, ciudad). El nombre se arma como en el prototipo: «Suc. 07 Boca del Río».
SUCURSALES = [
    ("01", "Centro"),
    ("04", "Xalapa"),
    ("07", "Boca del Río"),
    ("12", "Córdoba"),
    ("18", "Orizaba"),
    ("21", "Tuxpan"),
]

ANDENES = [
    *((f"R{n}", TipoAnden.RECIBO) for n in range(1, 5)),
    *((f"E{n}", TipoAnden.EMBARQUE) for n in range(1, 4)),
]

# (usuario, nombre, rol, clave de sucursal o RFC del proveedor).
USUARIOS = [
    ("caseta.jlopez", "Jorge López", Rol.CASETA, None),
    ("desem.mruiz", "María Ruiz", Rol.DESEMBARQUE, None),
    ("embar.acruz", "Alan Cruz", Rol.EMBARQUE, None),
    ("suc07", "Suc. 07 Boca del Río", Rol.SUCURSAL, "07"),
    ("pgolfo", "Papelera del Golfo", Rol.PROVEEDOR, GOLFO),
    ("admin.cedis", "Ana Domínguez", Rol.OFICINA, None),
]


@dataclass
class Resultado:
    creados: dict[str, int] = field(default_factory=dict)

    def __str__(self) -> str:
        return ", ".join(f"{tabla}: {n}" for tabla, n in self.creados.items())


def _uno(session: Session, modelo: type, **clave: Any) -> Any:
    return session.scalars(select(modelo).filter_by(**clave)).one_or_none()


def _agrega(session: Session, resultado: Resultado, tabla: str, registro: object) -> None:
    session.add(registro)
    resultado.creados[tabla] = resultado.creados.get(tabla, 0) + 1


def cargar(session: Session, contrasena: str = CONTRASENA_DEMO) -> Resultado:
    """Agrega lo que falte de las semillas. No hace commit: lo decide quien llama."""
    tablas = ["racks", "andenes", "proveedores", "productos", "sucursales", "usuarios"]
    r = Resultado(creados=dict.fromkeys(tablas, 0))

    for n in range(1, 33):
        if not _uno(session, Rack, clave=f"R-{n:02d}"):
            _agrega(session, r, "racks", Rack(clave=f"R-{n:02d}"))

    for clave, tipo in ANDENES:
        if not _uno(session, Anden, clave=clave):
            _agrega(session, r, "andenes", Anden(clave=clave, tipo=tipo))

    for rfc, nombre, contacto, telefono, estado in PROVEEDORES:
        if not _uno(session, Proveedor, rfc=rfc):
            prov = Proveedor(
                rfc=rfc, nombre=nombre, contacto=contacto, telefono=telefono, estado=estado
            )
            _agrega(session, r, "proveedores", prov)
    session.flush()

    for sku, nombre, ilustracion, unidad, piezas, kg, m3, rfc in PRODUCTOS:
        if not _uno(session, Producto, sku=sku):
            producto = Producto(
                sku=sku,
                nombre=nombre,
                ilustracion=ilustracion,
                unidad=unidad,
                piezas_por_bulto=piezas,
                kg=Decimal(kg),
                m3=Decimal(m3),
                proveedor=_uno(session, Proveedor, rfc=rfc),
            )
            _agrega(session, r, "productos", producto)

    for clave, ciudad in SUCURSALES:
        if not _uno(session, Sucursal, clave=clave):
            sucursal = Sucursal(
                clave=clave,
                nombre=f"Suc. {clave} {ciudad}",
                ciudad=ciudad,
                rack=_uno(session, Rack, clave=f"R-{clave}"),
            )
            _agrega(session, r, "sucursales", sucursal)
    session.flush()

    # Un solo hash para todos: Argon2 es lento a propósito y la contraseña es la misma.
    contrasena_hash = hashear(contrasena)
    for nombre_usuario, nombre, rol, vinculo in USUARIOS:
        if _uno(session, Usuario, usuario=nombre_usuario):
            continue
        usuario = Usuario(
            usuario=nombre_usuario,
            nombre=nombre,
            rol=rol,
            canal=CANAL_DE_ROL[rol],
            contrasena_hash=contrasena_hash,
            # Los usuarios de demostración entran directo, sin cambio obligatorio (R-17).
            contrasena_temporal=False,
            sucursal=_uno(session, Sucursal, clave=vinculo) if rol == Rol.SUCURSAL else None,
            proveedor=_uno(session, Proveedor, rfc=vinculo) if rol == Rol.PROVEEDOR else None,
        )
        _agrega(session, r, "usuarios", usuario)
    session.flush()
    return r


class ProduccionSinPermisoError(Exception):
    pass


def revisar_entorno(app_env: str, permitir_produccion: bool) -> None:
    if app_env == "production" and not permitir_produccion:
        raise ProduccionSinPermisoError(
            "APP_ENV=production: las semillas no corren en producción. "
            "Si de verdad quieres cargarlas, agrega --permitir-produccion."
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.seeds", description="Carga los datos de ejemplo del prototipo."
    )
    parser.add_argument(
        "--permitir-produccion",
        action="store_true",
        help="Permite cargar las semillas cuando APP_ENV=production.",
    )
    parser.add_argument(
        "--contrasena",
        default=CONTRASENA_DEMO,
        help=f"Contraseña de los usuarios nuevos (por omisión: {CONTRASENA_DEMO}).",
    )
    args = parser.parse_args(argv)

    try:
        revisar_entorno(get_settings().app_env, args.permitir_produccion)
    except ProduccionSinPermisoError as error:
        print(error, file=sys.stderr)
        return 2

    with Session(get_engine()) as session:
        resultado = cargar(session, args.contrasena)
        session.commit()
    print(f"Semillas cargadas. Registros nuevos · {resultado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
