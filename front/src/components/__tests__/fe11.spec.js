import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { mount, flushPromises } from '@vue/test-utils'
import LoginMovilView from '@/views/LoginMovilView.vue'
import { detectarRolMovil } from '@/utils/cedis'
import { crearRutas } from '@/router'
import { haySesion } from '@/api'
import { http } from '@/api/http'
import { crearAdaptadorMock, limpiarMocks } from '@/api/mock'
import { reiniciarDatos } from '@/api/mocks/datos'
import { registrarMocks } from '@/api/mocks'
import { usarAlmacenesEnMemoria } from '@/api/__tests__/almacen'
import { useToast } from '@/composables/useToast'

const adaptadorOriginal = http.defaults.adapter

describe('FE-11 · LoginMovil', () => {
  beforeEach(() => {
    usarAlmacenesEnMemoria()
    reiniciarDatos()
    registrarMocks()
    http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
    useToast().ocultar()
  })

  afterEach(() => {
    limpiarMocks()
    http.defaults.adapter = adaptadorOriginal
    vi.unstubAllGlobals()
    useToast().ocultar()
  })

  it('muestra el chip de rol con CEDIS Veracruz solo con los prefijos completos caseta., desem. y embar. (H-03)', async () => {
    expect(detectarRolMovil('cas')).toBeNull()
    expect(detectarRolMovil('des')).toBeNull()
    expect(detectarRolMovil('emb')).toBeNull()
    expect(detectarRolMovil('caseta.jlopez')).toBe('caseta')
    expect(detectarRolMovil('desem.mruiz')).toBe('desembarque')
    expect(detectarRolMovil('embar.acruz')).toBe('embarque')

    const wrapper = mount(LoginMovilView)
    await wrapper.find('#u').setValue('cas')
    expect(wrapper.find('#role').classes()).not.toContain('show')

    await wrapper.find('#u').setValue('caseta.jlopez')
    expect(wrapper.find('#role').classes()).toContain('show')
    expect(wrapper.find('#role').text()).toContain('Caseta')
    expect(wrapper.find('#role').text()).toContain('CEDIS Veracruz')
  })

  it('alterna mostrar contraseña y oculta «Probar como» en producción (N-02)', async () => {
    const devWrapper = mount(LoginMovilView, { props: { esProduccion: false } })
    expect(devWrapper.find('#demo').exists()).toBe(true)
    expect(devWrapper.find('#p').attributes('type')).toBe('password')

    await devWrapper.find('#eye').trigger('click')
    expect(devWrapper.find('#p').attributes('type')).toBe('text')

    const prodWrapper = mount(LoginMovilView, { props: { esProduccion: true } })
    expect(prodWrapper.find('#demo').exists()).toBe(false)
  })

  it('inicia sesión con «Probar como», muestra bienvenida con los 3 módulos del rol y permite Salir', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: crearRutas({ esDev: true }),
    })
    const wrapper = mount(LoginMovilView, {
      props: { esProduccion: false },
      global: { plugins: [router] },
    })

    await wrapper.find('button[data-k="desembarque"]').trigger('click')
    expect(wrapper.find('#u').element.value).toBe('desem.mruiz')
    expect(wrapper.find('#p').element.value).toBe('cedis2026')

    await wrapper.find('#go').trigger('click')
    await flushPromises()

    expect(haySesion()).toBe(true)
    expect(wrapper.find('#wel').classes()).toContain('show')
    expect(wrapper.find('#wel').text()).toContain('Bienvenido')
    expect(wrapper.find('#wel').text()).toContain('Sup. desembarque')
    const modulos = wrapper.findAll('#wel .mods div').map((m) => m.text())
    expect(modulos).toEqual(['Escanear', 'Bultos', 'Tarima 3D'])

    await wrapper.find('#back').trigger('click')
    expect(haySesion()).toBe(false)
    expect(wrapper.find('#wel').classes()).not.toContain('show')
  })
})
