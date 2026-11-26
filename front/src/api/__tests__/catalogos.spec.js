import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { iniciarSesion } from '../auth.js'
import { productos, proveedores, sucursales, usuarios } from '../catalogos.js'
import { http } from '../http.js'
import { obtenerIndicadoresOficina } from '../indicadores.js'
import { crearAdaptadorMock, limpiarMocks } from '../mock.js'
import { CONTRASENA_DEMO, reiniciarDatos } from '../mocks/datos.js'
import { registrarMocks } from '../mocks/index.js'
import { usarAlmacenesEnMemoria } from './almacen.js'

const adaptadorOriginal = http.defaults.adapter

beforeEach(async () => {
  usarAlmacenesEnMemoria()
  reiniciarDatos()
  registrarMocks()
  http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
  await iniciarSesion({ usuario: 'admin.cedis', contrasena: CONTRASENA_DEMO, canal: 'web' })
})

afterEach(() => {
  limpiarMocks()
  http.defaults.adapter = adaptadorOriginal
  vi.unstubAllGlobals()
})

describe('permisos', () => {
  it('solo Oficina usa los catálogos', async () => {
    await iniciarSesion({ usuario: 'suc07', contrasena: CONTRASENA_DEMO, canal: 'web' })
    await expect(productos.listar()).rejects.toMatchObject({ estado: 403, codigo: 'sin_permiso' })
  })

  it('con contraseña temporal pide cambiarla', async () => {
    await iniciarSesion({ usuario: 'caseta.rgomez', contrasena: 'Tmp-7Kq2-xW9p', canal: 'android' })
    await expect(productos.listar()).rejects.toMatchObject({
      codigo: 'cambio_contrasena_requerido',
    })
  })
})

describe('productos', () => {
  it('lista los 7 del prototipo con su proveedor y busca sin acentos', async () => {
    const { items, total } = await productos.listar()
    expect(total).toBe(7)
    expect(items[0]).toMatchObject({ sku: 'RES-0500', proveedor: { nombre: 'Papelera del Golfo' } })
    expect((await productos.listar({ q: 'lapiz' })).items.map((p) => p.sku)).toEqual(['LAP-0012'])
  })

  it('crea con valores por defecto y el SKU en mayúsculas', async () => {
    const nuevo = await productos.crear({
      sku: 'bor-0010',
      nombre: 'Borrador blanco, caja 10',
      piezas_por_bulto: 30,
      kg: 3.2,
      m3: 0.006,
    })
    expect(nuevo).toMatchObject({
      id: 8,
      sku: 'BOR-0010',
      ilustracion: 'bulto',
      unidad: 'piezas',
      estado: 'activo',
    })
  })

  it('valida obligatorios, positivos y SKU duplicado', async () => {
    await expect(
      productos.crear({ nombre: 'x', piezas_por_bulto: 0, kg: 1, m3: 1 }),
    ).rejects.toMatchObject({
      codigo: 'validacion',
      message: 'Completa SKU',
      campos: {
        sku: 'Completa SKU',
        piezas_por_bulto: 'Las piezas por bulto deben ser mayores a 0',
      },
    })
    await expect(
      productos.crear({ sku: 'res-0500', nombre: 'x', piezas_por_bulto: 1, kg: 1, m3: 1 }),
    ).rejects.toMatchObject({ estado: 409, codigo: 'sku_duplicado' })
  })

  it('edita solo los campos enviados y elimina', async () => {
    expect(await productos.editar(7, { kg: 1.25 })).toMatchObject({ sku: 'CLI-0100', kg: 1.3 })
    expect(await productos.eliminar(7)).toEqual({ resultado: 'eliminado' })
    await expect(productos.obtener(7)).rejects.toMatchObject({
      estado: 404,
      codigo: 'no_encontrado',
    })
  })
})

describe('proveedores', () => {
  it('valida el RFC y lo guarda en mayúsculas', async () => {
    await expect(proveedores.crear({ rfc: 'malo', nombre: 'X' })).rejects.toMatchObject({
      message: 'El RFC no es válido',
    })
    expect(await proveedores.crear({ rfc: 'abc010101xy9', nombre: 'Nuevo' })).toMatchObject({
      rfc: 'ABC010101XY9',
    })
    await expect(proveedores.crear({ rfc: 'PGO090312AB1', nombre: 'X' })).rejects.toMatchObject({
      codigo: 'rfc_duplicado',
    })
  })

  it('un proveedor con productos se desactiva en lugar de borrarse', async () => {
    const r = await proveedores.eliminar(1)
    expect(r).toMatchObject({ resultado: 'desactivado', registro: { id: 1, estado: 'inactivo' } })
    expect(await proveedores.eliminar(4)).toEqual({ resultado: 'eliminado' })
  })

  it('reactiva un proveedor suspendido', async () => {
    expect(await proveedores.editar(4, { estado: 'activo' })).toMatchObject({ estado: 'activo' })
  })
})

