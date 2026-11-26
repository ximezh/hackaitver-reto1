import { existsSync } from 'node:fs'
import { describe, it, expect } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { mount, flushPromises } from '@vue/test-utils'
import App from '@/App.vue'
import { crearRutas } from '@/router'

describe('FE-05 · Limpieza del andamiaje y rutas', () => {
  it('elimina los componentes, íconos, vistas y store de ejemplo de Vue', () => {
    const eliminados = [
      'src/components/HelloWorld.vue',
      'src/components/TheWelcome.vue',
      'src/components/WelcomeItem.vue',
      'src/components/icons/IconCommunity.vue',
      'src/components/icons/IconDocumentation.vue',
      'src/components/icons/IconEcosystem.vue',
      'src/components/icons/IconSupport.vue',
      'src/components/icons/IconTooling.vue',
      'src/views/AboutView.vue',
      'src/views/HomeView.vue',
      'src/stores/counter.js',
    ]
    for (const archivo of eliminados) {
      expect(existsSync(archivo)).toBe(false)
    }
  })

  it('configura las rutas /login, /movil/login y los grupos /movil/* y /web/* con sus layouts', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: crearRutas({ esDev: true }),
    })

    await router.push('/login')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    })
    await flushPromises()
    expect(wrapper.find('.login-web-placeholder').exists()).toBe(true)

    await router.push('/movil/login')
    await flushPromises()
    expect(wrapper.find('.login-movil-placeholder').exists()).toBe(true)

    await router.push('/movil/caseta')
    await flushPromises()
    expect(wrapper.find('.screen.screen-movil').exists()).toBe(true)
    expect(wrapper.find('.portal-movil-placeholder').exists()).toBe(true)

    await router.push('/web/oficina')
    await flushPromises()
    expect(wrapper.find('.web.web-layout').exists()).toBe(true)
    expect(wrapper.find('.portal-web-placeholder').exists()).toBe(true)
  })
})
