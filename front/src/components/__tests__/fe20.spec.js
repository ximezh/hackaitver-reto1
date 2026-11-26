import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SucursalView from '@/views/SucursalView.vue'
import { iniciarSesion } from '@/api'
import { http } from '@/api/http'
import { crearAdaptadorMock, limpiarMocks } from '@/api/mock'
import { CONTRASENA_DEMO, reiniciarDatos } from '@/api/mocks/datos'
import { registrarMocks } from '@/api/mocks'
import { usarAlmacenesEnMemoria } from '@/api/__tests__/almacen'
import { useToast } from '@/composables/useToast'

const adaptadorOriginal = http.defaults.adapter

describe('FE-20 · Sucursal · Pedir', () => {
  let pinia

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)
    usarAlmacenesEnMemoria()
    reiniciarDatos()
    registrarMocks()
    http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
    useToast().ocultar()
    await iniciarSesion({ usuario: 'suc07', contrasena: CONTRASENA_DEMO, canal: 'web' })
  })

  afterEach(() => {
    limpiarMocks()
    http.defaults.adapter = adaptadorOriginal
    useToast().ocultar()
  })

  it('arma el pedido con el catálogo y lo envía al CEDIS', async () => {
    const wrapper = mount(SucursalView, { global: { plugins: [pinia] } })
    await flushPromises()

    const tarjetas = wrapper.findAll('.prod')
    expect(tarjetas.length).toBeGreaterThan(0)
    expect(wrapper.text()).toContain('Agrega productos')
    expect(wrapper.find('#send').attributes('disabled')).toBeDefined()

    const mas = tarjetas[0].find('[aria-label="Más"]')
    await mas.trigger('click')
    await mas.trigger('click')
    expect(tarjetas[0].find('.step b').text()).toBe('2')
    expect(wrapper.find('.cart .chip').text()).toBe('2 bultos')
    expect(wrapper.findAll('.cart .it').length).toBe(1)

    await wrapper.find('#send').trigger('click')
    await flushPromises()

    expect(useToast().mensaje.value).toMatch(/^OC-.+ enviada al CEDIS$/)
    expect(wrapper.find('.cart .chip').text()).toBe('0 bultos')
    expect(wrapper.text()).toContain('Agrega productos')
  })
})
