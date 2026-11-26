import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import OficinaView from '@/views/OficinaView.vue'
import { iniciarSesion } from '@/api'
import { http } from '@/api/http'
import { crearAdaptadorMock, limpiarMocks } from '@/api/mock'
import { CONTRASENA_DEMO, reiniciarDatos } from '@/api/mocks/datos'
import { registrarMocks } from '@/api/mocks'
import { usarAlmacenesEnMemoria } from '@/api/__tests__/almacen'
import { useToast } from '@/composables/useToast'

const adaptadorOriginal = http.defaults.adapter

describe('FE-13 · CRUD de catálogos', () => {
  beforeEach(async () => {
    usarAlmacenesEnMemoria()
    reiniciarDatos()
    registrarMocks()
    http.defaults.adapter = crearAdaptadorMock({ latencia: 0 })
    useToast().ocultar()
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
    useToast().ocultar()
  })

  it('lista registros con miniatura de producto, busca y filtra la tabla', async () => {
    const wrapper = mount(OficinaView)
    await flushPromises()

    expect(wrapper.find('#cnt').text()).toBe('7 registros')
    expect(wrapper.findAll('table.tbl tr').length).toBe(8) // encabezado + 7 filas
    expect(wrapper.find('table.tbl .thumb img').exists()).toBe(true)

    await wrapper.find('#q').setValue('lapiz')
    await flushPromises()
    expect(wrapper.find('#cnt').text()).toBe('1 registros')
    expect(wrapper.find('table.tbl').text()).toContain('LAP-0012')
  })

  it('crea y edita un producto haciendo parpadear la fila y muestra errores del back en el campo', async () => {
    const wrapper = mount(OficinaView)
    await flushPromises()

    await wrapper.find('#new').trigger('click')
    expect(wrapper.find('#md').classes()).toContain('open')

    // Intentar guardar vacío muestra error de validación del back junto al campo
    await wrapper.find('#sv').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-err="sku"]').text()).toContain('Completa SKU')

    await wrapper.find('input[data-f="sku"]').setValue('BOR-0010')
    await wrapper.find('input[data-f="nombre"]').setValue('Borrador blanco')
    await wrapper.find('input[data-f="piezas_por_bulto"]').setValue('30')
    await wrapper.find('input[data-f="kg"]').setValue('3.2')
    await wrapper.find('input[data-f="m3"]').setValue('0.006')
    await wrapper.find('#sv').trigger('click')
    await flushPromises()

    expect(wrapper.find('#cnt').text()).toBe('8 registros')
    expect(wrapper.find('tr.flash').text()).toContain('BOR-0010')
    expect(wrapper.find('.toast').text()).toContain('Registro creado')

    // Editar primera fila
    await wrapper.find('button.ed').trigger('click')
    await wrapper.find('input[data-f="nombre"]').setValue('Resma carta editada')
    await wrapper.find('#sv').trigger('click')
    await flushPromises()

    expect(wrapper.find('table.tbl').text()).toContain('Resma carta editada')
    expect(wrapper.find('.toast').text()).toContain('Cambios guardados')
  })

  it('crea un usuario con selector de rol/sucursal y muestra contrasena_generada una sola vez (AV-DO-006)', async () => {
    const wrapper = mount(OficinaView)
    await flushPromises()

    await wrapper.find('#nav button[data-k="usuarios"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('#ttl').text()).toBe('Usuarios')

    await wrapper.find('#new').trigger('click')
    await wrapper.find('input[data-f="usuario"]').setValue('suc04')
    await wrapper.find('input[data-f="nombre"]').setValue('Suc. 04 Xalapa')
    await wrapper.find('select[data-f="rol"]').setValue('sucursal')
    expect(wrapper.find('select[data-f="sucursal_id"]').exists()).toBe(true)
    await wrapper.find('select[data-f="sucursal_id"]').setValue('2')

    await wrapper.find('#sv').trigger('click')
    await flushPromises()

    expect(wrapper.find('#md').classes()).toContain('open')
    expect(wrapper.find('#mdb').text()).toContain('Tmp-')
    await wrapper.find('#ok-pass').trigger('click')
    expect(wrapper.find('#md').classes()).not.toContain('open')
  })

  it('confirma ¿Eliminar? y muestra «Registro eliminado» tanto si se elimina como si se desactiva', async () => {
    const wrapper = mount(OficinaView)
    await flushPromises()

    await wrapper.find('#nav button[data-k="proveedores"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('#cnt').text()).toBe('4 registros')

    // Eliminar proveedor 1 (con productos -> se desactiva a Inactivo pero muestra Registro eliminado)
    await wrapper.find('button.del').trigger('click')
    expect(wrapper.find('#mdb').text()).toContain('¿Eliminar?')
    await wrapper.find('#dl').trigger('click')
    await flushPromises()

    expect(wrapper.find('.toast').text()).toContain('Registro eliminado')
    expect(wrapper.find('table.tbl').text()).toContain('Inactivo')
  })
})
