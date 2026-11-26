import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  cambiarContrasena,
  cerrarSesion,
  haySesion,
  iniciarSesion,
  obtenerPerfil,
} from '../auth.js'
import { configurarHttp, http } from '../http.js'
import { crearAdaptadorMock, limpiarMocks } from '../mock.js'
import { CONTRASENA_DEMO, reiniciarDatos } from '../mocks/datos.js'
import { registrarMocks } from '../mocks/index.js'
import { obtenerToken, sesionRecordada } from '../sesion.js'
import { usarAlmacenesEnMemoria } from './almacen.js'

const adaptadorOriginal = http.defaults.adapter

beforeEach(() => {
  reiniciarDatos()
  registrarMocks()
  http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
  usarAlmacenesEnMemoria()
})

afterEach(() => {
  limpiarMocks()
  http.defaults.adapter = adaptadorOriginal
  vi.unstubAllGlobals()
  configurarHttp({ alNoAutorizado: () => {}, alCambioContrasena: () => {} })
})

const entrar = (usuario, canal, extra = {}) =>
  iniciarSesion({ usuario, contrasena: CONTRASENA_DEMO, canal, ...extra })

describe('iniciarSesion', () => {
  it.each([
    ['caseta.jlopez', 'android', 'caseta'],
    ['desem.mruiz', 'android', 'desembarque'],
    ['embar.acruz', 'android', 'embarque'],
    ['suc07', 'web', 'sucursal'],
    ['pgolfo', 'web', 'proveedor'],
    ['admin.cedis', 'web', 'oficina'],
  ])('%s entra por %s con rol %s', async (usuario, canal, rol) => {
    const sesion = await entrar(usuario, canal)
    expect(sesion.usuario.rol).toBe(rol)
    expect(sesion.expira_en).toBe(43200)
    expect(haySesion()).toBe(true)
  })

  it('acepta mayúsculas y espacios en el usuario', async () => {
    const sesion = await entrar('  ADMIN.cedis ', 'web')
    expect(sesion.usuario.usuario).toBe('admin.cedis')
  })

  it('guarda el token según «Recordarme»', async () => {
    await entrar('suc07', 'web', { recordar: true })
    expect(sesionRecordada()).toBe(true)
    await entrar('suc07', 'web', { recordar: false })
    expect(sesionRecordada()).toBe(false)
    expect(sessionStorage.getItem('cedis.token')).toBeTruthy()
  })

  it('una contraseña incorrecta no cierra la sesión', async () => {
    const alNoAutorizado = vi.fn()
    configurarHttp({ alNoAutorizado })
    await expect(
      iniciarSesion({ usuario: 'suc07', contrasena: 'mala', canal: 'web' }),
    ).rejects.toMatchObject({ estado: 401, codigo: 'credenciales_invalidas' })
    expect(alNoAutorizado).not.toHaveBeenCalled()
  })

  it('rechaza el canal equivocado con el texto del contrato', async () => {
    await expect(entrar('caseta.jlopez', 'web')).rejects.toMatchObject({
      codigo: 'canal_incorrecto',
      message: 'Este usuario entra desde el teléfono',
    })
    await expect(entrar('suc07', 'android')).rejects.toMatchObject({
      codigo: 'canal_incorrecto',
      message: 'Este usuario entra desde la web',
    })
  })

  it('valida campos vacíos con campos por nombre', async () => {
    await expect(
      iniciarSesion({ usuario: '', contrasena: '', canal: 'web' }),
    ).rejects.toMatchObject({ codigo: 'validacion', campos: { usuario: expect.any(String) } })
  })
})

describe('perfil y sesión', () => {
  it('obtiene el perfil del usuario con sesión', async () => {
    await entrar('pgolfo', 'web')
    const perfil = await obtenerPerfil()
    expect(perfil).toMatchObject({ usuario: 'pgolfo', rol: 'proveedor', proveedor: { id: 1 } })
  })

  it('sin token avisa a la app y no deja sesión', async () => {
    const alNoAutorizado = vi.fn()
    configurarHttp({ alNoAutorizado })
    await expect(obtenerPerfil()).rejects.toMatchObject({ codigo: 'no_autenticado' })
    expect(alNoAutorizado).toHaveBeenCalledOnce()
    expect(haySesion()).toBe(false)
  })

  it('cerrarSesion borra el token', async () => {
    await entrar('suc07', 'web', { recordar: true })
    cerrarSesion()
    expect(obtenerToken()).toBeNull()
  })
})

describe('contraseña temporal (R-17)', () => {
  it('el login avisa que la contraseña es temporal y el perfil sí responde', async () => {
    const sesion = await iniciarSesion({
      usuario: 'caseta.rgomez',
      contrasena: 'Tmp-7Kq2-xW9p',
      canal: 'android',
    })
    expect(sesion.contrasena_temporal).toBe(true)
    await expect(obtenerPerfil()).resolves.toMatchObject({ contrasena_temporal: true })
  })

  it('cambia la contraseña y reemplaza el token', async () => {
    await iniciarSesion({
      usuario: 'caseta.rgomez',
      contrasena: 'Tmp-7Kq2-xW9p',
      canal: 'android',
      recordar: true,
    })
    const anterior = obtenerToken()
    const sesion = await cambiarContrasena({ actual: 'Tmp-7Kq2-xW9p', nueva: 'MiClaveSegura26' })
    expect(sesion.contrasena_temporal).toBe(false)
    expect(obtenerToken()).not.toBe(anterior)
    expect(sesionRecordada()).toBe(true)
    await expect(
      iniciarSesion({ usuario: 'caseta.rgomez', contrasena: 'MiClaveSegura26', canal: 'android' }),
    ).resolves.toMatchObject({ contrasena_temporal: false })
  })

  it('valida la contraseña actual y la nueva', async () => {
    await iniciarSesion({ usuario: 'caseta.rgomez', contrasena: 'Tmp-7Kq2-xW9p', canal: 'android' })
    await expect(
      cambiarContrasena({ actual: 'otra', nueva: 'MiClaveSegura26' }),
    ).rejects.toMatchObject({ estado: 400, codigo: 'contrasena_actual_incorrecta' })
    await expect(
      cambiarContrasena({ actual: 'Tmp-7Kq2-xW9p', nueva: 'corta' }),
    ).rejects.toMatchObject({
      codigo: 'validacion',
      campos: { nueva: 'La contraseña debe tener al menos 8 caracteres' },
    })
  })
})

describe('errores del back con campos', () => {
  it('respeta campos y avisa del cambio de contraseña requerido', async () => {
    const alCambioContrasena = vi.fn()
    configurarHttp({ alCambioContrasena })
    const { registrarMock, errorMock } = await import('../mock.js')
    registrarMock('get', '/productos', () => {
      throw errorMock(403, 'Cambia tu contraseña para continuar', 'cambio_contrasena_requerido')
    })
    await expect(http.get('/productos')).rejects.toMatchObject({
      codigo: 'cambio_contrasena_requerido',
    })
    expect(alCambioContrasena).toHaveBeenCalledOnce()
  })
})
