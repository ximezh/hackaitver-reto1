/**
 * Mocks de los catálogos de Oficina con las reglas y textos del contrato del sprint 1.
 */
import { errorMock, registrarMock, respuesta } from '../mock.js'
import { usuarioDeSesion, validacion } from './auth.js'
import { ROLES, db } from './datos.js'

const SIN_ACENTOS = (texto) =>
  String(texto ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()

function soloOficina(headers) {
  const u = usuarioDeSesion(headers)
  if (u.rol !== 'oficina') throw errorMock(403, 'No tienes acceso a esta sección', 'sin_permiso')
  return u
}

function buscar(tabla, id) {
  const registro = tabla.find((x) => x.id === Number(id))
  if (!registro) throw errorMock(404, 'No encontramos el registro', 'no_encontrado')
  return registro
}

function siguienteId(tabla) {
  return Math.max(0, ...tabla.map((x) => x.id)) + 1
}

/** Revisa los obligatorios y las reglas; lanza 422 con todos los campos inválidos. */
function validar(datos, reglas, { parcial = false } = {}) {
  const campos = {}
  for (const [campo, { etiqueta, obligatorio, revisar }] of Object.entries(reglas)) {
    const valor = datos[campo]
    const vacio = valor === undefined || valor === null || String(valor).trim() === ''
    if (vacio) {
      // Al editar solo se revisan los campos que llegan.
      if (obligatorio && (!parcial || campo in datos)) campos[campo] = `Completa ${etiqueta}`
      continue
    }
    const error = revisar?.(valor)
    if (error) campos[campo] = error
  }
  const [primero] = Object.values(campos)
  if (primero) throw validacion(primero, campos)
}

const positivo = (mensaje) => (v) => (Number(v) > 0 ? null : mensaje)

function registrarCrud({ ruta, tabla, reglas, preparar, publico, unico, despues, eliminar }) {
  const formato = publico ?? ((x) => x)

  registrarMock('get', ruta, ({ headers, query }) => {
    // Sprint 2: Sucursal también lista productos, solo los activos.
    const sesion = usuarioDeSesion(headers)
    const sucursalVeProductos = tabla === 'productos' && sesion.rol === 'sucursal'
    if (!sucursalVeProductos) soloOficina(headers)
    const q = SIN_ACENTOS(query.q)
    const items = db[tabla].filter(
      (x) =>
        (!sucursalVeProductos || x.estado === 'activo') &&
        (!q || SIN_ACENTOS(Object.values(x).join(' ')).includes(q)),
    )
    return { items: items.map(formato), total: items.length }
  })

  registrarMock('get', `${ruta}/:id`, ({ headers, params }) => {
    soloOficina(headers)
    return formato(buscar(db[tabla], params.id))
  })

  registrarMock('post', ruta, ({ headers, body }) => {
    const sesion = soloOficina(headers)
    const datos = { ...body }
    validar(datos, reglas)
    const registro = { id: siguienteId(db[tabla]), estado: 'activo', ...preparar(datos, null) }
    unico?.(registro)
    db[tabla].push(registro)
    const extra = despues?.(registro, sesion) ?? {}
    return respuesta(201, { ...formato(registro), ...extra })
  })

  registrarMock('patch', `${ruta}/:id`, ({ headers, params, body }) => {
    soloOficina(headers)
    const actual = buscar(db[tabla], params.id)
    const cambios = { ...body }
    validar(cambios, reglas, { parcial: true })
    const nuevo = { ...actual, ...preparar(cambios, actual) }
    unico?.(nuevo)
    Object.assign(actual, nuevo)
    return formato(actual)
  })

  registrarMock('delete', `${ruta}/:id`, ({ headers, params }) => {
    const sesion = soloOficina(headers)
    const registro = buscar(db[tabla], params.id)
    if (eliminar?.tieneDependencias(registro, sesion)) {
      registro.estado = 'inactivo'
      return { resultado: 'desactivado', registro: formato(registro) }
    }
    db[tabla].splice(db[tabla].indexOf(registro), 1)
    return { resultado: 'eliminado' }
  })
}

function duplicado(tabla, campo, registro, code, detail) {
  if (db[tabla].some((x) => x.id !== registro.id && x[campo] === registro[campo])) {
    throw errorMock(409, detail, code)
  }
}

const SKU = /^[A-Z0-9-]{3,20}$/
const RFC = /^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$/
const CLAVE = /^(0[1-9]|[12]\d|3[0-2])$/
const USUARIO = /^[a-z0-9._-]{3,40}$/

function registrarProductos() {
  registrarCrud({
    ruta: '/productos',
    tabla: 'productos',
    reglas: {
      sku: {
        etiqueta: 'SKU',
        obligatorio: true,
        revisar: (v) => (SKU.test(String(v).toUpperCase()) ? null : 'El SKU no es válido'),
      },
      nombre: { etiqueta: 'Producto', obligatorio: true },
      piezas_por_bulto: {
        etiqueta: 'Piezas/bulto',
        obligatorio: true,
        revisar: positivo('Las piezas por bulto deben ser mayores a 0'),
      },
      kg: {
        etiqueta: 'Peso bulto (kg)',
        obligatorio: true,
        revisar: positivo('El peso debe ser mayor a 0'),
      },
      m3: {
        etiqueta: 'Volumen (m³)',
        obligatorio: true,
        revisar: positivo('El volumen debe ser mayor a 0'),
      },
      proveedor_id: {
        etiqueta: 'Proveedor',
        revisar: (v) =>
          db.proveedores.some((p) => p.id === Number(v)) ? null : 'El proveedor no existe',
      },
    },
    preparar: (d, actual) => ({
      ...d,
      ...(d.sku !== undefined && { sku: String(d.sku).toUpperCase() }),
      ...(d.piezas_por_bulto !== undefined && { piezas_por_bulto: Number(d.piezas_por_bulto) }),
      ...(d.kg !== undefined && { kg: Math.round(Number(d.kg) * 10) / 10 }),
      ...(d.m3 !== undefined && { m3: Math.round(Number(d.m3) * 1000) / 1000 }),
      ...(!actual && {
        ilustracion: d.ilustracion ?? 'bulto',
        unidad: d.unidad ?? 'piezas',
        proveedor_id: d.proveedor_id ?? null,
      }),
    }),
    publico: (p) => {
      const prov = db.proveedores.find((x) => x.id === p.proveedor_id)
      return { ...p, proveedor: prov ? { id: prov.id, nombre: prov.nombre } : null }
    },
    unico: (r) => duplicado('productos', 'sku', r, 'sku_duplicado', 'Este SKU ya está registrado'),
  })
}

function registrarProveedores() {
  registrarCrud({
    ruta: '/proveedores',
    tabla: 'proveedores',
    reglas: {
      rfc: {
        etiqueta: 'RFC',
        obligatorio: true,
        revisar: (v) => (RFC.test(String(v).toUpperCase()) ? null : 'El RFC no es válido'),
      },
      nombre: { etiqueta: 'Proveedor', obligatorio: true },
    },
    preparar: (d) => ({ ...d, ...(d.rfc !== undefined && { rfc: String(d.rfc).toUpperCase() }) }),
    unico: (r) =>
      duplicado('proveedores', 'rfc', r, 'rfc_duplicado', 'Este RFC ya está registrado'),
    eliminar: {
      tieneDependencias: (p) =>
        db.productos.some((x) => x.proveedor_id === p.id) ||
        db.usuarios.some((x) => x.proveedor_id === p.id),
    },
  })
}

function registrarSucursales() {
  registrarCrud({
    ruta: '/sucursales',
    tabla: 'sucursales',
    reglas: {
      clave: {
        etiqueta: 'Clave',
        obligatorio: true,
        revisar: (v) => (CLAVE.test(String(v)) ? null : 'La clave debe ser de 01 a 32'),
      },
      nombre: { etiqueta: 'Sucursal', obligatorio: true },
      ciudad: { etiqueta: 'Ciudad', obligatorio: true },
    },
    preparar: (d, actual) => {
      if (actual && ('clave' in d || 'rack' in d)) {
        const m = 'La clave no se puede cambiar'
        throw validacion(m, { clave: m })
      }
      return actual ? d : { ...d, rack: `R-${d.clave}` }
    },
    unico: (r) => {
      duplicado('sucursales', 'clave', r, 'clave_duplicada', 'Esta clave ya está registrada')
      duplicado('sucursales', 'rack', r, 'rack_ocupado', 'Ese rack ya está asignado')
    },
    eliminar: { tieneDependencias: (s) => db.usuarios.some((x) => x.sucursal_id === s.id) },
  })
}

function contrasenaTemporal() {
  const parte = () => Math.random().toString(36).slice(2, 6)
  return `Tmp-${parte()}-${parte()}`
}

function publicoUsuario(u) {
  const s = db.sucursales.find((x) => x.id === u.sucursal_id)
  const p = db.proveedores.find((x) => x.id === u.proveedor_id)
  return {
    id: u.id,
    usuario: u.usuario,
    nombre: u.nombre,
    rol: u.rol,
    canal: u.canal,
    sucursal_id: u.sucursal_id ?? null,
    sucursal: s ? { id: s.id, nombre: s.nombre } : null,
    proveedor_id: u.proveedor_id ?? null,
    proveedor: p ? { id: p.id, nombre: p.nombre } : null,
    contrasena_temporal: u.contrasena_temporal,
    estado: u.estado,
  }
}

function revisarUsuario(u) {
  const reglaRol = ROLES[u.rol]
  const prefijos = Object.values(ROLES)
    .map((r) => r.prefijo)
    .filter(Boolean)
  if (reglaRol.prefijo && !u.usuario.startsWith(reglaRol.prefijo)) {
    const m = `El usuario de ${reglaRol.etiqueta} debe empezar con ${reglaRol.prefijo}`
    throw validacion(m, { usuario: m })
  }
  if (!reglaRol.prefijo && prefijos.some((p) => u.usuario.startsWith(p))) {
    const m = 'Ese prefijo es solo para usuarios de Android'
    throw validacion(m, { usuario: m })
  }
  if (u.rol === 'sucursal' && !db.sucursales.some((s) => s.id === u.sucursal_id)) {
    throw validacion('Elige la sucursal', { sucursal_id: 'Elige la sucursal' })
  }
  if (u.rol === 'proveedor' && !db.proveedores.some((p) => p.id === u.proveedor_id)) {
    throw validacion('Elige el proveedor', { proveedor_id: 'Elige el proveedor' })
  }
  duplicado('usuarios', 'usuario', u, 'usuario_duplicado', 'Este usuario ya está registrado')
}

function registrarUsuarios() {
  registrarCrud({
    ruta: '/usuarios',
    tabla: 'usuarios',
    reglas: {
      usuario: {
        etiqueta: 'Usuario',
        obligatorio: true,
        revisar: (v) => (USUARIO.test(String(v).toLowerCase()) ? null : 'El usuario no es válido'),
      },
      nombre: { etiqueta: 'Nombre', obligatorio: true },
      rol: {
        etiqueta: 'Rol',
        obligatorio: true,
        revisar: (v) => (v in ROLES ? null : 'El rol no es válido'),
      },
    },
    preparar: (d, actual) => {
      const r = { ...actual, ...d }
      if (d.usuario !== undefined) r.usuario = String(d.usuario).trim().toLowerCase()
      r.canal = ROLES[r.rol].canal
      r.sucursal_id = r.rol === 'sucursal' ? Number(r.sucursal_id) || null : null
      r.proveedor_id = r.rol === 'proveedor' ? Number(r.proveedor_id) || null : null
      if (!actual) {
        r.contrasena = contrasenaTemporal()
        r.contrasena_temporal = true
      }
      return r
    },
    publico: publicoUsuario,
    unico: revisarUsuario,
    despues: (u) => ({ contrasena_generada: u.contrasena }),
    eliminar: {
      tieneDependencias: (u, sesion) => {
        if (u.id === sesion.id) {
          throw errorMock(409, 'No puedes eliminar tu propio usuario', 'no_puedes_eliminarte')
        }
        return false
      },
    },
  })

  registrarMock('post', '/usuarios/:id/restablecer', ({ headers, params }) => {
    soloOficina(headers)
    const u = buscar(db.usuarios, params.id)
    u.contrasena = contrasenaTemporal()
    u.contrasena_temporal = true
    return { ...publicoUsuario(u), contrasena_generada: u.contrasena }
  })
}

export function registrarCatalogos() {
  registrarProductos()
  registrarProveedores()
  registrarSucursales()
  registrarUsuarios()
}
