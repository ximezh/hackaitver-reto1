"""BE-22: citas por andén sin empalmes (R-02, R-03, A-08) y folio de factura (R-04)."""

import threading
from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import tiempo
from app.contrasenas import hashear
from app.db import get_engine
from app.models import (
    Anden,
    Cita,
    FacturaProducto,
    OrdenCompra,
    ParteOc,
    Proveedor,
    Rack,
    Sucursal,
    Usuario,
)
from tests.conftest import entrar

RUTA = "/api/citas"
HOY = date(2026, 11, 25)  # miércoles
JUEVES = "2026-11-26"


@pytest.fixture(autouse=True)
def miercoles_temprano(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tiempo, "hoy", lambda: HOY)
    monkeypatch.setattr(tiempo, "ahora", lambda: datetime.combine(HOY, time(7, 0), tiempo.ZONA))


@pytest.fixture
def golfo(api: TestClient, semillas: None) -> dict[str, str]:
    return entrar(api, "pgolfo")


@pytest.fixture
def atlas(api: TestClient, db: Session, semillas: None) -> dict[str, str]:
    prov = db.scalars(select(Proveedor).filter_by(rfc="DAT110820KL3")).one()
    db.add(Usuario(usuario="datlas", nombre="Distribuidora Atlas", rol="proveedor", canal="web",
                   contrasena_hash=hashear("cedis2026"), contrasena_temporal=False,
                   proveedor_id=prov.id))  # fmt: skip
    db.commit()
    return entrar(api, "datlas")


def pedir(api: TestClient, *lineas: tuple[str, int]) -> str:
    cuerpo = {"lineas": [{"sku": s, "bultos": b} for s, b in lineas]}
    return api.post("/api/pedidos", json=cuerpo, headers=entrar(api, "suc07")).json()["folio"]


@pytest.fixture
def oc(api: TestClient, semillas: None) -> str:
    """OC con hojas y resmas de Papelera del Golfo y lápices de Atlas."""
    return pedir(api, ("PAP-0100", 14), ("RES-0500", 10), ("LAP-0012", 2))


def cita(oc: str, **cambios: object) -> dict:
    datos = {
        "oc": oc,
        "folio_factura": "FAC-A-20418",
        "anden": "R1",
        "dia": JUEVES,
        "inicio": "11:00",
        "duracion_min": 60,
    }
    return datos | cambios


def agendar(api: TestClient, encabezado: dict, oc: str, **cambios: object):
    return api.post(RUTA, json=cita(oc, **cambios), headers=encabezado)


# --- Agendar ---------------------------------------------------------------------------


def test_agenda_la_cita(api: TestClient, golfo: dict, oc: str) -> None:
    r = agendar(api, golfo, oc, folio_factura=" fac-a-20418 ")
    assert r.status_code == 201
    cuerpo = r.json()
    ignorar = ("id", "creado_en", "sucursal", "proveedor")
    assert {k: v for k, v in cuerpo.items() if k not in ignorar} == {
        "oc": oc,
        "folio_factura": "FAC-A-20418",
        "anden": "R1",
        "dia": JUEVES,
        "inicio": "11:00",
        "fin": "12:00",
        "duracion_min": 60,
        "bultos": 24,
        "estado": "programada",
    }  # fmt: skip
    assert cuerpo["proveedor"]["nombre"] == "Papelera del Golfo"
    assert cuerpo["sucursal"]["nombre"] == "Suc. 07 Boca del Río"