describe('sucursales', () => {
  it('asigna el rack de la clave y no deja cambiar la clave', async () => {
    const s = await sucursales.crear({
      clave: '09',
      nombre: 'Suc. 09 Veracruz Puerto',
      ciudad: 'Veracruz',
    })
    expect(s).toMatchObject({ id: 7, rack: 'R-09' })
    await expect(sucursales.editar(s.id, { clave: '10' })).rejects.toMatchObject({
      message: 'La clave no se puede cambiar',
    })
    await expect(sucursales.crear({ clave: '33', nombre: 'x', ciudad: 'x' })).rejects.toMatchObject(
      {
        message: 'La clave debe ser de 01 a 32',
      },
    )
    await expect(sucursales.crear({ clave: '07', nombre: 'x', ciudad: 'x' })).rejects.toMatchObject(
      {
        codigo: 'clave_duplicada',
      },
    )
  })

  it('una sucursal con usuarios se desactiva', async () => {
    expect((await sucursales.eliminar(3)).resultado).toBe('desactivado')
    expect((await sucursales.eliminar(1)).resultado).toBe('eliminado')
  })
})

describe('usuarios', () => {
  it('crea con contraseña temporal visible una vez y el canal del rol', async () => {
    const u = await usuarios.crear({ usuario: 'caseta.rgomez2', nombre: 'Rosa', rol: 'caseta' })
    expect(u).toMatchObject({ canal: 'android', contrasena_temporal: true })
    expect(u.contrasena_generada).toMatch(/^Tmp-/)
    expect((await usuarios.obtener(u.id)).contrasena_generada).toBeUndefined()
    await expect(
      iniciarSesion({
        usuario: 'caseta.rgomez2',
        contrasena: u.contrasena_generada,
        canal: 'android',
      }),
    ).resolves.toMatchObject({ contrasena_temporal: true })
  })

  it('aplica los prefijos de Android (R-01)', async () => {
    await expect(
      usuarios.crear({ usuario: 'rgomez', nombre: 'R', rol: 'caseta' }),
    ).rejects.toMatchObject({
      message: 'El usuario de Caseta debe empezar con caseta.',
    })
    await expect(
      usuarios.crear({ usuario: 'desem.x', nombre: 'R', rol: 'oficina' }),
    ).rejects.toMatchObject({
      message: 'Ese prefijo es solo para usuarios de Android',
    })
  })

  it('pide la sucursal o el proveedor según el rol', async () => {
    await expect(
      usuarios.crear({ usuario: 'suc04', nombre: 'S', rol: 'sucursal' }),
    ).rejects.toMatchObject({
      campos: { sucursal_id: 'Elige la sucursal' },
    })
    expect(
      await usuarios.crear({
        usuario: 'suc04',
        nombre: 'Suc. 04',
        rol: 'sucursal',
        sucursal_id: 2,
      }),
    ).toMatchObject({ sucursal: { id: 2, nombre: 'Suc. 04 Xalapa' } })
  })

  it('no permite duplicados ni eliminarse a sí mismo', async () => {
    await expect(
      usuarios.crear({ usuario: 'SUC07', nombre: 'x', rol: 'sucursal', sucursal_id: 3 }),
    ).rejects.toMatchObject({
      codigo: 'usuario_duplicado',
    })
    await expect(usuarios.eliminar(6)).rejects.toMatchObject({ codigo: 'no_puedes_eliminarte' })
  })

  it('restablece la contraseña con una temporal nueva', async () => {
    const r = await usuarios.restablecer(4)
    expect(r).toMatchObject({ usuario: 'suc07', contrasena_temporal: true })
    await expect(
      iniciarSesion({ usuario: 'suc07', contrasena: CONTRASENA_DEMO, canal: 'web' }),
    ).rejects.toMatchObject({ codigo: 'credenciales_invalidas' })
  })
})

describe('indicadores de Oficina', () => {
  it('usa los valores del prototipo hasta BE-44', async () => {
    const i = await obtenerIndicadoresOficina()
    expect(i.camiones_recibidos).toEqual({ valor: 23, total: 35 })
    expect(i.racks).toHaveLength(32)
    const ocupadas = i.racks.reduce((a, r) => a + r.ocupadas, 0)
    expect(Math.round((ocupadas / (32 * 32)) * 100)).toBe(78)
  })
})
