import { vi } from 'vitest'

/**
 * localStorage y sessionStorage en memoria para las pruebas.
 * Node 25+ define su propio `localStorage` experimental, que tapa el de jsdom y queda sin
 * funcionar si no se arranca con `--localstorage-file`. En el navegador no hace falta.
 */
class AlmacenEnMemoria {
  #datos = new Map()
  getItem(clave) {
    return this.#datos.has(clave) ? this.#datos.get(clave) : null
  }
  setItem(clave, valor) {
    this.#datos.set(clave, String(valor))
  }
  removeItem(clave) {
    this.#datos.delete(clave)
  }
  clear() {
    this.#datos.clear()
  }
}

export function usarAlmacenesEnMemoria() {
  vi.stubGlobal('localStorage', new AlmacenEnMemoria())
  vi.stubGlobal('sessionStorage', new AlmacenEnMemoria())
}
