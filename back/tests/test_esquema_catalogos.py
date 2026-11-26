"""BE-02: las restricciones del esquema se cumplen en PostgreSQL, no solo en la API."""

from decimal import Decimal
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import BACK_DIR
from app.models import Anden, Producto, Proveedor, Rack, Sucursal, Usuario


def viola(db: Session, restriccion: str | set[str], *registros: object) -> None:
    """Afirma que guardar los registros rompe la restricción indicada (o una del conjunto).

    Un conjunto se usa cuando un valor rompe varias reglas a la vez: PostgreSQL reporta la
    primera que revisa, y ese orden no está garantizado.
    """
    esperadas = {restriccion} if isinstance(restriccion, str) else restriccion
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add_all(registros)
        db.flush()
    assert error.value.orig.diag.constraint_name in esperadas  # type: ignore[union-attr]


def guarda(db: Session, *registros: object) -> None:
    db.add_all(registros)
    db.flush()


# --- Fábricas con datos del prototipo ---------------------------------------------------


def proveedor(**cambios: Any) -> Proveedor:
    datos = {"rfc": "PGO090312AB1", "nombre": "Papelera del Golfo"} | cambios
    return Proveedor(**datos)


def producto(**cambios: Any) -> Producto:
    datos = {
        "sku": "RES-0500",
        "nombre": "Resma carta 500 hojas",
        "piezas_por_bulto": 10,
        "kg": Decimal("25.0"),
        "m3": Decimal("0.032"),
    } | cambios
    return Producto(**datos)


def sucursal(rack: Rack, **cambios: Any) -> Sucursal:
    datos = {"clave": "07", "nombre": "Suc. 07 Boca del Río", "ciudad": "Boca del Río"} | cambios
    return Sucursal(rack=rack, **datos)


def usuario(**cambios: Any) -> Usuario:
    datos = {
        "usuario": "caseta.jlopez",
        "nombre": "Jorge López",
        "rol": "caseta",
        "canal": "android",
        "contrasena_hash": "$argon2id$prueba",
    } | cambios
    return Usuario(**datos)


# --- Migración -------------------------------------------------------------------------


def test_los_modelos_coinciden_con_la_migracion() -> None:
    # Falla si alguien cambia un modelo sin generar su migración.
    command.check(Config(BACK_DIR / "alembic.ini"))


def test_la_migracion_se_revierte_y_se_vuelve_a_aplicar() -> None:
    config = Config(BACK_DIR / "alembic.ini")
    command.downgrade(config, "base")
    command.upgrade(config, "head")


# --- Productos -------------------------------------------------------------------------


def test_producto_con_valores_por_omision(db: Session) -> None:
    p = producto()
    guarda(db, p)
    db.refresh(p)
    assert (p.ilustracion, p.unidad, p.estado) == ("bulto", "piezas", "activo")
    assert p.creado_en is not None


def test_sku_unico(db: Session) -> None:
    guarda(db, producto())
    viola(db, "uq_productos_sku", producto(nombre="Otra resma"))


@pytest.mark.parametrize("sku", ["res-0500", "R", "RES 0500"])
def test_sku_con_formato(db: Session, sku: str) -> None:
    viola(db, "ck_productos_sku_formato", producto(sku=sku))


@pytest.mark.parametrize(
    ("campo", "valor", "restriccion"),
    [
        ("piezas_por_bulto", 0, "ck_productos_piezas_positivas"),
        ("kg", Decimal("0"), "ck_productos_kg_positivo"),
        ("m3", Decimal("-0.001"), "ck_productos_m3_positivo"),
    ],
)
def test_piezas_peso_y_volumen_mayores_a_cero(
    db: Session, campo: str, valor: object, restriccion: str
) -> None:
    viola(db, restriccion, producto(**{campo: valor}))


def test_ilustracion_de_la_lista(db: Session) -> None:
    viola(db, "ck_productos_ilustracion", producto(ilustracion="camion"))


def test_producto_con_proveedor_principal(db: Session) -> None:
    prov = proveedor()
    p = producto(proveedor=prov)
    guarda(db, p)
    assert prov.productos == [p]


# --- Proveedores -----------------------------------------------------------------------


def test_rfc_unico(db: Session) -> None:
    guarda(db, proveedor())
    viola(db, "uq_proveedores_rfc", proveedor(nombre="Otra papelera"))


@pytest.mark.parametrize("rfc", ["PGO090312AB1", "PEGL800101AB1", "ÑAF090312AB1", "A&B090312XY9"])
def test_rfc_valido_de_persona_moral_o_fisica(db: Session, rfc: str) -> None:
    guarda(db, proveedor(rfc=rfc))


@pytest.mark.parametrize("rfc", ["pgo090312ab1", "PG090312AB1", "PGO0903AB1", "PGO090312AB"])
def test_rfc_invalido(db: Session, rfc: str) -> None:
    viola(db, "ck_proveedores_rfc_formato", proveedor(rfc=rfc))


def test_estado_de_proveedor(db: Session) -> None:
    guarda(db, proveedor(estado="suspendido"))
    viola(db, "ck_proveedores_estado", proveedor(rfc="DAT110820KL3", estado="baja"))


# --- Racks, sucursales y andenes -------------------------------------------------------


@pytest.mark.parametrize("clave", ["R-00", "R-33", "R-7", "R1"])
def test_rack_de_r01_a_r32(db: Session, clave: str) -> None:
    viola(db, "ck_racks_clave_formato", Rack(clave=clave))


