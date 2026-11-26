// Punto de entrada de la API para vistas y stores: `import { iniciarSesion } from '@/api'`.
export { configurarHttp, usaMocks } from './http.js'
export { ErrorApi } from './errores.js'
export { obtenerSalud } from './salud.js'
export { cambiarContrasena, cerrarSesion, haySesion, iniciarSesion, obtenerPerfil } from './auth.js'
