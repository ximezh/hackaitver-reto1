import { hoy, proximoHabil, sumarDias } from './fechas.js'

/** Datos iniciales: los del prototipo, con fechas relativas a hoy. */
export function crearDatosPedidos() {
  const manana = proximoHabil(hoy())
  return {
    pedidos: [
      {
        folio: 'OC-26-1182',
        sucursal_id: 3,
        creado_en: `${sumarDias(hoy(), -4)}T09:40:00-06:00`,
        paso: 'oc_emitida',
        llega_estimado: sumarDias(hoy(), 3),
        lineas: [
          { sku: 'PAP-0100', bultos: 14, proveedor_id: 1 },
          { sku: 'RES-0500', bultos: 10, proveedor_id: 1 },
        ],
      },
      {
        folio: 'OC-26-1170',
        sucursal_id: 2,
        creado_en: `${sumarDias(hoy(), -6)}T11:00:00-06:00`,
        paso: 'proveedor',
        llega_estimado: sumarDias(hoy(), 2),
        lineas: [{ sku: 'LAP-0012', bultos: 8, proveedor_id: 2 }],
      },
    ],
    citas: [
      {
        id: 1,
        oc: 'OC-26-1170',
        proveedor_id: 2,
        folio_factura: 'FAC-B-10002',
        anden: 'R1',
        dia: manana,
        inicio: '08:00',
        fin: '09:00',
        duracion_min: 60,
        creado_en: `${sumarDias(hoy(), -1)}T10:00:00-06:00`,
      },
    ],
    facturas: [
      { folio: 'FAC-B-10002', sku: 'LAP-0012' },
      { folio: 'FAC-A-20391', sku: 'PAP-0100' },
    ],
    siguienteOc: 1211,
  }
}
