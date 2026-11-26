/**
 * Datos de los mocks: los ejemplos del contrato del sprint 1 (docs/api/sprint-1.md), que son
 * los del prototipo. Viven en memoria; recargar la página los regresa a este estado.
 */

/** Contraseña de todos los usuarios de demostración en modo mock. */
export const CONTRASENA_DEMO = 'cedis2026'

const PRODUCTOS = [
  ['RES-0500', 'Resma carta 500 hojas', 'hojas', 'resmas', 10, 25.0, 0.032, 1],
  ['CUA-0100', 'Cuaderno profesional 100 h', 'bulto', 'cuadernos', 24, 16.8, 0.03, 3],
  ['FOL-0100', 'Folder carta crema', 'bulto', 'folders', 100, 9.6, 0.024, 3],
  ['ENG-0020', 'Engrapadora metálica', 'bulto', 'piezas', 20, 8.2, 0.02, 2],
  ['PAP-0100', 'Hojas carta, paquete 100', 'hojas', 'paquetes', 10, 5.1, 0.018, 1],
  ['LAP-0012', 'Lápiz HB, caja 12', 'lapices', 'cajas', 24, 2.4, 0.008, 2],
  ['CLI-0100', 'Clip #1, caja 100', 'clips', 'cajas', 40, 1.0, 0.004, 2],
].map(([sku, nombre, ilustracion, unidad, piezas_por_bulto, kg, m3, proveedor_id], i) => ({
  id: i + 1,
  sku,
  nombre,
  ilustracion,
  unidad,
  piezas_por_bulto,
  kg,
  m3,
  proveedor_id,
  estado: 'activo',
}))

const PROVEEDORES = [
  ['PGO090312AB1', 'Papelera del Golfo', 'Laura Pérez', '229 555 0142', 'activo'],
  ['DAT110820KL3', 'Distribuidora Atlas', 'Hugo Ríos', '228 555 0193', 'activo'],
  ['GEM150101QW8', 'Grupo Escolar MX', 'Sofía Lara', '55 5555 0110', 'activo'],
  ['USU180507ZX2', 'Útiles del Sureste', 'Iván Cruz', '999 555 0177', 'suspendido'],
].map(([rfc, nombre, contacto, telefono, estado], i) => ({
  id: i + 1,
  rfc,
  nombre,
  contacto,
  telefono,
  estado,
}))

const SUCURSALES = [
  ['01', 'Suc. 01 Centro', 'Centro'],
  ['04', 'Suc. 04 Xalapa', 'Xalapa'],
  ['07', 'Suc. 07 Boca del Río', 'Boca del Río'],
  ['12', 'Suc. 12 Córdoba', 'Córdoba'],
  ['18', 'Suc. 18 Orizaba', 'Orizaba'],
  ['21', 'Suc. 21 Tuxpan', 'Tuxpan'],
].map(([clave, nombre, ciudad], i) => ({
  id: i + 1,
  clave,
  nombre,
  ciudad,
  rack: `R-${clave}`,
  estado: 'activo',
}))

const USUARIOS = [
  ['caseta.jlopez', 'Jorge López', 'caseta', null, null],
  ['desem.mruiz', 'María Ruiz', 'desembarque', null, null],
  ['embar.acruz', 'Alan Cruz', 'embarque', null, null],
  ['suc07', 'Suc. 07 Boca del Río', 'sucursal', 3, null],
  ['pgolfo', 'Papelera del Golfo', 'proveedor', null, 1],
  ['admin.cedis', 'Ana Domínguez', 'oficina', null, null],
  // Usuario recién creado por Oficina, para probar el cambio obligatorio de contraseña (R-17).
  ['caseta.rgomez', 'Rosa Gómez', 'caseta', null, null],
].map(([usuario, nombre, rol, sucursal_id, proveedor_id], i) => ({
  id: i + 1,
  usuario,
  nombre,
  rol,
  sucursal_id,
  proveedor_id,
  estado: 'activo',
}))

const TEMPORALES = { 7: 'Tmp-7Kq2-xW9p' }

export const ROLES = {
  caseta: { canal: 'android', prefijo: 'caseta.', etiqueta: 'Caseta' },
  desembarque: { canal: 'android', prefijo: 'desem.', etiqueta: 'Sup. desembarque' },
  embarque: { canal: 'android', prefijo: 'embar.', etiqueta: 'Sup. embarque' },
  sucursal: { canal: 'web', prefijo: null, etiqueta: 'Sucursal' },
  proveedor: { canal: 'web', prefijo: null, etiqueta: 'Proveedor' },
  oficina: { canal: 'web', prefijo: null, etiqueta: 'Oficina' },
}

function crear() {
  return {
    productos: structuredClone(PRODUCTOS),
    proveedores: structuredClone(PROVEEDORES),
    sucursales: structuredClone(SUCURSALES),
    usuarios: USUARIOS.map((u) => ({
      ...structuredClone(u),
      canal: ROLES[u.rol].canal,
      contrasena_temporal: u.id in TEMPORALES,
      contrasena: TEMPORALES[u.id] ?? CONTRASENA_DEMO,
    })),
  }
}

/** Tablas vivas que modifican los mocks. */
export const db = crear()
export const usuarios = db.usuarios

/** Regresa los datos al estado inicial. Lo usan las pruebas. */
export function reiniciarDatos() {
  const nuevo = crear()
  for (const tabla of Object.keys(db)) db[tabla].splice(0, db[tabla].length, ...nuevo[tabla])
}
