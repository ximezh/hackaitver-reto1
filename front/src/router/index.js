import { createRouter, createWebHistory } from 'vue-router'
import { haySesion } from '@/api'
import LayoutMovil from '@/layouts/LayoutMovil.vue'
import LayoutWeb from '@/layouts/LayoutWeb.vue'
import { obtenerRutaInicioRol, useSesionStore } from '@/stores/sesion'
import ElementosView from '../views/ElementosView.vue'
import LoginMovilView from '../views/LoginMovilView.vue'
import LoginWebView from '../views/LoginWebView.vue'
import OficinaView from '../views/OficinaView.vue'
import PortalMovilView from '../views/PortalMovilView.vue'
import PortalWebView from '../views/PortalWebView.vue'
import ProveedorView from '../views/ProveedorView.vue'

export function crearRutas({ esDev = import.meta.env.DEV } = {}) {
  return [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      meta: { publica: true, canal: 'web' },
      component: LoginWebView,
    },
    {
      path: '/movil/login',
      name: 'movil-login',
      meta: { publica: true, canal: 'android' },
      component: LoginMovilView,
    },
    {
      path: '/movil',
      component: LayoutMovil,
      meta: { canal: 'android' },
      children: [
        {
          path: 'caseta',
          name: 'movil-caseta',
          meta: { rol: 'caseta', canal: 'android' },
          component: PortalMovilView,
        },
        {
          path: 'desembarque',
          name: 'movil-desembarque',
          meta: { rol: 'desembarque', canal: 'android' },
          component: PortalMovilView,
        },
        {
          path: 'embarque',
          name: 'movil-embarque',
          meta: { rol: 'embarque', canal: 'android' },
          component: PortalMovilView,
        },
        {
          path: ':ruta(.*)*',
          name: 'movil',
          meta: { canal: 'android' },
          component: PortalMovilView,
        },
      ],
    },
    {
      // Vista con layout web propio (barra lateral del proveedor), fuera de LayoutWeb.
      path: '/web/proveedor',
      name: 'web-proveedor',
      meta: { rol: 'proveedor', canal: 'web' },
      component: ProveedorView,
    },
    {
      path: '/web',
      component: LayoutWeb,
      meta: { canal: 'web' },
      children: [
        {
          path: 'oficina',
          name: 'web-oficina',
          meta: { rol: 'oficina', canal: 'web' },
          component: OficinaView,
        },
        {
          path: 'sucursal',
          name: 'web-sucursal',
          meta: { rol: 'sucursal', canal: 'web' },
          component: PortalWebView,
        },
        {
          path: ':ruta(.*)*',
          name: 'web',
          meta: { canal: 'web' },
          component: PortalWebView,
        },
      ],
    },
    ...(esDev
      ? [
          {
            path: '/elementos',
            name: 'elementos',
            meta: { publica: true },
            component: ElementosView,
          },
        ]
      : []),
  ]
}

export function configurarGuardas(instanciaRouter) {
  instanciaRouter.beforeEach(async (to) => {
    if (to.path === '/elementos') return true

    const sesion = useSesionStore()
    if (!sesion.usuario && haySesion()) {
      await sesion.cargarPerfil()
    }

    const esMovil = to.path.startsWith('/movil')
    if (!sesion.autenticado) {
      if (to.meta?.publica) return true
      return esMovil ? '/movil/login' : '/login'
    }

    const inicioRol = obtenerRutaInicioRol(sesion.rol)
    if (to.meta?.publica) {
      return inicioRol
    }

    const canalEsperado = esMovil ? 'android' : 'web'
    if (sesion.canal && sesion.canal !== canalEsperado) {
      return inicioRol
    }

    if (to.meta?.rol && to.meta.rol !== sesion.rol) {
      return inicioRol
    }

    return true
  })
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: crearRutas(),
})

configurarGuardas(router)

export default router