def test_la_oc_pasa_a_proveedor_y_se_estima_la_llegada(
    api: TestClient, golfo: dict, atlas: dict, oc: str
) -> None:
    suc = entrar(api, "suc07")
    agendar(api, golfo, oc)
    pedido = api.get(f"/api/pedidos/{oc}", headers=suc).json()
    assert (pedido["paso"], pedido["paso_indice"]) == ("proveedor", 1)
    assert pedido["partes"][0]["cita"] == {
        "anden": "R1",
        "dia": JUEVES,
        "inicio": "11:00",
        "fin": "12:00",
    }
    assert pedido["llega_estimado"] == "2026-11-28"  # aún falta la cita de Atlas
    # Atlas agenda el sábado: llega el siguiente día hábil, el lunes (C2-02).
    agendar(api, atlas, oc, folio_factura="FAC-AT-7", anden="R2", dia="2026-11-28")
    assert api.get(f"/api/pedidos/{oc}", headers=suc).json()["llega_estimado"] == "2026-11-30"


def test_la_orden_del_proveedor_muestra_su_cita_y_factura(
    api: TestClient, golfo: dict, oc: str
) -> None:
    agendar(api, golfo, oc)
    orden = api.get("/api/proveedor/ordenes", headers=golfo).json()["items"][0]
    assert orden["cita"] | {"id": 0} == {
        "id": 0,
        "anden": "R1",
        "dia": JUEVES,
        "inicio": "11:00",
        "fin": "12:00",
        "estado": "programada",
    }
    assert orden["factura"] == {"folio": "FAC-A-20418", "bultos_capturados": 0}
    sin_cita = api.get("/api/proveedor/ordenes", params={"sin_cita": True}, headers=golfo).json()
    assert sin_cita["total"] == 0


@pytest.mark.parametrize(("duracion", "fin"), [(90, "12:30"), (120, "13:00"), (180, "14:00")])
def test_duraciones(api: TestClient, golfo: dict, oc: str, duracion: int, fin: str) -> None:
    assert agendar(api, golfo, oc, duracion_min=duracion).json()["fin"] == fin


def test_puede_terminar_a_las_18(api: TestClient, golfo: dict, oc: str) -> None:
    r = agendar(api, golfo, oc, inicio="17:00", duracion_min=60)
    assert (r.status_code, r.json()["fin"]) == (201, "18:00")


# --- Empalmes --------------------------------------------------------------------------


def test_anden_ocupado(api: TestClient, golfo: dict, atlas: dict, oc: str) -> None:
    agendar(api, golfo, oc, inicio="11:00", duracion_min=120)
    r = agendar(api, atlas, oc, folio_factura="FAC-AT-7", inicio="12:30")
    assert r.status_code == 409
    assert r.json() == {
        "detail": "Ese andén ya está ocupado",
        "code": "anden_ocupado",
        "campos": {"anden": "Ese andén ya está ocupado"},
    }


def test_otro_anden_a_la_misma_hora(api: TestClient, golfo: dict, atlas: dict, oc: str) -> None:
    agendar(api, golfo, oc)
    assert agendar(api, atlas, oc, folio_factura="FAC-AT-7", anden="R2").status_code == 201


def test_una_cita_empieza_cuando_termina_otra(
    api: TestClient, golfo: dict, atlas: dict, oc: str
) -> None:
    agendar(api, golfo, oc, inicio="11:00", duracion_min=60)
    r = agendar(api, atlas, oc, folio_factura="FAC-AT-7", inicio="12:00")
    assert r.status_code == 201


def test_la_base_impide_el_empalme_aunque_se_salte_la_revision(
    api: TestClient, golfo: dict, atlas: dict, oc: str, db: Session
) -> None:
    agendar(api, golfo, oc)
    parte_atlas = db.scalars(
        select(ParteOc).join(ParteOc.oc).join(ParteOc.proveedor)
        .where(OrdenCompra.folio == oc, Proveedor.rfc == "DAT110820KL3")
    ).one()  # fmt: skip
    r1 = db.scalars(select(Anden).filter_by(clave="R1")).one()
    inicio = datetime.combine(date(2026, 11, 26), time(11, 30), tiempo.ZONA)
    with pytest.raises(IntegrityError) as error, db.begin_nested():
        db.add(Cita(parte=parte_atlas, anden=r1, inicio=inicio, fin=inicio + timedelta(hours=1)))
        db.flush()
    assert error.value.orig.diag.constraint_name == "ex_citas_sin_empalme"  # type: ignore[union-attr]


