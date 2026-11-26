# Avisos para front

Buzón de Ximena y su agente. Cómo funciona: [AVISOS.md](AVISOS.md).

## Pendientes

### AV-DO-010 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** hay ruta crítica para la entrega (~45 min) al inicio de `docs/scrum.md`. Congelamiento de `dev` a los 30 minutos; después solo se corrigen errores que bloqueen la demo.
- **Qué tienes que hacer:** seguir tu columna de la tabla; usar los servicios de DO-20 en cuanto entren a `dev`; mientras tanto, mocks.
- **Referencia:** `docs/scrum.md` · Ruta crítica de la entrega.

### AV-BE-002 · 2026-11-25 · de back · Pendiente
- **Qué cambió:** está publicado el contrato del sprint 2 en `docs/api/sprint-2.md`, para FE-20 a FE-23: pasos del pedido (`paso` y `paso_indice`), `llega_estimado`, órdenes del proveedor con solo su parte, disponibilidad por andén con `propia`, verificación del folio (`GET /api/facturas/verificar`), factura con `bultos_esperados`, `totales`, `cuadra` y `diferencias`, y el texto del QR de cada bulto.
- **Qué tienes que hacer:** usar los textos del contrato, que son los del prototipo («Ese andén ya está ocupado», «Este folio ya está registrado», «El folio es obligatorio»). Hay criterios por defecto en las preguntas C2-01 a C2-05 del contrato; si Ximena quiere otro, avísalo en `AVISOS-back.md`.
- **Referencia:** BE-16 · `docs/api/sprint-2.md`.

## Atendidos

### AV-DO-009 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** el CEDIS está en la Ciudad de México, no en Veracruz (issue #13). El chip del login móvil dice **«CEDIS CDMX»**.
- **Cómo se atendió:** actualizado a «CEDIS CDMX» en `LoginMovilView.vue`, `fe11.spec.js` y `docs/scrum/front.md`.
- **Referencia:** issue #13 · FE-11.

### AV-BE-001 · 2026-11-25 · de back · Atendido
- **Qué cambió:** el contrato del sprint 1 sumó mensajes de error: productos con más de 1,000 kg o 2.576 m³ (capacidad de una tarima, R-09), SKU o ilustración inválidos, `409 no_puedes_cambiar_tu_rol` cuando Oficina cambia su propio rol, y el formato del usuario. Ningún `code` ni campo existente cambió.
- **Cómo se atendió:** `OficinaView.vue` muestra `error.message` y `error.campos` tal cual llegan desde `@/api`.
- **Referencia:** BE-11, BE-14, FE-13.

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
