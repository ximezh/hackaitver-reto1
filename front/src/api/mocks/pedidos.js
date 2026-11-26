/**
 * Mocks de pedidos, órdenes del proveedor y citas (contrato del sprint 2, BE-20 a BE-22).
 */
import { errorMock, registrarMock, respuesta } from '../mock.js'
import { usuarioDeSesion, validacion } from './auth.js'
import { db } from './datos.js'
import { aHora, aMin, esDomingo, hoy, sumarDias } from './fechas.js'

const ANDENES = ['R1', 'R2', 'R3', 'R4']
const DURACIONES = [60, 90, 120, 180]

function conRol(headers, rol) {
  const u = usuarioDeSesion(headers)
  if (u.rol !== rol) throw errorMock(403, 'No tienes acceso a esta sección', 'sin_permiso')
  return u
}

const producto = (sku) => db.productos.find((p) => p.sku === sku)
const proveedorPub = (id) => {
  const p = db.proveedores.find((x) => x.id === id)
  return p ? { id: p.id, nombre: p.nombre } : null
}
const sucursalPub = (id) => {
  const s = db.sucursales.find((x) => x.id === id)
  return { id: s.id, clave: s.clave, nombre: s.nombre }
}
const redondear = (n, d) => Math.round(n * 10 ** d) / 10 ** d

function citaPub(c) {
  return c ? { anden: c.anden, dia: c.dia, inicio: c.inicio, fin: c.fin } : null
}

function pedidoPub(o) {
  const lineas = o.lineas.map((l) => {
    const p = producto(l.sku)
    return {
      producto: {
        id: p.id,
        sku: p.sku,
        nombre: p.nombre,
        ilustracion: p.ilustracion,
        unidad: p.unidad,
        piezas_por_bulto: p.piezas_por_bulto,
      },
      proveedor: proveedorPub(l.proveedor_id),
      bultos: l.bultos,
      piezas: l.bultos * p.piezas_por_bulto,
      kg: redondear(l.bultos * p.kg, 1),
      m3: redondear(l.bultos * p.m3, 3),
    }
  })
  const proveedores = [...new Set(o.lineas.map((l) => l.proveedor_id))]
  const pasos = ['oc_emitida', 'proveedor', 'en_cedis', 'en_tarima', 'en_camino', 'recibido']
  return {
    folio: o.folio,
    creado_en: o.creado_en,
    sucursal: sucursalPub(o.sucursal_id),
    paso: o.paso,
    paso_indice: pasos.indexOf(o.paso),
    llega_estimado: o.llega_estimado,
    embarque: null,
    bultos: lineas.reduce((a, l) => a + l.bultos, 0),
    kg: redondear(
      lineas.reduce((a, l) => a + l.kg, 0),
      1,
    ),
    m3: redondear(
      lineas.reduce((a, l) => a + l.m3, 0),
      3,
    ),
    lineas,
    partes: proveedores.map((id) => ({
      proveedor: proveedorPub(id),
      bultos: o.lineas.filter((l) => l.proveedor_id === id).reduce((a, l) => a + l.bultos, 0),
      cita: citaPub(db.citas.find((c) => c.oc === o.folio && c.proveedor_id === id)),
    })),
  }
}

function ordenProveedorPub(o, proveedorId) {
  const propias = o.lineas.filter((l) => l.proveedor_id === proveedorId)
  const lineas = propias.map((l) => {
    const p = producto(l.sku)
    return {
      producto: {
        id: p.id,
        sku: p.sku,
        nombre: p.nombre,
        ilustracion: p.ilustracion,
        unidad: p.unidad,
        piezas_por_bulto: p.piezas_por_bulto,
        kg: p.kg,
        m3: p.m3,
      },
      bultos: l.bultos,
      piezas: l.bultos * p.piezas_por_bulto,
    }
  })
  const cita = db.citas.find((c) => c.oc === o.folio && c.proveedor_id === proveedorId)
  return {
    oc: o.folio,
    creado_en: o.creado_en,
    sucursal: sucursalPub(o.sucursal_id),
    bultos: lineas.reduce((a, l) => a + l.bultos, 0),
    kg: redondear(
      lineas.reduce((a, l) => a + l.bultos * l.producto.kg, 0),
      1,
    ),
    m3: redondear(
      lineas.reduce((a, l) => a + l.bultos * l.producto.m3, 0),
      3,
    ),
    lineas,
    cita: cita ? citaCompleta(cita) : null,
    factura: cita ? { folio: cita.folio_factura, bultos_capturados: 0 } : null,
  }
}

