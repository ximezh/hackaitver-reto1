import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BotonBase from '../BotonBase.vue'
import Chip from '../Chip.vue'
import CampoTexto from '../CampoTexto.vue'
import Segmentado from '../Segmentado.vue'
import BarraAvance from '../BarraAvance.vue'
import ZonasTarima from '../ZonasTarima.vue'
import ElementosView from '@/views/ElementosView.vue'
import { crearRutas } from '@/router'

describe('FE-04 · Componentes base (Elementos)', () => {
  it('renderiza BotonBase con sus variantes (primary, soft, line, danger, ok) y estados (sm, block, disabled)', () => {
    for (const variante of ['primary', 'soft', 'line', 'danger', 'ok']) {
      const w = mount(BotonBase, {
        props: { variante },
        slots: { default: 'Acción' },
      })
      expect(w.classes()).toContain('btn')
      expect(w.classes()).toContain(variante)
    }

    const completo = mount(BotonBase, {
      props: {
        variante: 'primary',
        sm: true,
        block: true,
        disabled: true,
        icono: 'scan',
      },
      slots: { default: 'Escanear' },
    })
    expect(completo.classes()).toContain('sm')
    expect(completo.classes()).toContain('block')
    expect(completo.attributes('disabled')).toBeDefined()
    expect(completo.find('svg').exists()).toBe(true)
  })

  it('renderiza Chip con variantes normal, ok, warn, bad y mute, con punto o ícono', () => {
    const normal = mount(Chip, {
      props: { punto: true },
      slots: { default: 'En andén' },
    })
    expect(normal.classes()).toEqual(['chip'])
    expect(normal.find('.dot').exists()).toBe(true)

    for (const variante of ['ok', 'warn', 'bad', 'mute']) {
      const chip = mount(Chip, {
        props: { variante, icono: 'check' },
        slots: { default: 'Estado' },
      })
      expect(chip.classes()).toContain('chip')
      expect(chip.classes()).toContain(variante)
      expect(chip.find('svg').exists()).toBe(true)
    }
  })

  it('renderiza CampoTexto con ícono y actualiza v-model', async () => {
    const wrapper = mount(CampoTexto, {
      props: {
        modelValue: 'suc07',
        placeholder: 'Usuario',
        icono: 'user',
        sm: true,
      },
    })
    expect(wrapper.classes()).toContain('field')
    expect(wrapper.classes()).toContain('sm')
    expect(wrapper.find('svg').exists()).toBe(true)
    const input = wrapper.find('input')
    expect(input.element.value).toBe('suc07')
    await input.setValue('admin.cedis')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['admin.cedis'])
  })

  it('renderiza Segmentado y cambia la opción activa', async () => {
    const opciones = [
      { valor: 'in', etiqueta: 'Entradas', icono: 'login' },
      { valor: 'out', etiqueta: 'Salidas', icono: 'exit' },
    ]
    const wrapper = mount(Segmentado, {
      props: {
        modelValue: 'in',
        opciones,
      },
    })
    const botones = wrapper.findAll('button')
    expect(botones.length).toBe(2)
    expect(botones[0].classes()).toContain('on')
    expect(botones[1].classes()).not.toContain('on')

    await botones[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['out'])
  })

  it('renderiza BarraAvance con valor, tope y variantes', () => {
    const barra = mount(BarraAvance, {
      props: {
        etiqueta: 'Peso de tarima',
        valor: 567,
        tope: 1000,
        unidad: 'kg',
        variante: 'ok',
      },
    })
    expect(barra.text()).toContain('Peso de tarima')
    expect(barra.text()).toContain('567 / 1,000 kg')
    expect(barra.find('.bar').classes()).toContain('ok')
    expect(barra.find('.bar > i').attributes('style')).toContain('width: 56.7%')
  })

  it('renderiza ZonasTarima y la vista /elementos (solo en desarrollo) idéntica al prototipo', () => {
    const zonas = mount(ZonasTarima)
    expect(zonas.text()).toContain('Caja roja')
    expect(zonas.text()).toContain('Caja naranja')
    expect(zonas.text()).toContain('Caja verde')

    const vista = mount(ElementosView)
    expect(vista.find('#el.el').exists()).toBe(true)
    expect(vista.findAll('.card').length).toBe(5)
    expect(vista.text()).toContain('Escanear bulto')
    expect(vista.text()).toContain('567 / 1,000 kg')
    expect(vista.text()).toContain('Tortón · regla 90%')

    const rutasDev = crearRutas({ esDev: true })
    const rutasProd = crearRutas({ esDev: false })
    expect(rutasDev.some((r) => r.path === '/elementos')).toBe(true)
    expect(rutasProd.some((r) => r.path === '/elementos')).toBe(false)
  })
})