def test_dos_citas_simultaneas_solo_gana_una() -> None:
    """Dos proveedores confirman el mismo hueco al mismo tiempo, en conexiones distintas (A-08)."""
    engine = get_engine()
    with Session(engine) as s:
        rack = s.scalars(select(Rack).filter_by(clave="R-32")).one_or_none()
        rack_nuevo = rack is None
        rack = rack or Rack(clave="R-32")
        anden = s.scalars(select(Anden).filter_by(clave="R4")).one_or_none()
        anden_nuevo = anden is None
        anden = anden or Anden(clave="R4", tipo="recibo")
        suc = Sucursal(clave="32", nombre="Suc. 32 Prueba", ciudad="Prueba", rack=rack)
        provs = [Proveedor(rfc=f"ZZQ0101{n}1AB1", nombre=f"Prueba {n}") for n in (1, 2)]
        oc = OrdenCompra(folio="OC-99-0001", sucursal=suc)
        partes = [ParteOc(oc=oc, proveedor=p) for p in provs]
        s.add_all([rack, anden, suc, *provs, oc, *partes])
        s.commit()
        ids = {
            "rack": rack.id,
            "anden": anden.id,
            "suc": suc.id,
            "oc": oc.id,
            "partes": [p.id for p in partes],
            "provs": [p.id for p in provs],
        }

    inicio = datetime.combine(date(2026, 12, 1), time(9, 0), tiempo.ZONA)
    barrera = threading.Barrier(2)
    resultados: list[str] = []

    def confirmar(parte_id: int) -> None:
        with Session(engine) as s:
            s.add(Cita(parte_id=parte_id, anden_id=ids["anden"], inicio=inicio,
                       fin=inicio + timedelta(hours=1)))  # fmt: skip
            barrera.wait()
            try:
                s.commit()
                resultados.append("ok")
            except IntegrityError as exc:
                resultados.append(exc.orig.diag.constraint_name)  # type: ignore[union-attr]

    hilos = [threading.Thread(target=confirmar, args=(p,)) for p in ids["partes"]]
    try:
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(timeout=30)
        assert sorted(resultados) == ["ex_citas_sin_empalme", "ok"]
    finally:
        with Session(engine) as s:
            s.execute(delete(Cita).where(Cita.parte_id.in_(ids["partes"])))
            s.execute(delete(ParteOc).where(ParteOc.id.in_(ids["partes"])))
            s.execute(delete(OrdenCompra).where(OrdenCompra.id == ids["oc"]))
            s.execute(delete(Proveedor).where(Proveedor.id.in_(ids["provs"])))
            s.execute(delete(Sucursal).where(Sucursal.id == ids["suc"]))
            if anden_nuevo:
                s.execute(delete(Anden).where(Anden.id == ids["anden"]))
            if rack_nuevo:
                s.execute(delete(Rack).where(Rack.id == ids["rack"]))
            s.commit()


# --- Folio de factura (R-04) -----------------------------------------------------------


@pytest.mark.parametrize(
    ("folio", "mensaje"),
    [
        ("", "El folio es obligatorio"),
        ("   ", "El folio es obligatorio"),
        ("A-20418", "El folio debe empezar con FAC-"),
        ("FAC-" + "9" * 30, "El folio admite hasta 30 caracteres"),
    ],
)
def test_forma_del_folio(api: TestClient, golfo: dict, oc: str, folio: str, mensaje: str) -> None:
    r = agendar(api, golfo, oc, folio_factura=folio)
    assert r.status_code == 422
    assert r.json()["campos"] == {"folio_factura": mensaje}


def test_folio_repetido_para_el_mismo_producto(api: TestClient, golfo: dict, oc: str) -> None:
    agendar(api, golfo, oc)
    otra = pedir(api, ("PAP-0100", 1))  # otra OC con un producto que ya usó el folio
    r = agendar(api, golfo, otra, anden="R2")
    assert r.status_code == 409
    assert r.json()["code"] == "folio_registrado"
    assert r.json()["detail"] == "Este folio ya está registrado"


