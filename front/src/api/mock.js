/**
 * Modo mock: responde las peticiones sin red, con los datos del prototipo.
 * Cada servicio registra sus rutas en `api/mocks/`. Las rutas usan parámetros con dos puntos:
 * `registrarMock('get', '/citas/:folio', ({ params }) => ...)`.
 *
 * Un manejador devuelve los datos (estado 200), `respuesta(estado, datos)` para otro estado,
 * o lanza `errorMock(estado, detail, code)` para simular un error del back.
 */
const rutas = []

export function registrarMock(metodo, patron, manejador) {
  const nombres = []
  const expresion = patron.replace(/:([a-zA-Z_]+)/g, (_, nombre) => {
    nombres.push(nombre)
    return '([^/]+)'
  })
  rutas.push({
    metodo: metodo.toLowerCase(),
    regex: new RegExp(`^${expresion}/?$`),
    nombres,
    manejador,
  })
}

export function limpiarMocks() {
  rutas.length = 0
}

const RESPUESTA = Symbol('respuesta')

export function respuesta(estado, datos) {
  return { [RESPUESTA]: true, estado, datos }
}

export function errorMock(estado, detail, code) {
  const error = new Error(detail)
  error.mock = { estado, datos: { detail, code } }
  return error
}

function buscar(metodo, ruta) {
  for (const r of rutas) {
    if (r.metodo !== metodo) continue
    const m = ruta.match(r.regex)
    if (m) {
      const params = Object.fromEntries(r.nombres.map((n, i) => [n, decodeURIComponent(m[i + 1])]))
      return { manejador: r.manejador, params }
    }
  }
  return null
}

function cuerpo(data) {
  if (typeof data !== 'string') return data
  try {
    return JSON.parse(data)
  } catch {
    return data
  }
}

function rechazar(config, estado, datos) {
  const error = new Error(datos?.detail ?? `Error ${estado}`)
  error.config = config
  error.response = { status: estado, data: datos, headers: {}, config }
  return Promise.reject(error)
}

/** Adaptador de Axios que responde con los mocks registrados. */
export function crearAdaptadorMock({ latencia = 150 } = {}) {
  return async function adaptadorMock(config) {
    const metodo = (config.method ?? 'get').toLowerCase()
    const ruta = new URL(config.url, 'http://mock').pathname
    const encontrado = buscar(metodo, ruta)

    if (latencia) await new Promise((resolver) => setTimeout(resolver, latencia))

    if (!encontrado) {
      return rechazar(config, 404, {
        detail: `No hay mock para ${metodo.toUpperCase()} ${ruta}`,
        code: 'mock_no_definido',
      })
    }

    try {
      const salida = await encontrado.manejador({
        params: encontrado.params,
        query: config.params ?? {},
        body: cuerpo(config.data),
        headers: config.headers ?? {},
      })
      const { estado, datos } = salida?.[RESPUESTA] ? salida : { estado: 200, datos: salida }
      if (estado >= 400) return rechazar(config, estado, datos)
      return { data: datos, status: estado, statusText: 'OK', headers: {}, config }
    } catch (error) {
      if (error.mock) return rechazar(config, error.mock.estado, error.mock.datos)
      throw error
    }
  }
}
