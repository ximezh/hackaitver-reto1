import { http } from './http.js'

/** Estado de la API y de su conexión a PostgreSQL: `{ status, database }`. */
export async function obtenerSalud() {
  const { data } = await http.get('/health')
  return data
}
