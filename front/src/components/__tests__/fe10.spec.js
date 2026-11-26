import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { mount, flushPromises } from '@vue/test-utils'
import LoginWebView from '@/views/LoginWebView.vue'
import { crearRutas } from '@/router'
import { http } from '@/api/http'
import { crearAdaptadorMock, limpiarMocks } from '@/api/mock'
import { CONTRASENA_DEMO, reiniciarDatos } from '@/api/mocks/datos'
import { registrarMocks } from '@/api/mocks'
import { sesionRecordada } from '@/api/sesion'
import { usarAlmacenesEnMemoria } from '@/api/__tests__/almacen'
import { useToast } from '@/composables/useToast'

const adaptadorOriginal = http.defaults.adapter

describe('FE-10 · LoginWeb', () => {
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

  it('cambia ilustración, lema, puntos y placeholder al elegir Sucursal, Proveedor u Oficina', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: crearRutas({ esDev: true }),
    })
    const wrapper = mount(LoginWebView, {
      global: { plugins: [router] },
    })

    expect(wrapper.find('#cap').text()).toBe('Pide y recibe a tiempo')
    expect(wrapper.find('#u').attributes('placeholder')).toBe('suc07@empresa.mx')
    expect(wrapper.findAll('#dots i')[0].classes()).toContain('on')

    const botonesRol = wrapper.findAll('#roles button')
    await botonesRol[1].trigger('click')
    expect(wrapper.find('#cap').text()).toBe('Agenda tu cita de entrega')
    expect(wrapper.find('#u').attributes('placeholder')).toBe('ventas@papeleradelgolfo.mx')
    expect(wrapper.findAll('#dots i')[1].classes()).toContain('on')

    await botonesRol[2].trigger('click')
    expect(wrapper.find('#cap').text()).toBe('Control total del catálogo')
    expect(wrapper.find('#u').attributes('placeholder')).toBe('admin.cedis')
    expect(wrapper.findAll('#dots i')[2].classes()).toContain('on')
  })

  it('muestra el aviso del prototipo con usuario o contraseña incorrectos', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: crearRutas({ esDev: true }),
    })
    const wrapper = mount(LoginWebView, {
      global: { plugins: [router] },
    })

    await wrapper.find('#u').setValue('admin.cedis')
    await wrapper.find('#p').setValue('incorrecta')
    await wrapper.find('#go').trigger('click')
    await flushPromises()

    expect(wrapper.find('.toast').classes()).toContain('show')
    expect(wrapper.find('.toast').text()).toContain('Revisa usuario y contraseña')
  })

  it('redirige al portal del rol que devuelve el back y respeta Recordarme', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: crearRutas({ esDev: true }),
    })
    await router.push('/login')
    await router.isReady()

    const wrapper = mount(LoginWebView, {
      global: { plugins: [router] },
    })

    await wrapper.find('input[type="checkbox"]').setValue(false)
    await wrapper.find('#u').setValue('admin.cedis')
    await wrapper.find('#p').setValue(CONTRASENA_DEMO)
    await wrapper.find('#go').trigger('click')
    await flushPromises()

    expect(sesionRecordada()).toBe(false)
    expect(router.currentRoute.value.path).toBe('/web/oficina')
  })
})
