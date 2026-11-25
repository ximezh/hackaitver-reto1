import process from 'node:process'
import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// Lee `front/.env` (y `.env.local`) para el destino del proxy.
const env = loadEnv('', process.cwd())

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // En desarrollo, las llamadas a /api van a FastAPI sin problemas de CORS.
    proxy: {
      '/api': env.VITE_API_PROXY || 'http://localhost:8000',
    },
  },
})
