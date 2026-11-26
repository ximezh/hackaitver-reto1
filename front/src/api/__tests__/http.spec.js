import { afterEach, describe, expect, it, vi } from 'vitest'

import { ErrorApi } from '../errores.js'
import { configurarHttp, crearHttp } from '../http.js'
import { crearAdaptadorMock, errorMock, limpiarMocks, registrarMock, respuesta } from '../mock.js'
import { registrarMocks } from '../mocks/index.js'

function clienteMock() {
  return crearHttp({ adapter: crearAdaptadorMock({ latencia: 0 }) })
}

afterEach(() => {
  limpiarMocks()
  configurarHttp({ obtenerToken: () => null, alNoAutorizado: () => {} })
})

describe('cliente http', () => {
  it('usa la base /api y agrega el token de sesión', async () => {
    let visto
    const http = crearHttp({
      adapter: async (config) => {
        visto = config
        return { data: {}, status: 200, statusText: 'OK', headers: {}, config }
      },
    })
    configurarHttp({ obtenerToken: () => 'abc' })
    await http.get('/health')
    expect(visto.baseURL).toBe('/api')
    expect(visto.headers.Authorization).toBe('Bearer abc')
  })

  it('no agrega Authorization sin token', async () => {
    let visto
    const http = crearHttp({
      adapter: async (config) => {
        visto = config
        return { data: {}, status: 200, statusText: 'OK', headers: {}, config }
      },
    })
    await http.get('/health')
    expect(visto.headers.Authorization).toBeUndefined()
  })

  it('avisa a la app con un 401 y rechaza con ErrorApi', async () => {
    const alNoAutorizado = vi.fn()
    configurarHttp({ alNoAutorizado })
    registrarMock('get', '/auth/me', () =>
      respuesta(401, {
        detail: 'Tu sesión terminó. Inicia sesión de nuevo',
        code: 'token_expirado',
      }),
    )
    await expect(clienteMock().get('/auth/me')).rejects.toBeInstanceOf(ErrorApi)
    expect(alNoAutorizado).toHaveBeenCalledOnce()
  })
})

describe('modo mock', () => {
  it('responde con parámetros de ruta, query y cuerpo', async () => {
    registrarMock('post', '/citas/:anden', ({ params, query, body }) => ({ params, query, body }))
    const { data } = await clienteMock().post('/citas/R2', { duracion: 2 }, { params: { dia: 1 } })
    expect(data).toEqual({ params: { anden: 'R2' }, query: { dia: 1 }, body: { duracion: 2 } })
  })

  it('simula errores del back', async () => {
    registrarMock('post', '/citas', () => {
      throw errorMock(409, 'Ese andén ya está ocupado', 'cita_empalmada')
    })
    await expect(clienteMock().post('/citas', {})).rejects.toMatchObject({
      estado: 409,
      codigo: 'cita_empalmada',
      message: 'Ese andén ya está ocupado',
    })
  })

  it('avisa cuando una ruta no tiene mock', async () => {
    await expect(clienteMock().get('/no-existe')).rejects.toMatchObject({
      estado: 404,
      codigo: 'mock_no_definido',
    })
  })

  it('el mock de salud responde como el back', async () => {
    registrarMocks()
    const { data } = await clienteMock().get('/health')
    expect(data).toEqual({ status: 'ok', database: 'ok' })
  })
})