def test_clave_de_sucursal_unica(db: Session) -> None:
    guarda(db, sucursal(Rack(clave="R-07")))
    viola(db, "uq_sucursales_clave", sucursal(Rack(clave="R-08")))


def test_dos_sucursales_no_comparten_rack(db: Session) -> None:
    rack = Rack(clave="R-07")
    guarda(db, sucursal(rack))
    # Por `rack_id` y no por la relación: en memoria, SQLAlchemy movería el rack de sucursal.
    otra = Sucursal(clave="08", nombre="Suc. 08", ciudad="Veracruz", rack_id=rack.id)
    viola(db, "uq_sucursales_rack_id", otra)


@pytest.mark.parametrize("clave", ["00", "33", "7", "A1"])
def test_clave_de_sucursal_de_01_a_32(db: Session, clave: str) -> None:
    viola(db, "ck_sucursales_clave_formato", sucursal(Rack(clave="R-09"), clave=clave))


@pytest.mark.parametrize(
    ("clave", "tipo"), [("R1", "recibo"), ("R4", "recibo"), ("E3", "embarque")]
)
def test_andenes_validos(db: Session, clave: str, tipo: str) -> None:
    guarda(db, Anden(clave=clave, tipo=tipo))


@pytest.mark.parametrize(
    ("clave", "tipo"), [("R5", "recibo"), ("E1", "recibo"), ("R1", "embarque")]
)
def test_anden_con_clave_de_su_tipo(db: Session, clave: str, tipo: str) -> None:
    viola(db, "ck_andenes_clave_de_tipo", Anden(clave=clave, tipo=tipo))


def test_clave_de_anden_unica(db: Session) -> None:
    guarda(db, Anden(clave="R1", tipo="recibo"))
    viola(db, "uq_andenes_clave", Anden(clave="R1", tipo="recibo"))


# --- Usuarios --------------------------------------------------------------------------


def test_usuario_con_valores_por_omision(db: Session) -> None:
    u = usuario()
    guarda(db, u)
    db.refresh(u)
    assert (u.contrasena_temporal, u.estado) == (True, "activo")


def test_usuario_unico(db: Session) -> None:
    guarda(db, usuario())
    viola(db, "uq_usuarios_usuario", usuario(nombre="Otro Jorge"))


@pytest.mark.parametrize("nombre", ["Caseta.JLopez", "ab", ".caseta", "caseta jlopez"])
def test_usuario_en_minusculas_y_con_formato(db: Session, nombre: str) -> None:
    viola(db, "ck_usuarios_usuario_formato", usuario(usuario=nombre, rol="oficina", canal="web"))


def test_rol_de_la_lista(db: Session) -> None:
    # Un rol fuera de la lista tampoco tiene canal válido: cualquiera de las dos lo detiene.
    viola(
        db,
        {"ck_usuarios_rol", "ck_usuarios_canal_de_rol"},
        usuario(rol="admin", usuario="admin.cedis", canal="web"),
    )


@pytest.mark.parametrize(("rol", "canal"), [("caseta", "web"), ("oficina", "android")])
def test_el_canal_lo_define_el_rol(db: Session, rol: str, canal: str) -> None:
    viola(db, "ck_usuarios_canal_de_rol", usuario(rol=rol, canal=canal, usuario="ana.dominguez"))


@pytest.mark.parametrize(
    ("rol", "nombre"),
    [("caseta", "desem.mruiz"), ("desembarque", "mruiz"), ("embarque", "embarcruz")],
)
def test_rol_de_android_exige_su_prefijo(db: Session, rol: str, nombre: str) -> None:
    viola(db, "ck_usuarios_prefijo_de_rol", usuario(rol=rol, usuario=nombre))


@pytest.mark.parametrize(
    ("rol", "nombre"),
    [("caseta", "caseta.jlopez"), ("desembarque", "desem.mruiz"), ("embarque", "embar.acruz")],
)
def test_usuarios_de_android_del_prototipo(db: Session, rol: str, nombre: str) -> None:
    guarda(db, usuario(rol=rol, usuario=nombre))


def test_rol_web_no_usa_prefijo_de_android(db: Session) -> None:
    viola(db, "ck_usuarios_prefijo_de_rol", usuario(rol="oficina", canal="web"))


def test_sucursal_exige_su_sucursal(db: Session) -> None:
    datos = {"rol": "sucursal", "canal": "web", "usuario": "suc07"}
    viola(db, "ck_usuarios_sucursal_solo_de_rol_sucursal", usuario(**datos))
    guarda(db, usuario(**datos, sucursal=sucursal(Rack(clave="R-07"))))


def test_proveedor_exige_su_proveedor(db: Session) -> None:
    datos = {"rol": "proveedor", "canal": "web", "usuario": "pgolfo"}
    viola(db, "ck_usuarios_proveedor_solo_de_rol_proveedor", usuario(**datos))
    guarda(db, usuario(**datos, proveedor=proveedor()))


def test_otros_roles_no_llevan_sucursal_ni_proveedor(db: Session) -> None:
    viola(
        db,
        "ck_usuarios_sucursal_solo_de_rol_sucursal",
        usuario(sucursal=sucursal(Rack(clave="R-07"))),
    )
    viola(db, "ck_usuarios_proveedor_solo_de_rol_proveedor", usuario(proveedor=proveedor()))
