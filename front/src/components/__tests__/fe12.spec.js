import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import OficinaView from '@/views/OficinaView.vue'
import { iniciarSesion } from '@/api'
import { http } from '@/api/http'
import { crearAdaptadorMock, limpiarMocks } from '@/api/mock'
import { CONTRASENA_DEMO, reiniciarDatos } from '@/api/mocks/datos'
import { registrarMocks } from '@/api/mocks'
import { usarAlmacenesEnMemoria } from '@/api/__tests__/almacen'

const adaptadorOriginal = http.defaults.adapter

describe('FE-12 · Portal de Oficina e indicadores', () => {
  beforeEach(async () => {
    usarAlmacenesEnMemoria()
    reiniciarDatos()
    registrarMocks()
    http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
    await iniciarSesion({
      usuario: 'admin.cedis',
      contrasena: CONTRASENA_DEMO,
      canal: 'web',
    })
  })

  afterEach(() => {
    limpiarMocks()
    http.defaults.adapter = adaptadorOriginal
    vi.unstubAllGlobals()
  })

  it('muestra la navegación con conteo por catálogo, chip de fecha, 3 KPIs y 32 racks en 16 columnas desde @/api', async () => {
    const wrapper = mount(OficinaView)
    await flushPromises()

    const botonesNav = wrapper.findAll('#nav button')
    expect(botonesNav.length).toBe(4)
    expect(botonesNav[0].text()).toContain('Productos')
    expect(botonesNav[0].text()).toContain('7')
    expect(botonesNav[1].text()).toContain('Proveedores')
    expect(botonesNav[1].text()).toContain('4')
    expect(botonesNav[2].text()).toContain('Sucursales')
    expect(botonesNav[2].text()).toContain('6')
    expect(botonesNav[3].text()).toContain('Usuarios')
    expect(botonesNav[3].text()).toContain('7')

    expect(wrapper.find('#dt').text()).toContain('Mié 25 nov')

    const kpis = wrapper.find('#kpis')
    expect(kpis.text()).toContain('Camiones recibidos hoy')
    expect(kpis.text()).toContain('23 / 35')
    expect(kpis.text()).toContain('Embarques hoy')
    expect(kpis.text()).toContain('14 / 20')
    expect(kpis.text()).toContain('Recepciones sin error')
    expect(kpis.text()).toContain('96%')
    expect(kpis.text()).toContain('Ocupación de racks')
    expect(kpis.text()).toContain('78%')

    const racks = wrapper.findAll('.racks i')
    expect(racks.length).toBe(32)
    expect(wrapper.find('.racks').attributes('style')).toContain('repeat(16, 1fr)')
  })
})
