# Avisos para front

Buzón de Ximena y su agente. Cómo funciona: [AVISOS.md](AVISOS.md).

## Pendientes

Ninguno todavía.

## Atendidos

### AV-DO-006 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** están listos los servicios de Oficina en `@/api`: `productos`, `proveedores`, `sucursales` y `usuarios`, cada uno con `listar({ q })`, `obtener(id)`, `crear(datos)`, `editar(id, cambios)` y `eliminar(id)`; `usuarios.restablecer(id)`; `ROLES` y `ESTADOS` con etiqueta y chip; y `obtenerIndicadoresOficina()` con los valores del prototipo hasta BE-44. Los mocks aplican las reglas y textos del contrato del sprint 1.
- **Cómo se atendió:** en FE-12 y FE-13 (`OficinaView.vue`) se consumen `obtenerIndicadoresOficina()`, `productos`, `proveedores`, `sucursales`, `usuarios`, `ROLES` y `ESTADOS`, se muestra «Registro eliminado» tanto en eliminación como en desactivación, se incorporaron los selectores de `ROLES` y de `Sucursal` / `Proveedor` en la cuadrícula `grid2` del modal (C1-04) y el modal de confirmación de `contrasena_generada`.
- **Referencia:** DO-11, FE-12, FE-13 · `front/src/views/OficinaView.vue`.

### AV-DO-003 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** están listos los servicios de sesión en `@/api`: `iniciarSesion({ usuario, contrasena, canal, recordar })`, `obtenerPerfil()`, `cambiarContrasena({ actual, nueva })`, `cerrarSesion()` y `haySesion()`, con la forma del contrato del sprint 1. El token se guarda solo; «Recordarme» decide si dura al cerrar el navegador.
- **Cómo se atendió:** en FE-10 (`LoginWebView.vue`), FE-11 (`LoginMovilView.vue`, con «Probar como» rellenando `cedis2026` fuera de producción) y FE-14 (`front/src/stores/sesion.js`, configurando `configurarHttp({ alNoAutorizado, alCambioContrasena })`).
- **Referencia:** DO-10, FE-10, FE-11, FE-14 · `front/src/stores/sesion.js`.

### AV-DO-002 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** las vistas y stores consumen la API solo con `import { … } from '@/api'`. Axios ya está en `front/package.json` (excepción del sprint 0). Con `VITE_API_MOCK=true` en `front/.env` la app responde con mocks sin back. Los errores llegan como `ErrorApi` con `estado`, `codigo`, `message` y `campos`.
- **Cómo se atendió:** todas las vistas y stores consumen exclusivamente `@/api`, mostrando `error.message` en el aviso y `error.campos[nombre]` junto a cada campo en `OficinaView.vue`.
- **Referencia:** DO-03, FE-10…14.

### AV-DO-001 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** cada PR corre los checks `ci` y `convenciones`. Una rama de front solo puede editar los archivos de front (no `front/src/api/`, `front/vite.config.js`, `front/.env.example` ni `Dockerfile`), y los commits llevan `(front)` o `(scrum)` como alcance. El visor del prototipo corre con `cd tools/prototipo && npm run prototipo` en <http://localhost:5180>.
- **Cómo se atendió:** aplicado en `front-chore/sprint0` (PR #10) y `front-feat/sprint1`.
- **Referencia:** DO-01, DO-02, DO-06 · PR #4, PR #10.
