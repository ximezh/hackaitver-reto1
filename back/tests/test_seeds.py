"""BE-03: semillas del prototipo, idempotentes y bloqueadas en producción."""

from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.contrasenas import verificar
from app.models import Anden, Producto, Proveedor, Rack, Sucursal, Usuario
from app.seeds import (
    CONTRASENA_DEMO,
    ProduccionSinPermisoError,
    cargar,
    main,
    revisar_entorno,
)

TOTALES = {
    "racks": 32,
    "andenes": 7,
    "proveedores": 4,
    "productos": 7,
    "sucursales": 6,
    "usuarios": 6,
}
MODELOS = {
    "racks": Rack,
    "andenes": Anden,
    "proveedores": Proveedor,
    "productos": Producto,
    "sucursales": Sucursal,
    "usuarios": Usuario,
}


def conteos(db: Session) -> dict[str, int]:
    return {t: db.scalar(select(func.count()).select_from(m)) or 0 for t, m in MODELOS.items()}


def test_carga_los_datos_del_prototipo(db: Session) -> None:
    resultado = cargar(db)
    assert resultado.creados == TOTALES
    assert conteos(db) == TOTALES


def test_es_idempotente(db: Session) -> None:
    cargar(db)
    segunda = cargar(db)
    assert set(segunda.creados.values()) == {0}
    assert conteos(db) == TOTALES


def test_no_sobrescribe_lo_que_edito_oficina(db: Session) -> None:
    cargar(db)
    resma = db.scalars(select(Producto).filter_by(sku="RES-0500")).one()
    resma.nombre = "Resma carta 500 hojas (editada)"
    db.flush()
    cargar(db)
    db.refresh(resma)
    assert resma.nombre == "Resma carta 500 hojas (editada)"


def test_completa_lo_que_falta(db: Session) -> None:
    cargar(db)
    db.delete(db.scalars(select(Anden).filter_by(clave="E3")).one())
    db.flush()
    assert cargar(db).creados["andenes"] == 1


def test_producto_como_en_el_prototipo(db: Session) -> None:
    cargar(db)
    p = db.scalars(select(Producto).filter_by(sku="CUA-0100")).one()
    assert (p.nombre, p.ilustracion, p.unidad, p.piezas_por_bulto) == (
        "Cuaderno profesional 100 h",
        "bulto",
        "cuadernos",
        24,
    )
    assert (p.kg, p.m3) == (Decimal("16.8"), Decimal("0.030"))
    assert p.proveedor is not None and p.proveedor.nombre == "Grupo Escolar MX"


def test_proveedor_suspendido(db: Session) -> None:
    cargar(db)
    prov = db.scalars(select(Proveedor).filter_by(rfc="USU180507ZX2")).one()
    assert (prov.nombre, prov.estado) == ("Útiles del Sureste", "suspendido")
    assert prov.productos == []


def test_cada_sucursal_en_el_rack_de_su_clave(db: Session) -> None:
    cargar(db)
    sucursales = db.scalars(select(Sucursal).order_by(Sucursal.clave)).all()
    assert [(s.nombre, s.rack.clave) for s in sucursales] == [
        ("Suc. 01 Centro", "R-01"),
        ("Suc. 04 Xalapa", "R-04"),
        ("Suc. 07 Boca del Río", "R-07"),
        ("Suc. 12 Córdoba", "R-12"),
        ("Suc. 18 Orizaba", "R-18"),
        ("Suc. 21 Tuxpan", "R-21"),
    ]


def test_andenes_de_recibo_y_embarque(db: Session) -> None:
    cargar(db)
    andenes = db.scalars(select(Anden).order_by(Anden.clave)).all()
    assert [(a.clave, a.tipo) for a in andenes] == [
        ("E1", "embarque"),
        ("E2", "embarque"),
        ("E3", "embarque"),
        ("R1", "recibo"),
        ("R2", "recibo"),
        ("R3", "recibo"),
        ("R4", "recibo"),
    ]


def test_usuarios_de_demostracion(db: Session) -> None:
    cargar(db)
    usuarios = {u.usuario: u for u in db.scalars(select(Usuario))}
    assert {n: (u.rol, u.canal) for n, u in usuarios.items()} == {
        "caseta.jlopez": ("caseta", "android"),
        "desem.mruiz": ("desembarque", "android"),
        "embar.acruz": ("embarque", "android"),
        "suc07": ("sucursal", "web"),
        "pgolfo": ("proveedor", "web"),
        "admin.cedis": ("oficina", "web"),
    }
    assert usuarios["suc07"].sucursal.clave == "07"  # type: ignore[union-attr]
    assert usuarios["pgolfo"].proveedor.rfc == "PGO090312AB1"  # type: ignore[union-attr]
    assert usuarios["admin.cedis"].nombre == "Ana Domínguez"
    for u in usuarios.values():
        assert not u.contrasena_temporal
        assert u.contrasena_hash.startswith("$argon2id$")
        assert verificar(u.contrasena_hash, CONTRASENA_DEMO)
        assert not verificar(u.contrasena_hash, "otra")


def test_contrasena_de_demostracion_configurable(db: Session) -> None:
    cargar(db, contrasena="staging-2026")
    u = db.scalars(select(Usuario).filter_by(usuario="pgolfo")).one()
    assert verificar(u.contrasena_hash, "staging-2026")


def test_no_corre_en_produccion_sin_bandera() -> None:
    with pytest.raises(ProduccionSinPermisoError, match="--permitir-produccion"):
        revisar_entorno("production", permitir_produccion=False)
    revisar_entorno("production", permitir_produccion=True)
    revisar_entorno("development", permitir_produccion=False)


def test_el_comando_se_detiene_en_produccion(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("app.seeds.get_settings", lambda: type("S", (), {"app_env": "production"}))
    assert main([]) == 2
    assert "no corren en producción" in capsys.readouterr().err
