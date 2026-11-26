import { errorMock, registrarMock } from '../mock.js'
import { db, usuarios } from './datos.js'

const EXPIRA_EN = 43200

/** Forma pública del usuario: la de `GET /api/auth/me`. */
export function perfil(u) {
  const s = db.sucursales.find((x) => x.id === u.sucursal_id)
  const p = db.proveedores.find((x) => x.id === u.proveedor_id)
  return {
    id: u.id,
    usuario: u.usuario,
    nombre: u.nombre,
    rol: u.rol,
    canal: u.canal,
    contrasena_temporal: u.contrasena_temporal,
    sucursal: s ? { id: s.id, clave: s.clave, nombre: s.nombre } : null,
    proveedor: p ? { id: p.id, rfc: p.rfc, nombre: p.nombre } : null,
  }
}

function token(u) {
  return `mock.${u.id}.${u.contrasena_temporal ? 'temporal' : 'ok'}`
}

function sesion(u) {
  return {
    access_token: token(u),
    token_type: 'bearer',
    expira_en: EXPIRA_EN,
    contrasena_temporal: u.contrasena_temporal,
    usuario: perfil(u),
  }
}

/**
 * Usuario de la sesión según el encabezado Authorization, o error 401 como el back.
 * Con `permitirTemporal: false` responde 403 si la contraseña es temporal (R-17).
 */
export function usuarioDeSesion(headers, { permitirTemporal = false } = {}) {
  const valor = headers?.Authorization ?? headers?.authorization ?? ''
  const id = Number(valor.match(/^Bearer mock\.(\d+)\./)?.[1])
  const u = usuarios.find((x) => x.id === id)
  if (!u) throw errorMock(401, 'Inicia sesión para continuar', 'no_autenticado')
  if (u.contrasena_temporal && !permitirTemporal) {
    throw errorMock(403, 'Cambia tu contraseña para continuar', 'cambio_contrasena_requerido')
  }
  return u
}

export function validacion(detail, campos) {
  const error = errorMock(422, detail, 'validacion')
  error.mock.datos.campos = campos
  return error
}

export function registrarAuth() {
  registrarMock('post', '/auth/login', ({ body }) => {
    const usuario = String(body?.usuario ?? '')
      .trim()
      .toLowerCase()
    const { contrasena, canal } = body ?? {}
    if (!usuario || !contrasena || !canal) {
      throw validacion('Revisa usuario y contraseña', {
        ...(!usuario && { usuario: 'Revisa usuario y contraseña' }),
        ...(!contrasena && { contrasena: 'Revisa usuario y contraseña' }),
      })
    }
    const u = usuarios.find((x) => x.usuario === usuario)
    if (!u || u.contrasena !== contrasena) {
      throw errorMock(401, 'Revisa usuario y contraseña', 'credenciales_invalidas')
    }
    if (u.estado === 'inactivo') {
      throw errorMock(403, 'Tu usuario está inactivo. Comunícate con Oficina', 'usuario_inactivo')
    }
    if (u.canal !== canal) {
      const detalle =
        u.canal === 'android'
          ? 'Este usuario entra desde el teléfono'
          : 'Este usuario entra desde la web'
      throw errorMock(403, detalle, 'canal_incorrecto')
    }
    return sesion(u)
  })

  registrarMock('get', '/auth/me', ({ headers }) =>
    perfil(usuarioDeSesion(headers, { permitirTemporal: true })),
  )

  registrarMock('post', '/auth/contrasena', ({ headers, body }) => {
    const u = usuarioDeSesion(headers, { permitirTemporal: true })
    const { actual, nueva } = body ?? {}
    if (actual !== u.contrasena) {
      throw errorMock(400, 'La contraseña actual no coincide', 'contrasena_actual_incorrecta')
    }
    if (!nueva || nueva.length < 8) {
      const m = 'La contraseña debe tener al menos 8 caracteres'
      throw validacion(m, { nueva: m })
    }
    if (nueva === actual) {
      const m = 'La contraseña nueva debe ser distinta de la actual'
      throw validacion(m, { nueva: m })
    }
    u.contrasena = nueva
    u.contrasena_temporal = false
    return sesion(u)
  })
}
