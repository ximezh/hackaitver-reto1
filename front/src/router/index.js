import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

export function crearRutas({ esDev = import.meta.env.DEV } = {}) {
  return [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
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
