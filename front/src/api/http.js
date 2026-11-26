/**
 * Cliente HTTP de la app. Las vistas y stores no importan Axios: usan los servicios de `@/api`.
 *
 * - Base `/api`: en desarrollo la reenvía Vite (VITE_API_PROXY) y en producción Nginx.
 * - Agrega el token de sesión guardado (`./sesion.js`) a cada petición.
 * - Sesión vencida o sin token (`401 no_autenticado` · `token_expirado`): avisa a la app para
 *   que regrese al login. Un `401 credenciales_invalidas` del login no cierra nada.
 * - Contraseña temporal (`403 cambio_contrasena_requerido`): avisa a la app para que lleve al
 *   cambio de contraseña (R-17).
 * - Todos los errores llegan como `ErrorApi` (`./errores.js`).
 * - Con `VITE_API_MOCK=true` responde con los mocks de `./mocks`, sin red.
 */
import axios from 'axios'

import { normalizarError } from './errores.js'
import { borrarToken, obtenerToken } from './sesion.js'

const SESION_INVALIDA = new Set(['no_autenticado', 'token_expirado'])

const opciones = {
  obtenerToken,
  alNoAutorizado: () => {},
  alCambioContrasena: () => {},
}

/**
 * La app indica qué hacer cuando la sesión deja de servir o la contraseña es temporal.
 * Se llama una vez al iniciar (lo usa el store de sesión). `obtenerToken` solo se cambia en pruebas.
 */
export function configurarHttp({ obtenerToken, alNoAutorizado, alCambioContrasena } = {}) {
  if (obtenerToken) opciones.obtenerToken = obtenerToken
  if (alNoAutorizado) opciones.alNoAutorizado = alNoAutorizado
  if (alCambioContrasena) opciones.alCambioContrasena = alCambioContrasena
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
      if (errorApi.estado === 401 && SESION_INVALIDA.has(errorApi.codigo)) {
        borrarToken()
        opciones.alNoAutorizado(errorApi)
      } else if (errorApi.codigo === 'cambio_contrasena_requerido') {
        opciones.alCambioContrasena(errorApi)
      }
      return Promise.reject(errorApi)
    },
  )

  return instancia
}

export const http = crearHttp()