function citaCompleta(c) {
  const o = db.pedidos.find((x) => x.folio === c.oc)
  return {
    id: c.id,
    oc: c.oc,
    sucursal: sucursalPub(o.sucursal_id),
    proveedor: proveedorPub(c.proveedor_id),
    folio_factura: c.folio_factura,
    anden: c.anden,
    dia: c.dia,
    inicio: c.inicio,
    fin: c.fin,
    duracion_min: c.duracion_min,
    bultos: o.lineas
      .filter((l) => l.proveedor_id === c.proveedor_id)
      .reduce((a, l) => a + l.bultos, 0),
    estado: 'programada',
    creado_en: c.creado_en,
  }
}

function validarDia(dia) {
  const m = !dia
    ? 'Completa Día'
    : esDomingo(dia)
      ? 'Las citas son de lunes a sábado'
      : dia < hoy()
        ? 'Ese día ya pasó'
        : dia > sumarDias(hoy(), 14)
          ? 'Solo se agenda hasta 2 semanas adelante'
          : null
  if (m) throw validacion(m, { dia: m })
}

const normalizarFolio = (f) =>
  String(f ?? '')
    .trim()
    .toUpperCase()

function folioRegistrado(folio, oc, proveedorId) {
  const orden = db.pedidos.find((o) => o.folio === oc)
  const skus = orden
    ? orden.lineas.filter((l) => l.proveedor_id === proveedorId).map((l) => l.sku)
    : []
  return db.facturas.some((f) => f.folio === folio && skus.includes(f.sku))
}

