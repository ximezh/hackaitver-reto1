/**
 * Guarda el token de sesión.
 * - Con «Recordarme»: `localStorage`, sobrevive a cerrar el navegador.
 * - Sin «Recordarme»: `sessionStorage`, se borra al cerrar la pestaña.
 * El token dura 12 horas en el back; «Recordarme» no cambia esa duración (contrato del sprint 1).
 */
const CLAVE = 'cedis.token'

function almacenes() {
  return [globalThis.localStorage, globalThis.sessionStorage].filter(Boolean)
}

export function guardarToken(token, { recordar = false } = {}) {
  borrarToken()
  const destino = recordar ? globalThis.localStorage : globalThis.sessionStorage
  destino?.setItem(CLAVE, token)
}

export function obtenerToken() {
  for (const almacen of almacenes()) {
    const token = almacen.getItem(CLAVE)
    if (token) return token
  }
  return null
}

/** true si la sesión actual se guardó con «Recordarme». */
export function sesionRecordada() {
  return Boolean(globalThis.localStorage?.getItem(CLAVE))
}

export function borrarToken() {
  for (const almacen of almacenes()) almacen.removeItem(CLAVE)
}
