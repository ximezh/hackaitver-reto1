import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { useSesionStore } from '@/stores/sesion'
import { http } from '@/api/http'
import { crearAdaptadorMock, limpiarMocks } from '@/api/mock'
import { CONTRASENA_DEMO, reiniciarDatos } from '@/api/mocks/datos'
import { registrarMocks } from '@/api/mocks'
import { usarAlmacenesEnMemoria } from '@/api/__tests__/almacen'
import ProveedorView from '@/views/ProveedorView.vue'

const adaptadorOriginal = http.defaults.adapter

async function montar() {
  const wrapper = mount(ProveedorView, { attachTo: document.body })
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('FE-22 · Proveedor · Agendar cita', () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    usarAlmacenesEnMemoria()
    reiniciarDatos()
    registrarMocks()
    http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
    await useSesionStore().entrar({ usuario: 'pgolfo', contrasena: CONTRASENA_DEMO, canal: 'web' })
  })

  afterEach(() => {
    limpiarMocks()
    http.defaults.adapter = adaptadorOriginal
    document.body.innerHTML = ''
  })

  it('muestra navegación, órdenes sin cita, duraciones y el calendario de 4 andenes × 20 bloques', async () => {
    const wrapper = await montar()
    const nav = wrapper.findAll('#nav button').map((b) => b.text())
    expect(nav).toEqual(['Agendar cita', 'Factura y bultos', 'Historial'])
    expect(wrapper.find('#ttl').text()).toBe('Agendar cita')
    expect(wrapper.find('#oc').text()).toContain('OC-26-1182 ·')
    expect(wrapper.findAll('#dur button').map((b) => b.text())).toEqual([
      '1 h',
      '1.5 h',
      '2 h',
      '3 h',
    ])
    expect(wrapper.findAll('#cal .c')).toHaveLength(80)
    expect(wrapper.findAll('#days button[data-dia]')).toHaveLength(6)
    expect(wrapper.find('#ok').attributes('disabled')).toBeDefined()
  })

  it('marca el folio vacío como obligatorio y deja confirmar con folio y horario libre', async () => {
    const wrapper = await montar()
    const fac = wrapper.find('#fac')
    await fac.setValue('')
    await fac.trigger('change')
    await flushPromises()
    expect(wrapper.find('#err-fac').text()).toContain('El folio es obligatorio')

    await fac.setValue('FAC-Z-99999')
    await fac.trigger('change')
    await flushPromises()
    expect(wrapper.find('#err-fac').exists()).toBe(false)

    // Elige un día hábil posterior a hoy y busca una celda libre.
    const habiles = wrapper.findAll('#days button[data-dia]:not([disabled])')
    await habiles[1].trigger('click')
    await flushPromises()
    const celdas = wrapper.findAll('#cal .c')
    for (const celda of celdas.slice(40)) {
      await celda.trigger('click')
      if (!wrapper.find('#err-anden').exists()) break
    }
    expect(wrapper.find('.blk.mine').exists()).toBe(true)
    expect(wrapper.find('#ok').attributes('disabled')).toBeUndefined()

    await wrapper.find('#ok').trigger('click')
    await flushPromises()
    await flushPromises()
    expect(wrapper.find('.toast').text()).toContain('Cita confirmada · QR enviado')
    expect(wrapper.find('.blk.mine').exists()).toBe(false)
    wrapper.unmount()
  })
})
