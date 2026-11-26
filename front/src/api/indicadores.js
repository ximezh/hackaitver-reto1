/**
 * Indicadores del día y ocupación de racks de Oficina.
 *
 * El back los calcula hasta el sprint 4 (BE-44, H-13). Mientras tanto, según el contrato del
 * sprint 1 («Fuera de este contrato»), el front usa los valores del prototipo
 * (`design/CEDIS Flow/components/Oficina/preview.html`). Cuando exista la ruta, solo cambia
 * esta función y las pantallas no se tocan.
 */
const OCUPACION_PROTOTIPO = [
  28, 31, 19, 24, 32, 12, 27, 30, 22, 26, 29, 17, 31, 25, 20, 23, 30, 28, 14, 26, 32, 24, 21, 27,
  19, 30, 25, 22, 29, 18, 26, 31,
]

/**
 * @returns {Promise<{
 *   camiones_recibidos: { valor: number, total: number },
 *   embarques: { valor: number, total: number },
 *   recepciones_sin_error: number,
 *   racks: { rack: string, ocupadas: number, capacidad: number }[],
 * }>}
 */
export async function obtenerIndicadoresOficina() {
  return {
    camiones_recibidos: { valor: 23, total: 35 },
    embarques: { valor: 14, total: 20 },
    recepciones_sin_error: 96,
    racks: OCUPACION_PROTOTIPO.map((ocupadas, i) => ({
      rack: `R-${String(i + 1).padStart(2, '0')}`,
      ocupadas,
      capacidad: 32,
    })),
  }
}
