/**
 * Sesión: login, perfil y cambio de contraseña (contrato del sprint 1, docs/api/sprint-1.md).
 * Las respuestas se devuelven tal cual las define el contrato.
 */
import { http } from './http.js'
import { borrarToken, guardarToken, obtenerToken, sesionRecordada } from './sesion.js'

/**
 * Inicia sesión y guarda el token.
 * @param {{ usuario: string, contrasena: string, canal: 'web' | 'android', recordar?: boolean }} datos
 * @returns {Promise<{ usuario: object, contrasena_temporal: boolean, expira_en: number }>}
 */
export async function iniciarSesion({ usuario, contrasena, canal, recordar = false }) {
  const { data } = await http.post('/auth/login', { usuario, contrasena, canal })
  guardarToken(data.access_token, { recordar })
  return data
}

/** Perfil del usuario con sesión: id, usuario, nombre, rol, canal, sucursal y proveedor. */
export async function obtenerPerfil() {
  const { data } = await http.get('/auth/me')
  return data
}

/**
 * Cambia la contraseña y reemplaza el token por el nuevo, ya sin contraseña temporal.
 * Conserva la forma de guardado («Recordarme») de la sesión actual.
 */
export async function cambiarContrasena({ actual, nueva }) {
  const { data } = await http.post('/auth/contrasena', { actual, nueva })
  guardarToken(data.access_token, { recordar: sesionRecordada() })
  return data
}

/** No hay ruta de cierre de sesión: el front borra el token. */
export function cerrarSesion() {
  borrarToken()
}

export function haySesion() {
  return Boolean(obtenerToken())
}
