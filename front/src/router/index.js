import { createRouter, createWebHistory } from 'vue-router'
import { haySesion } from '@/api'
import LayoutMovil from '@/layouts/LayoutMovil.vue'
import LayoutWeb from '@/layouts/LayoutWeb.vue'
import { obtenerRutaInicioRol, useSesionStore } from '@/stores/sesion'

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
      component: () => import('../views/LoginWebView.vue'),
    },
    {
      path: '/movil/login',
      name: 'movil-login',
      meta: { publica: true, canal: 'android' },
      component: () => import('../views/LoginMovilView.vue'),
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
          component: () => import('../views/PortalMovilView.vue'),
        },
        {
          path: 'desembarque',
          name: 'movil-desembarque',
          meta: { rol: 'desembarque', canal: 'android' },
          component: () => import('../views/PortalMovilView.vue'),
        },
        {
          path: 'embarque',
          name: 'movil-embarque',
          meta: { rol: 'embarque', canal: 'android' },
          component: () => import('../views/PortalMovilView.vue'),
        },
        {
          path: ':ruta(.*)*',
          name: 'movil',
          meta: { canal: 'android' },
          component: () => import('../views/PortalMovilView.vue'),
        },
      ],
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
          component: () => import('../views/OficinaView.vue'),
        },
        {
          path: 'sucursal',
          name: 'web-sucursal',
          meta: { rol: 'sucursal', canal: 'web' },
          component: () => import('../views/PortalWebView.vue'),
        },
        {
          path: 'proveedor',
          name: 'web-proveedor',
          meta: { rol: 'proveedor', canal: 'web' },
          component: () => import('../views/PortalWebView.vue'),
        },
        {
          path: ':ruta(.*)*',
          name: 'web',
          meta: { canal: 'web' },
          component: () => import('../views/PortalWebView.vue'),
        },
      ],
    },
    ...(esDev
      ? [
          {
            path: '/elementos',
            name: 'elementos',
            meta: { publica: true },
            component: () => import('../views/ElementosView.vue'),
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
