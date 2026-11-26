// Registra los mocks de cada servicio. Cada servicio nuevo agrega aquí su función `registrar…`.
import { registrarAuth } from './auth.js'
import { registrarCatalogos } from './catalogos.js'
import { registrarPedidos } from './pedidos.js'
import { registrarSalud } from './salud.js'

export function registrarMocks() {
  registrarSalud()
  registrarAuth()
  registrarCatalogos()
  registrarPedidos()
}
