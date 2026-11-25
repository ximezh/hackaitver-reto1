/**
 * Cliente HTTP de la app. Las vistas y stores no importan Axios: usan los servicios de `@/api`.
 *
 * - Base `/api`: en desarrollo la reenvía Vite (VITE_API_PROXY) y en producción Nginx.
 * - Agrega el token de sesión a cada petición.
 * - Un 401 avisa a la app para que cierre la sesión.
 * - Todos los errores llegan como `ErrorApi` (`./errores.js`).
 * - Con `VITE_API_MOCK=true` responde con los mocks de `./mocks`, sin red.
 */
import axios from 'axios'

import { normalizarError } from './errores.js'

const opciones = {
  obtenerToken: () => null,
  alNoAutorizado: () => {},
}

/**
 * La app indica cómo leer el token y qué hacer si la sesión ya no es válida.
 * Se llama una vez al iniciar (lo usa el store de sesión).
 */
export function configurarHttp({ obtenerToken, alNoAutorizado } = {}) {
  if (obtenerToken) opciones.obtenerToken = obtenerToken
  if (alNoAutorizado) opciones.alNoAutorizado = alNoAutorizado
}

export function usaMocks() {
  return import.meta.env.VITE_API_MOCK === 'true'
}

let adaptadorMock = null

// La condición va directa sobre `import.meta.env` para que, sin modo mock, el build descarte
// los imports de abajo y los mocks no lleguen a `dist`.
const adaptadorPorDefecto =
  import.meta.env.VITE_API_MOCK === 'true'
    ? async (config) => {
        if (!adaptadorMock) {
          const { crearAdaptadorMock } = await import('./mock.js')
          const { registrarMocks } = await import('./mocks/index.js')
          registrarMocks()
          adaptadorMock = crearAdaptadorMock()
        }
        return adaptadorMock(config)
      }
    : undefined

export function crearHttp({ adapter } = {}) {
  const instancia = axios.create({
    baseURL: '/api',
    timeout: 15000,
    headers: { Accept: 'application/json' },
    adapter: adapter ?? adaptadorPorDefecto,
  })

  instancia.interceptors.request.use((config) => {
    const token = opciones.obtenerToken()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })

  instancia.interceptors.response.use(
    (respuesta) => respuesta,
    (error) => {
      const errorApi = normalizarError(error)
      if (errorApi.estado === 401) opciones.alNoAutorizado(errorApi)
      return Promise.reject(errorApi)
    },
  )

  return instancia
}

export const http = crearHttp()
