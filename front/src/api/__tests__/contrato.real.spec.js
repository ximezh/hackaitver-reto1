// @vitest-environment node
/**
 * Conexión de punta a punta (DO-14): los servicios de `@/api` contra un back real, sin mocks.
 * Se omite salvo que se indique la URL del back o del front que lo reenvía:
 *
 *   API_REAL=http://localhost:8000 npx vitest run src/api/__tests__/contrato.real.spec.js
 *   API_REAL=https://staging.<dominio> npx vitest run src/api/__tests__/contrato.real.spec.js
 *
 * Usa los usuarios de las semillas del back (BE-03): contraseña `cedis2026`.
 */
import process from 'node:process'

import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'

import { cerrarSesion, iniciarSesion, obtenerPerfil } from '../auth.js'
import { productos, proveedores, sucursales, usuarios } from '../catalogos.js'
import { http } from '../http.js'
import { obtenerSalud } from '../salud.js'
import { usarAlmacenesEnMemoria } from './almacen.js'

const API_REAL = process.env.API_REAL
const CONTRASENA = process.env.CONTRASENA_DEMO ?? 'cedis2026'

describe.skipIf(!API_REAL)(`contrato del sprint 1 contra ${API_REAL}`, () => {
  const baseOriginal = http.defaults.baseURL

  beforeAll(() => {
    usarAlmacenesEnMemoria()
    http.defaults.baseURL = `${API_REAL.replace(/\/$/, '')}/api`
  })

  afterAll(() => {
    http.defaults.baseURL = baseOriginal
    vi.unstubAllGlobals()
  })

  it('la API y PostgreSQL responden', async () => {
    expect(await obtenerSalud()).toEqual({ status: 'ok', database: 'ok' })
  })

  it('rechaza credenciales inválidas con el código del contrato', async () => {
    await expect(
      iniciarSesion({ usuario: 'admin.cedis', contrasena: 'incorrecta', canal: 'web' }),
    ).rejects.toMatchObject({ estado: 401, codigo: 'credenciales_invalidas' })
  })

  it('rechaza el canal equivocado', async () => {
    await expect(
      iniciarSesion({ usuario: 'caseta.jlopez', contrasena: CONTRASENA, canal: 'web' }),
    ).rejects.toMatchObject({ estado: 403, codigo: 'canal_incorrecto' })
  })

  it('Oficina inicia sesión y lee su perfil', async () => {
    const sesion = await iniciarSesion({
      usuario: 'admin.cedis',
      contrasena: CONTRASENA,
      canal: 'web',
    })
    expect(sesion).toMatchObject({
      token_type: 'bearer',
      usuario: { rol: 'oficina', canal: 'web' },
    })
    expect(await obtenerPerfil()).toMatchObject({ usuario: 'admin.cedis', rol: 'oficina' })
  })

  it('Oficina lista los cuatro catálogos con la forma { items, total }', async () => {
    for (const catalogo of [productos, proveedores, sucursales, usuarios]) {
      const { items, total } = await catalogo.listar()
      expect(Array.isArray(items)).toBe(true)
      expect(total).toBe(items.length)
    }
    expect((await productos.listar({ q: 'RES-0500' })).items[0]).toMatchObject({ sku: 'RES-0500' })
  })

  it('un rol sin permiso recibe 403 sin_permiso', async () => {
    await iniciarSesion({ usuario: 'suc07', contrasena: CONTRASENA, canal: 'web' })
    await expect(productos.listar()).rejects.toMatchObject({ estado: 403, codigo: 'sin_permiso' })
  })

  it('sin sesión responde 401 no_autenticado', async () => {
    cerrarSesion()
    await expect(obtenerPerfil()).rejects.toMatchObject({ estado: 401, codigo: 'no_autenticado' })
  })
})
