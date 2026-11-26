import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Icono from '../Icono.vue'
import CodigoQr from '../CodigoQr.vue'
import { ICONOS, zona, zonas, formatoKg } from '@/utils/cedis'
import { generarMatrizQr } from '@/utils/qr'

describe('FE-02 · Íconos y utilidades visuales', () => {
  it('renderiza Icono con caja de 24px, trazo 1.8 por defecto y tamaño/grosor configurables', () => {
    expect(Object.keys(ICONOS).length).toBeGreaterThanOrEqual(48)

    const porDefecto = mount(Icono, { props: { nombre: 'scan' } })
    const svg = porDefecto.find('svg')
    expect(svg.attributes('viewBox')).toBe('0 0 24 24')
    expect(svg.attributes('width')).toBe('20')
    expect(svg.attributes('height')).toBe('20')
    expect(svg.attributes('stroke-width')).toBe('1.8')
    expect(svg.attributes('stroke-linecap')).toBe('round')
    expect(svg.attributes('stroke-linejoin')).toBe('round')
    expect(porDefecto.find('path').attributes('d')).toBe(ICONOS.scan)

    const personalizado = mount(Icono, {
      props: { nombre: 'check', tamano: 14, grosor: 2.4 },
    })
    expect(personalizado.find('svg').attributes('width')).toBe('14')
    expect(personalizado.find('svg').attributes('stroke-width')).toBe('2.4')
    expect(personalizado.find('path').attributes('d')).toBe(ICONOS.check)

    const respaldo = mount(Icono, { props: { nombre: 'inexistente' } })
    expect(respaldo.find('path').attributes('d')).toBe(ICONOS.box)
  })

  it('clasifica zona(kg) según R-08 con pruebas en los límites 7 y 15 kg', () => {
    expect(zona(0)).toBe('verde')
    expect(zona(6.9)).toBe('verde')
    expect(zona(6.99)).toBe('verde')

    expect(zona(7)).toBe('naranja')
    expect(zona(7.01)).toBe('naranja')
    expect(zona(14.9)).toBe('naranja')
    expect(zona(14.99)).toBe('naranja')

    expect(zona(15)).toBe('roja')
    expect(zona(15.01)).toBe('roja')
    expect(zona(25)).toBe('roja')

    expect(zonas.roja.hex).toBe('#d13438')
    expect(zonas.naranja.hex).toBe('#f59e0b')
    expect(zonas.naranja.fg).toBe('#3a2300')
    expect(zonas.verde.hex).toBe('#16884a')
  })

  it('formatea pesos con formatoKg() en es-MX', () => {
    expect(formatoKg(1000)).toBe('1,000 kg')
    expect(formatoKg(567)).toBe('567 kg')
    expect(formatoKg(16.84)).toBe('16.8 kg')
  })

  it('dibuja CodigoQr real con el tamaño y colores del prototipo', () => {
    const wrapper = mount(CodigoQr, {
      props: { texto: 'EMB-0412', tamano: 74 },
    })
    const svg = wrapper.find('svg.qr')
    expect(svg.exists()).toBe(true)
    expect(svg.attributes('width')).toBe('74')
    expect(svg.attributes('height')).toBe('74')
    expect(svg.attributes('aria-label')).toBe('Código QR EMB-0412')
    expect(wrapper.find('rect[fill="#fff"]').exists()).toBe(true)
    expect(wrapper.find('g[fill="#0f1f3d"]').exists()).toBe(true)

    const m1 = generarMatrizQr('EMB-0412')
    const m2 = generarMatrizQr('B-01OC-26-1182RES-0500')
    expect(m1.length).toBe(25)
    // Patrones buscadores 7x7 en las 3 esquinas
    expect(m1[0][0]).toBe(true)
    expect(m1[0][6]).toBe(true)
    expect(m1[6][0]).toBe(true)
    expect(m1[1][1]).toBe(false)
    expect(m1[2][2]).toBe(true)
    expect(m1).not.toEqual(m2)
  })
})