def test_mismo_folio_para_productos_distintos(
    api: TestClient, golfo: dict, oc: str, db: Session
) -> None:
    """Una factura cubre varios productos; el folio solo choca por producto (P-02)."""
    from app.models import Producto

    agendar(api, golfo, oc)
    golfo_id = db.scalars(select(Proveedor.id).filter_by(rfc="PGO090312AB1")).one()
    db.scalars(select(Producto).filter_by(sku="CLI-0100")).one().proveedor_id = golfo_id
    db.commit()
    otra = pedir(api, ("CLI-0100", 1))
    assert agendar(api, golfo, otra, anden="R2").status_code == 201


def test_el_folio_se_registra_por_producto(
    api: TestClient, golfo: dict, oc: str, db: Session
) -> None:
    agendar(api, golfo, oc)
    registrados = db.scalars(select(FacturaProducto).filter_by(folio="FAC-A-20418")).all()
    assert len(registrados) == 2  # hojas y resmas


def test_verificar_folio(api: TestClient, golfo: dict, oc: str) -> None:
    verificar = lambda folio: api.get(  # noqa: E731
        "/api/facturas/verificar", params={"folio": folio, "oc": oc}, headers=golfo
    ).json()
    assert verificar("fac-a-20418") == {"folio": "FAC-A-20418", "disponible": True, "detail": None}
    assert verificar("") == {"folio": "", "disponible": False, "detail": "El folio es obligatorio"}
    agendar(api, golfo, oc)
    otra = pedir(api, ("PAP-0100", 1))
    r = api.get(
        "/api/facturas/verificar", params={"folio": "FAC-A-20418", "oc": otra}, headers=golfo
    )
    assert r.json() == {
        "folio": "FAC-A-20418",
        "disponible": False,
        "detail": "Este folio ya está registrado",
    }


# --- Horario y día (R-02) --------------------------------------------------------------


@pytest.mark.parametrize(
    ("cambios", "campo", "mensaje"),
    [
        (
            {"inicio": "07:30"},
            "inicio",
            "Elige un horario de 8:00 a 18:00 en bloques de 30 minutos",
        ),
        (
            {"inicio": "18:00"},
            "inicio",
            "Elige un horario de 8:00 a 18:00 en bloques de 30 minutos",
        ),
        (
            {"inicio": "10:15"},
            "inicio",
            "Elige un horario de 8:00 a 18:00 en bloques de 30 minutos",
        ),
        ({"inicio": "diez"}, "inicio", "Elige un horario de 8:00 a 18:00 en bloques de 30 minutos"),
        (
            {"inicio": "17:30", "duracion_min": 60},
            "inicio",
            "La cita debe terminar a más tardar a las 18:00",
        ),
        ({"duracion_min": 45}, "duracion_min", "Elige una duración de 1, 1.5, 2 o 3 h"),
        ({"dia": "2026-11-29"}, "dia", "Las citas son de lunes a sábado"),
        ({"dia": "2026-11-24"}, "dia", "Ese día ya pasó"),
        ({"dia": "2026-12-10"}, "dia", "Solo se agenda hasta 2 semanas adelante"),
        ({"anden": "E1"}, "anden", "Elige un andén de recibo, de R1 a R4"),
        ({"anden": "R9"}, "anden", "Elige un andén de recibo, de R1 a R4"),
    ],
)
def test_reglas_del_calendario(
    api: TestClient, golfo: dict, oc: str, cambios: dict, campo: str, mensaje: str
) -> None:
    r = agendar(api, golfo, oc, **cambios)
    assert r.status_code == 422
    assert r.json()["campos"] == {campo: mensaje}


