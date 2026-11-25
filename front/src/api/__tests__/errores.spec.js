import { describe, expect, it } from 'vitest'

import { ErrorApi, normalizarError } from '../errores.js'

describe('normalizarError', () => {
  it('usa detail y code del back', () => {
    const e = normalizarError({
      response: {
        status: 409,
        data: { detail: 'Ese andén ya está ocupado', code: 'cita_empalmada' },
      },
    })
    expect(e).toBeInstanceOf(ErrorApi)
    expect(e).toMatchObject({
      estado: 409,
      codigo: 'cita_empalmada',
      message: 'Ese andén ya está ocupado',
    })
  })

  it('junta los errores de validación de FastAPI por campo', () => {
    const e = normalizarError({
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ['body', 'folio'], msg: 'El folio es obligatorio' },
            { loc: ['body', 'duracion'], msg: 'Duración no válida' },
          ],
        },
      },
    })
    expect(e.codigo).toBe('validacion')
    expect(e.campos).toEqual({ folio: 'El folio es obligatorio', duracion: 'Duración no válida' })
    expect(e.message).toBe('El folio es obligatorio. Duración no válida')
  })

  it('distingue sin conexión y tiempo agotado', () => {
    expect(normalizarError(new Error('Network Error'))).toMatchObject({
      estado: 0,
      codigo: 'sin_conexion',
    })
    expect(normalizarError({ code: 'ECONNABORTED' })).toMatchObject({
      estado: 0,
      codigo: 'tiempo_agotado',
    })
  })

  it('da un mensaje genérico a un 500 sin cuerpo', () => {
    const e = normalizarError({ response: { status: 500, data: '' } })
    expect(e).toMatchObject({ estado: 500, codigo: 'error_servidor' })
    expect(e.message).toBe('Ocurrió un error en el servidor')
  })
})
