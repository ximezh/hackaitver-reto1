# Avisos para front

Buzón de Ximena y su agente. Cómo funciona: [AVISOS.md](AVISOS.md).

## Pendientes

### AV-DO-003 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** están listos los servicios de sesión en `@/api`: `iniciarSesion({ usuario, contrasena, canal, recordar })`, `obtenerPerfil()`, `cambiarContrasena({ actual, nueva })`, `cerrarSesion()` y `haySesion()`, con la forma del contrato del sprint 1. El token se guarda solo; «Recordarme» decide si dura al cerrar el navegador.
- **Qué tienes que hacer:** en el store de sesión (FE-14), llamar una vez a `configurarHttp({ alNoAutorizado, alCambioContrasena })`: el primero regresa al login cuando la sesión vence y el segundo lleva al cambio de contraseña (R-17). En modo mock la contraseña de los usuarios de demostración es `cedis2026` (`caseta.rgomez` tiene la temporal `Tmp-7Kq2-xW9p`). El «Probar como» del prototipo rellena `••••••••`, que no entra: en desarrollo y staging conviene rellenar la contraseña de demostración.
- **Referencia:** DO-10 · `front/src/api/auth.js` · `front/src/api/mocks/datos.js`.

### AV-DO-002 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** las vistas y stores consumen la API solo con `import { … } from '@/api'`. Axios ya está en `front/package.json` (excepción del sprint 0). Con `VITE_API_MOCK=true` en `front/.env` la app responde con mocks sin back. Los errores llegan como `ErrorApi` con `estado`, `codigo`, `message` y `campos`.
- **Qué tienes que hacer:** decidir en pantalla con `error.codigo`, nunca con el texto; mostrar `error.message` tal cual y `error.campos[nombre]` junto a cada campo. Actualiza tu rama con `dev` antes de instalar dependencias para no chocar en `package-lock.json`.
- **Referencia:** DO-03 · `front/src/api/http.js` · `front/src/api/errores.js`.

### AV-DO-001 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** cada PR corre los checks `ci` y `convenciones`. Una rama de front solo puede editar los archivos de front (no `front/src/api/`, `front/vite.config.js`, `front/.env.example` ni `Dockerfile`), y los commits llevan `(front)` o `(scrum)` como alcance. El visor del prototipo corre con `cd tools/prototipo && npm run prototipo` en <http://localhost:5180>.
- **Qué tienes que hacer:** usar el visor para la comparación lado a lado que pide la DoD. Si necesitas algo de esos archivos, déjalo en el buzón de DevOps o abre un issue `devops`.
- **Referencia:** DO-01, DO-02, DO-06 · PR #4.

## Atendidos

Ninguno todavía.
