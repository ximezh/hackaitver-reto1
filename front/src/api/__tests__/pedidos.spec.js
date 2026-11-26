import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { iniciarSesion } from '../auth.js'
import { http } from '../http.js'
import { crearAdaptadorMock, limpiarMocks } from '../mock.js'
import { CONTRASENA_DEMO, reiniciarDatos } from '../mocks/datos.js'
import { proximoHabil, hoy } from '../mocks/fechas.js'
import { registrarMocks } from '../mocks/index.js'
import { citas, ordenesProveedor, pedidos } from '../pedidos.js'
import { usarAlmacenesEnMemoria } from './almacen.js'

const adaptadorOriginal = http.defaults.adapter
const entrar = (usuario) => iniciarSesion({ usuario, contrasena: CONTRASENA_DEMO, canal: 'web' })

beforeEach(() => {
  usarAlmacenesEnMemoria()
  reiniciarDatos()
  registrarMocks()
  http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
})

afterEach(() => {
  limpiarMocks()
  http.defaults.adapter = adaptadorOriginal
  vi.unstubAllGlobals()
})

describe('demo: sucursal pide y proveedor agenda', () => {
  it('la sucursal crea un pedido con partes por proveedor', async () => {
    await entrar('suc07')
    const p = await pedidos.crear([
      { sku: 'PAP-0100', bultos: 4 },
      { sku: 'LAP-0012', bultos: 2 },
      { sku: 'pap-0100', bultos: 1 },
    ])
    expect(p).toMatchObject({ folio: 'OC-26-1211', paso: 'oc_emitida', paso_indice: 0, bultos: 7 })
    expect(p.partes.map((x) => x.proveedor.nombre)).toEqual([
      'Papelera del Golfo',
      'Distribuidora Atlas',
    ])
    expect((await pedidos.listar({ enCurso: true })).items[0].folio).toBe('OC-26-1211')
  })

  it('valida el pedido con los textos del contrato', async () => {
    await entrar('suc07')
    await expect(pedidos.crear([])).rejects.toMatchObject({ message: 'Agrega productos' })
    await expect(pedidos.crear([{ sku: 'XXX-0001', bultos: 1 }])).rejects.toMatchObject({
      campos: { lineas: 'El producto XXX-0001 no está disponible' },
    })
  })

  it('el proveedor ve su parte, agenda y no deja empalmar ni repetir folio', async () => {
    await entrar('pgolfo')
    const { items } = await ordenesProveedor.listar({ sinCita: true })
    expect(items[0]).toMatchObject({ oc: 'OC-26-1182', bultos: 24, cita: null })
    const dia = proximoHabil(hoy())
    const disp = await citas.disponibilidad(dia)
    expect(disp.andenes[0].ocupados[0]).toMatchObject({
      inicio: '08:00',
      etiqueta: 'Distribuidora Atlas',
    })
    expect(await citas.verificarFolio({ folio: 'fac-a-20391', oc: 'OC-26-1182' })).toMatchObject({
      disponible: false,
      detail: 'Este folio ya está registrado',
    })
    const base = { oc: 'OC-26-1182', folio_factura: 'FAC-A-20418', dia, duracion_min: 60 }
    await expect(citas.agendar({ ...base, anden: 'R1', inicio: '08:30' })).rejects.toMatchObject({
      codigo: 'anden_ocupado',
    })
    const cita = await citas.agendar({ ...base, anden: 'R2', inicio: '11:00' })
    expect(cita).toMatchObject({ fin: '12:00', bultos: 24, estado: 'programada' })
    await expect(citas.agendar({ ...base, anden: 'R3', inicio: '11:00' })).rejects.toMatchObject({
      codigo: 'cita_existente',
    })
    await entrar('suc07')
    const oc = await pedidos.obtener('OC-26-1182')
    expect(oc).toMatchObject({ paso: 'proveedor', partes: [{ cita: { anden: 'R2' } }] })
  })

  it('aplica las reglas de horario y día', async () => {
    await entrar('pgolfo')
    const dia = proximoHabil(hoy())
    const base = { oc: 'OC-26-1182', folio_factura: 'FAC-A-1', anden: 'R1', dia }
    await expect(
      citas.agendar({ ...base, inicio: '17:30', duracion_min: 60 }),
    ).rejects.toMatchObject({
      message: 'La cita debe terminar a más tardar a las 18:00',
    })
    await expect(
      citas.agendar({ ...base, inicio: '09:15', duracion_min: 60 }),
    ).rejects.toMatchObject({
      message: 'Elige un horario de 8:00 a 18:00 en bloques de 30 minutos',
    })
    await expect(citas.disponibilidad('2020-01-01')).rejects.toMatchObject({
      message: 'Ese día ya pasó',
    })
  })
})
