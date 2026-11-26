/**
 * Datos de los mocks: los ejemplos del contrato del sprint 1, que son los del prototipo.
 * Viven en memoria; recargar la página los regresa a este estado.
 */

/** Contraseña de todos los usuarios de demostración en modo mock. */
export const CONTRASENA_DEMO = 'cedis2026'

const USUARIOS = [
  {
    id: 1,
    usuario: 'caseta.jlopez',
    nombre: 'Jorge López',
    rol: 'caseta',
    canal: 'android',
    sucursal: null,
    proveedor: null,
  },
  {
    id: 2,
    usuario: 'desem.mruiz',
    nombre: 'María Ruiz',
    rol: 'desembarque',
    canal: 'android',
    sucursal: null,
    proveedor: null,
  },
  {
    id: 3,
    usuario: 'embar.acruz',
    nombre: 'Alan Cruz',
    rol: 'embarque',
    canal: 'android',
    sucursal: null,
    proveedor: null,
  },
  {
    id: 4,
    usuario: 'suc07',
    nombre: 'Suc. 07 Boca del Río',
    rol: 'sucursal',
    canal: 'web',
    sucursal: { id: 3, clave: '07', nombre: 'Suc. 07 Boca del Río' },
    proveedor: null,
  },
  {
    id: 5,
    usuario: 'pgolfo',
    nombre: 'Papelera del Golfo',
    rol: 'proveedor',
    canal: 'web',
    sucursal: null,
    proveedor: { id: 1, rfc: 'PGO090312AB1', nombre: 'Papelera del Golfo' },
  },
  {
    id: 6,
    usuario: 'admin.cedis',
    nombre: 'Ana Domínguez',
    rol: 'oficina',
    canal: 'web',
    sucursal: null,
    proveedor: null,
  },
  // Usuario recién creado por Oficina, para probar el cambio obligatorio de contraseña (R-17).
  {
    id: 7,
    usuario: 'caseta.rgomez',
    nombre: 'Rosa Gómez',
    rol: 'caseta',
    canal: 'android',
    sucursal: null,
    proveedor: null,
  },
]

const TEMPORALES = { 7: 'Tmp-7Kq2-xW9p' }

function crearUsuarios() {
  return USUARIOS.map((u) => ({
    ...structuredClone(u),
    estado: 'activo',
    contrasena_temporal: u.id in TEMPORALES,
    contrasena: TEMPORALES[u.id] ?? CONTRASENA_DEMO,
  }))
}

/** Lista viva que modifican los mocks (cambio de contraseña, CRUD de Oficina). */
export const usuarios = crearUsuarios()

/** Regresa los datos al estado inicial. Lo usan las pruebas. */
export function reiniciarDatos() {
  usuarios.splice(0, usuarios.length, ...crearUsuarios())
}
