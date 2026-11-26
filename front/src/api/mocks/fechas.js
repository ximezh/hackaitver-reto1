// Fechas de los mocks en la zona de la operación (S-06).
const ZONA = 'America/Mexico_City'
export const hoy = () => new Intl.DateTimeFormat('en-CA', { timeZone: ZONA }).format(new Date())
export const sumarDias = (dia, n) => {
  const d = new Date(`${dia}T12:00:00Z`)
  d.setUTCDate(d.getUTCDate() + n)
  return d.toISOString().slice(0, 10)
}
export const esDomingo = (dia) => new Date(`${dia}T12:00:00Z`).getUTCDay() === 0
export const aMin = (hhmm) => Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5))
export const aHora = (min) =>
  `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`
export function proximoHabil(dia) {
  let d = sumarDias(dia, 1)
  while (esDomingo(d)) d = sumarDias(d, 1)
  return d
}
