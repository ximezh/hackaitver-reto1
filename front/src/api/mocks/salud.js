import { registrarMock } from '../mock.js'

export function registrarSalud() {
  registrarMock('get', '/health', () => ({ status: 'ok', database: 'ok' }))
}
