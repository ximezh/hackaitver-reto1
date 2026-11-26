/**
 * Pedido de sucursal, órdenes del proveedor y citas por andén (contrato del sprint 2,
 * docs/api/sprint-2.md · BE-20, BE-21 y BE-22). Las respuestas van tal cual el contrato.
 */
import { http } from './http.js'

/** Pasos del seguimiento del pedido (R-14), en orden. */
export const PASOS_PEDIDO = [
  { paso: 'oc_emitida', etiqueta: 'OC emitida' },
  { paso: 'proveedor', etiqueta: 'Proveedor' },
  { paso: 'en_cedis', etiqueta: 'En CEDIS' },
  { paso: 'en_tarima', etiqueta: 'En tarima' },
  { paso: 'en_camino', etiqueta: 'En camino' },
  { paso: 'recibido', etiqueta: 'Recibido' },
]

/** Duraciones permitidas de una cita, en minutos, con la etiqueta del prototipo. */
export const DURACIONES_CITA = [
  { minutos: 60, etiqueta: '1 h' },
  { minutos: 90, etiqueta: '1.5 h' },
  { minutos: 120, etiqueta: '2 h' },
  { minutos: 180, etiqueta: '3 h' },
]

export const ANDENES_RECIBO = ['R1', 'R2', 'R3', 'R4']

export const pedidos = {
  /** Sucursal: `lineas` es `[{ sku, bultos }]`. Responde el pedido con su folio `OC-…`. */
  async crear(lineas) {
    const { data } = await http.post('/pedidos', { lineas })
    return data
  },
  /** Sucursal: sus pedidos, del más nuevo al más antiguo. `enCurso` deja fuera los recibidos. */
  async listar({ enCurso } = {}) {
    const { data } = await http.get('/pedidos', {
      params: enCurso ? { en_curso: true } : undefined,
    })
    return data
  },
  async obtener(folio) {
    const { data } = await http.get(`/pedidos/${encodeURIComponent(folio)}`)
    return data
  },
}

export const ordenesProveedor = {
  /** Proveedor: su parte de cada OC. `sinCita` deja solo las que aún no tienen cita. */
  async listar({ sinCita } = {}) {
    const { data } = await http.get('/proveedor/ordenes', {
      params: sinCita ? { sin_cita: true } : undefined,
    })
    return data
  },
}

export const citas = {
  /** Bloques ocupados de un día (`AAAA-MM-DD`) en los andenes R1 a R4. */
  async disponibilidad(dia) {
    const { data } = await http.get('/citas/disponibilidad', { params: { dia } })
    return data
  },
  /** `{ folio, disponible, detail }`: para marcar el folio en rojo antes de confirmar. */
  async verificarFolio({ folio, oc }) {
    const { data } = await http.get('/facturas/verificar', { params: { folio, oc } })
    return data
  },
  /** `{ oc, folio_factura, anden, dia, inicio, duracion_min }` → la cita creada. */
  async agendar(cita) {
    const { data } = await http.post('/citas', cita)
    return data
  },
}
