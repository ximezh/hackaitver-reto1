import { readFileSync } from 'node:fs'
import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LayoutMovil from '@/layouts/LayoutMovil.vue'
import LayoutWeb from '@/layouts/LayoutWeb.vue'
import { useToast, DURACION_TOAST } from '@/composables/useToast'

const bundleCss = readFileSync('src/styles/bundle.css', 'utf8')

describe('FE-03 · Layouts móvil y web', () => {
  afterEach(() => {
    const { ocultar } = useToast()
    ocultar()
    vi.useRealTimers()
  })

  it('renderiza LayoutMovil con appbar, scroll, tabbar, fab, sheet y toast sin marco de teléfono ni 9:41', () => {
    const wrapper = mount(LayoutMovil, {
      props: {
        titulo: 'Caseta',
        subtitulo: 'Mié 25 nov · Turno 8:00–18:00',
        avatar: 'JL',
        mostrarCampana: true,
        mostrarFab: true,
        fabIcono: 'qr',
        sheetAbierto: true,
        tabActivo: 'inicio',
        tabs: [
          { id: 'inicio', icono: 'home', etiqueta: 'Inicio' },
          { id: 'citas', icono: 'calendar', etiqueta: 'Citas' },
          { id: 'historial', icono: 'history', etiqueta: 'Historial' },
          { id: 'perfil', icono: 'user', etiqueta: 'Perfil' },
        ],
      },
      slots: {
        default: '<div class="contenido-prueba">Lista de citas</div>',
        sheet: '<div class="hoja-prueba">Detalle check-in</div>',
      },
    })

    expect(wrapper.find('.phone').exists()).toBe(false)
    expect(wrapper.find('.sbar').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('9:41')

    expect(wrapper.find('.screen.screen-movil').exists()).toBe(true)
    expect(wrapper.find('.appbar h1').text()).toBe('Caseta')
    expect(wrapper.find('.appbar .sub').text()).toContain('Turno 8:00–18:00')
    expect(wrapper.find('.appbar .avatar').text()).toBe('JL')
    expect(wrapper.find('.scroll .contenido-prueba').text()).toBe('Lista de citas')
    expect(wrapper.find('button.fab').exists()).toBe(true)
    expect(wrapper.findAll('.tabbar button').length).toBe(4)
    expect(wrapper.find('.tabbar button.on').text()).toContain('Inicio')
    expect(wrapper.find('.sheet.open .grab').exists()).toBe(true)
    expect(wrapper.find('.sheet.open .hoja-prueba').text()).toBe('Detalle check-in')
    expect(wrapper.find('.toast').exists()).toBe(true)

    expect(bundleCss).toContain('.screen.screen-movil{min-height:100dvh;height:100dvh;width:100%')
  })

  it('adapta LayoutMovil al ancho del dispositivo en 360, 390 y 412 px', () => {
    for (const ancho of [360, 390, 412]) {
      window.innerWidth = ancho
      const wrapper = mount(LayoutMovil, {
        props: {
          titulo: 'OC-26-1182',
          sobretitulo: 'Andén R2 · Recibo',
          mostrarRegresar: true,
        },
      })
      const root = wrapper.find('.screen.screen-movil')
      expect(root.exists()).toBe(true)
      expect(wrapper.find('button[aria-label="Regresar"]').exists()).toBe(true)
    }
  })

  it('renderiza LayoutWeb con barra lateral de 232px, marca, navegación, usuario, encabezado y contenido', () => {
    expect(bundleCss).toContain('.side{width:232px;')

    const wrapper = mount(LayoutWeb, {
      props: {
        titulo: 'Productos',
        navActivo: 'productos',
        navItems: [
          { id: 'productos', icono: 'box', etiqueta: 'Productos', conteo: 7 },
          { id: 'proveedores', icono: 'factory', etiqueta: 'Proveedores', conteo: 4 },
        ],
        usuarioIniciales: 'AD',
        usuarioNombre: 'Ana Domínguez',
        usuarioRol: 'Oficina · Admin',
        placeholderBusqueda: 'Buscar producto o pedido',
      },
      slots: {
        default: '<div class="tabla-prueba">Catálogo</div>',
      },
    })

    expect(wrapper.find('.side .brand').text()).toContain('CEDIS Flow')
    expect(wrapper.findAll('.side .nav button').length).toBe(2)
    expect(wrapper.find('.side .nav button.on').text()).toContain('Productos')
    expect(wrapper.find('.side .avatar').text()).toBe('AD')
    expect(wrapper.find('.side').text()).toContain('Ana Domínguez')
    expect(wrapper.find('.side').text()).toContain('Oficina · Admin')
    expect(wrapper.find('.top h1').text()).toBe('Productos')
    expect(wrapper.find('.top input').attributes('placeholder')).toBe('Buscar producto o pedido')
    expect(wrapper.find('.top button[aria-label="Avisos"]').exists()).toBe(true)
    expect(wrapper.find('.content .tabla-prueba').text()).toBe('Catálogo')
  })

  it('muestra y oculta avisos con useToast tras 1.9 s (1900 ms)', () => {
    vi.useFakeTimers()
    const { visible, mensaje, icono, duracion, mostrar } = useToast()

    expect(DURACION_TOAST).toBe(1900)
    expect(duracion).toBe(1900)
    expect(visible.value).toBe(false)

    mostrar('Entrada VCZ-119-A · 09:00', 'check')
    expect(visible.value).toBe(true)
    expect(mensaje.value).toBe('Entrada VCZ-119-A · 09:00')
    expect(icono.value).toBe('check')

    vi.advanceTimersByTime(1899)
    expect(visible.value).toBe(true)

    vi.advanceTimersByTime(1)
    expect(visible.value).toBe(false)
  })
})