def test_hasta_dos_semanas_justas(api: TestClient, golfo: dict, oc: str) -> None:
    assert agendar(api, golfo, oc, dia="2026-12-09").status_code == 201


def test_hoy_pero_en_una_hora_que_ya_paso(
    api: TestClient, golfo: dict, oc: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tiempo, "ahora", lambda: datetime.combine(HOY, time(12, 0), tiempo.ZONA))
    r = agendar(api, golfo, oc, dia="2026-11-25", inicio="11:00")
    assert r.json()["campos"] == {"inicio": "Ese horario ya pasó"}


# --- Reglas de la parte ----------------------------------------------------------------


def test_una_cita_por_parte(api: TestClient, golfo: dict, oc: str) -> None:
    agendar(api, golfo, oc)
    r = agendar(api, golfo, oc, folio_factura="FAC-B-1", anden="R3")
    assert (r.status_code, r.json()["code"]) == (409, "cita_existente")


def test_oc_ajena_o_inexistente(api: TestClient, golfo: dict, semillas: None) -> None:
    solo_atlas = pedir(api, ("LAP-0012", 1))
    assert agendar(api, golfo, solo_atlas).json()["code"] == "no_encontrado"
    assert agendar(api, golfo, "OC-26-9999").json()["code"] == "no_encontrado"


def test_proveedor_suspendido_no_agenda(api: TestClient, golfo: dict, oc: str, db: Session) -> None:
    db.scalars(select(Proveedor).filter_by(rfc="PGO090312AB1")).one().estado = "suspendido"
    db.commit()
    r = agendar(api, golfo, oc)
    assert (r.status_code, r.json()["code"]) == (409, "proveedor_suspendido")


# --- Disponibilidad --------------------------------------------------------------------


def test_disponibilidad_vacia(api: TestClient, golfo: dict) -> None:
    r = api.get(f"{RUTA}/disponibilidad", params={"dia": JUEVES}, headers=golfo)
    assert r.json() == {
        "dia": JUEVES,
        "abre": "08:00",
        "cierra": "18:00",
        "bloque_min": 30,
        "andenes": [{"anden": f"R{n}", "ocupados": []} for n in range(1, 5)],
    }


def test_disponibilidad_propia_y_ajena(api: TestClient, golfo: dict, atlas: dict, oc: str) -> None:
    agendar(api, golfo, oc)
    agendar(api, atlas, oc, folio_factura="FAC-AT-7", inicio="08:00")

    def ocupados(enc: dict) -> list:
        r = api.get(f"{RUTA}/disponibilidad", params={"dia": JUEVES}, headers=enc)
        return r.json()["andenes"][0]["ocupados"]

    assert ocupados(golfo) == [
        {"inicio": "08:00", "fin": "09:00", "etiqueta": "Distribuidora Atlas", "propia": False},
        {"inicio": "11:00", "fin": "12:00", "etiqueta": oc, "propia": True},
    ]
    assert [o["propia"] for o in ocupados(atlas)] == [True, False]
    otro_dia = api.get(f"{RUTA}/disponibilidad", params={"dia": "2026-11-27"}, headers=golfo)
    assert all(a["ocupados"] == [] for a in otro_dia.json()["andenes"])


def test_disponibilidad_valida_el_dia(api: TestClient, golfo: dict) -> None:
    r = api.get(f"{RUTA}/disponibilidad", params={"dia": "2026-11-29"}, headers=golfo)
    assert r.json()["campos"] == {"dia": "Las citas son de lunes a sábado"}
    assert api.get(f"{RUTA}/disponibilidad", headers=golfo).json()["campos"] == {
        "dia": "Completa Día"
    }


@pytest.mark.parametrize("usuario", ["suc07", "admin.cedis"])
def test_solo_proveedor(api: TestClient, semillas: None, usuario: str) -> None:
    r = api.get(f"{RUTA}/disponibilidad", params={"dia": JUEVES}, headers=entrar(api, usuario))
    assert r.json()["code"] == "sin_permiso"
