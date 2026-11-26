/**
 * Catálogos de Oficina: productos, proveedores, sucursales y usuarios (contrato del sprint 1).
 * Los cuatro siguen el mismo patrón:
 *   listar({ q }) → { items, total } · obtener(id) · crear(datos) · editar(id, cambios)
 *   eliminar(id) → { resultado: 'eliminado' } o { resultado: 'desactivado', registro }
 */
import { http } from './http.js'

function crearCatalogo(ruta) {
  return {
    async listar({ q } = {}) {
      const { data } = await http.get(ruta, { params: q ? { q } : undefined })
      return data
    },
    async obtener(id) {
      const { data } = await http.get(`${ruta}/${id}`)
      return data
    },
    async crear(datos) {
      const { data } = await http.post(ruta, datos)
      return data
    },
    /** Solo se envían los campos que cambian. */
    async editar(id, cambios) {
      const { data } = await http.patch(`${ruta}/${id}`, cambios)
      return data
    },
    async eliminar(id) {
      const { data } = await http.delete(`${ruta}/${id}`)
      return data
    },
  }
}

export const productos = crearCatalogo('/productos')
export const proveedores = crearCatalogo('/proveedores')
export const sucursales = crearCatalogo('/sucursales')
export const usuarios = {
  ...crearCatalogo('/usuarios'),
  /** Genera una contraseña temporal nueva. La respuesta trae `contrasena_generada` una sola vez. */
  async restablecer(id) {
    const { data } = await http.post(`/usuarios/${id}/restablecer`)
    return data
  },
}

/** Roles fijos del contrato, con su etiqueta y canal. Sirven para el selector de Usuarios. */
export const ROLES = [
  { rol: 'caseta', etiqueta: 'Caseta', canal: 'android', prefijo: 'caseta.' },
  { rol: 'desembarque', etiqueta: 'Sup. desembarque', canal: 'android', prefijo: 'desem.' },
  { rol: 'embarque', etiqueta: 'Sup. embarque', canal: 'android', prefijo: 'embar.' },
  { rol: 'sucursal', etiqueta: 'Sucursal', canal: 'web', prefijo: null },
  { rol: 'proveedor', etiqueta: 'Proveedor', canal: 'web', prefijo: null },
  { rol: 'oficina', etiqueta: 'Oficina', canal: 'web', prefijo: null },
]

/** Etiquetas de los estados del contrato, con la variante de chip del prototipo. */
export const ESTADOS = {
  activo: { etiqueta: 'Activo', chip: 'ok' },
  suspendido: { etiqueta: 'Suspendido', chip: 'warn' },
  inactivo: { etiqueta: 'Inactivo', chip: 'warn' },
}
