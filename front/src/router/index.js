import { createRouter, createWebHistory } from 'vue-router'
import LayoutMovil from '@/layouts/LayoutMovil.vue'
import LayoutWeb from '@/layouts/LayoutWeb.vue'

export function crearRutas({ esDev = import.meta.env.DEV } = {}) {
  return [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginWebView.vue'),
    },
    {
      path: '/movil/login',
      name: 'movil-login',
      component: () => import('../views/LoginMovilView.vue'),
    },
    {
      path: '/movil',
      component: LayoutMovil,
      children: [
        {
          path: ':ruta(.*)*',
          name: 'movil',
          component: () => import('../views/PortalMovilView.vue'),
        },
      ],
    },
    {
      path: '/web',
      component: LayoutWeb,
      children: [
        {
          path: ':ruta(.*)*',
          name: 'web',
          component: () => import('../views/PortalWebView.vue'),
        },
      ],
    },
    ...(esDev
      ? [
          {
            path: '/elementos',
            name: 'elementos',
            component: () => import('../views/ElementosView.vue'),
          },
        ]
      : []),
  ]
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: crearRutas(),
})

export default router