export function registrarPedidos() {
  registrarMock('post', '/pedidos', ({ headers, body }) => {
    const u = conRol(headers, 'sucursal')
    const entrada = Array.isArray(body?.lineas) ? body.lineas : []
    if (!entrada.length) throw validacion('Agrega productos', { lineas: 'Agrega productos' })
    const sumadas = new Map()
    for (const l of entrada) {
      const sku = String(l.sku ?? '').toUpperCase()
      const bultos = Number(l.bultos)
      const error = (m) => validacion(m, { lineas: m })
      if (!(bultos >= 1)) throw error('Los bultos deben ser al menos 1')
      if (bultos > 999) throw error('Un pedido admite hasta 999 bultos por producto')
      const p = producto(sku)
      if (!p || p.estado !== 'activo') throw error(`El producto ${sku} no está disponible`)
      if (!p.proveedor_id) {
        throw error(`El producto ${sku} no tiene proveedor asignado. Comunícate con Oficina`)
      }
      const prov = db.proveedores.find((x) => x.id === p.proveedor_id)
      if (prov?.estado !== 'activo') {
        throw error(`El proveedor de ${sku} está suspendido. Comunícate con Oficina`)
      }
      sumadas.set(sku, (sumadas.get(sku) ?? 0) + bultos)
    }
    const orden = {
      folio: `OC-26-${db.siguienteOc++}`,
      sucursal_id: u.sucursal_id,
      creado_en: new Date().toISOString(),
      paso: 'oc_emitida',
      llega_estimado: sumarDias(hoy(), 3),
      lineas: [...sumadas].map(([sku, bultos]) => ({
        sku,
        bultos,
        proveedor_id: producto(sku).proveedor_id,
      })),
    }
    db.pedidos.push(orden)
    return respuesta(201, pedidoPub(orden))
  })

  registrarMock('get', '/pedidos', ({ headers, query }) => {
    const u = conRol(headers, 'sucursal')
    const enCurso = String(query.en_curso) === 'true'
    const items = db.pedidos
      .filter((o) => o.sucursal_id === u.sucursal_id && (!enCurso || o.paso !== 'recibido'))
      .toReversed()
      .map(pedidoPub)
    return { items, total: items.length }
  })

  registrarMock('get', '/pedidos/:folio', ({ headers, params }) => {
    const u = conRol(headers, 'sucursal')
    const o = db.pedidos.find((x) => x.folio === params.folio && x.sucursal_id === u.sucursal_id)
    if (!o) throw errorMock(404, 'No encontramos el registro', 'no_encontrado')
    return pedidoPub(o)
  })

  registrarMock('get', '/proveedor/ordenes', ({ headers, query }) => {
    const u = conRol(headers, 'proveedor')
    const sinCita = String(query.sin_cita) === 'true'
    const items = db.pedidos
      .filter((o) => o.lineas.some((l) => l.proveedor_id === u.proveedor_id))
      .map((o) => ordenProveedorPub(o, u.proveedor_id))
      .filter((o) => !sinCita || !o.cita)
      .toReversed()
    return { items, total: items.length }
  })

  registrarMock('get', '/citas/disponibilidad', ({ headers, query }) => {
    const u = conRol(headers, 'proveedor')
    validarDia(query.dia)
    return {
      dia: query.dia,
      abre: '08:00',
      cierra: '18:00',
      bloque_min: 30,
      andenes: ANDENES.map((anden) => ({
        anden,
        ocupados: db.citas
          .filter((c) => c.dia === query.dia && c.anden === anden)
          .map((c) => ({
            inicio: c.inicio,
            fin: c.fin,
            etiqueta:
              c.proveedor_id === u.proveedor_id ? c.oc : proveedorPub(c.proveedor_id).nombre,
            propia: c.proveedor_id === u.proveedor_id,
          })),
      })),
    }
  })

  registrarMock('get', '/facturas/verificar', ({ headers, query }) => {
    const u = conRol(headers, 'proveedor')
    const folio = normalizarFolio(query.folio)
    if (!folio) return { folio, disponible: false, detail: 'El folio es obligatorio' }
    const registrado = folioRegistrado(folio, query.oc, u.proveedor_id)
    return {
      folio,
      disponible: !registrado,
      detail: registrado ? 'Este folio ya está registrado' : null,
    }
  })

  registrarMock('post', '/citas', ({ headers, body }) => {
    const u = conRol(headers, 'proveedor')
    const prov = db.proveedores.find((x) => x.id === u.proveedor_id)
    if (prov?.estado !== 'activo') {
      throw errorMock(
        409,
        'Tu cuenta de proveedor está suspendida. Comunícate con Oficina',
        'proveedor_suspendido',
      )
    }
    const { oc, anden, dia, inicio } = body ?? {}
    const duracion = Number(body?.duracion_min)
    const folio = normalizarFolio(body?.folio_factura)
    const campo = (c, m) => validacion(m, { [c]: m })
    if (!folio) throw campo('folio_factura', 'El folio es obligatorio')
    if (!folio.startsWith('FAC-')) throw campo('folio_factura', 'El folio debe empezar con FAC-')
    if (folio.length > 30) throw campo('folio_factura', 'El folio admite hasta 30 caracteres')
    if (!ANDENES.includes(anden)) throw campo('anden', 'Elige un andén de recibo, de R1 a R4')
    validarDia(dia)
    const ini = /^\d{2}:\d{2}$/.test(inicio ?? '') ? aMin(inicio) : -1
    if (ini < 480 || ini >= 1080 || ini % 30) {
      throw campo('inicio', 'Elige un horario de 8:00 a 18:00 en bloques de 30 minutos')
    }
    if (!DURACIONES.includes(duracion)) {
      throw campo('duracion_min', 'Elige una duración de 1, 1.5, 2 o 3 h')
    }
    if (ini + duracion > 1080) {
      throw campo('inicio', 'La cita debe terminar a más tardar a las 18:00')
    }
    const orden = db.pedidos.find((o) => o.folio === oc)
    if (!orden || !orden.lineas.some((l) => l.proveedor_id === u.proveedor_id)) {
      throw errorMock(404, 'No encontramos el registro', 'no_encontrado')
    }
    if (db.citas.some((c) => c.oc === oc && c.proveedor_id === u.proveedor_id)) {
      throw errorMock(409, 'Esta orden ya tiene cita', 'cita_existente')
    }
    if (folioRegistrado(folio, oc, u.proveedor_id)) {
      throw errorMock(409, 'Este folio ya está registrado', 'folio_registrado')
    }
    const fin = ini + duracion
    const choca = db.citas.some(
      (c) => c.dia === dia && c.anden === anden && ini < aMin(c.fin) && aMin(c.inicio) < fin,
    )
    if (choca) throw errorMock(409, 'Ese andén ya está ocupado', 'anden_ocupado')
    const cita = {
      id: Math.max(0, ...db.citas.map((c) => c.id)) + 1,
      oc,
      proveedor_id: u.proveedor_id,
      folio_factura: folio,
      anden,
      dia,
      inicio: aHora(ini),
      fin: aHora(fin),
      duracion_min: duracion,
      creado_en: new Date().toISOString(),
    }
    db.citas.push(cita)
    for (const l of orden.lineas.filter((x) => x.proveedor_id === u.proveedor_id)) {
      db.facturas.push({ folio, sku: l.sku })
    }
    if (orden.paso === 'oc_emitida') orden.paso = 'proveedor'
    return respuesta(201, citaCompleta(cita))
  })
}
