import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { useSesionStore } from '@/stores/sesion'
import { configurarGuardas, crearRutas } from '@/router'
import { http } from '@/api/http'
import { crearAdaptadorMock, limpiarMocks } from '@/api/mock'
import { CONTRASENA_DEMO, reiniciarDatos } from '@/api/mocks/datos'
import { registrarMocks } from '@/api/mocks'
import { usarAlmacenesEnMemoria } from '@/api/__tests__/almacen'

const adaptadorOriginal = http.defaults.adapter

function crearRouterPrueba() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: crearRutas({ esDev: true }),
  })
  configurarGuardas(router)
  return router
}

describe('FE-14 · Sesión y guardas por rol', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    usarAlmacenesEnMemoria()
    reiniciarDatos()
    registrarMocks()
    http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
  })

  afterEach(() => {
    limpiarMocks()
    http.defaults.adapter = adaptadorOriginal
    vi.unstubAllGlobals()
  })

  it('guarda usuario, rol y canal en el store de sesión y limpia al salir', async () => {
    const sesion = useSesionStore()
    await sesion.entrar({
      usuario: 'admin.cedis',
      contrasena: CONTRASENA_DEMO,
      canal: 'web',
      recordar: true,
    })

    expect(sesion.autenticado).toBe(true)
    expect(sesion.nombreUsuario).toBe('admin.cedis')
    expect(sesion.rol).toBe('oficina')
    expect(sesion.canal).toBe('web')
    expect(sesion.rutaInicio).toBe('/web/oficina')

    sesion.salir()
    expect(sesion.autenticado).toBe(false)
    expect(sesion.rol).toBe('')
  })

  it('sin sesión redirige cualquier ruta al login de su canal (/login o /movil/login)', async () => {
    const router = crearRouterPrueba()

    await router.push('/web/oficina')
    expect(router.currentRoute.value.path).toBe('/login')

    await router.push('/movil/caseta')
    expect(router.currentRoute.value.path).toBe('/movil/login')
  })

  it('con sesión redirige rutas de otro rol o de otro canal al inicio del rol del usuario', async () => {
    const sesion = useSesionStore()
    const router = crearRouterPrueba()

    await sesion.entrar({
      usuario: 'suc07',
      contrasena: CONTRASENA_DEMO,
      canal: 'web',
    })

    await router.push('/web/oficina')
    expect(router.currentRoute.value.path).toBe('/web/sucursal')

    await router.push('/movil/caseta')
    expect(router.currentRoute.value.path).toBe('/web/sucursal')

    sesion.salir()
    await sesion.entrar({
      usuario: 'caseta.jlopez',
      contrasena: CONTRASENA_DEMO,
      canal: 'android',
    })

    await router.push('/web/oficina')
    expect(router.currentRoute.value.path).toBe('/movil/caseta')

    await router.push('/movil/desembarque')
    expect(router.currentRoute.value.path).toBe('/movil/caseta')
  })
})
