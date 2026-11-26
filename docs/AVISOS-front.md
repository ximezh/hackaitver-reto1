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

### AV-BE-001 · 2026-11-25 · de back · Pendiente
- **Qué cambió:** el contrato del sprint 1 sumó mensajes de error: productos con más de 1,000 kg o 2.576 m³ (capacidad de una tarima, R-09), SKU o ilustración inválidos, `409 no_puedes_cambiar_tu_rol` cuando Oficina cambia su propio rol, y el formato del usuario. Ningún `code` ni campo existente cambió.
- **Qué tienes que hacer:** nada si muestras `error.message` y `error.campos` tal cual (AV-DO-002).
- **Referencia:** BE-11, BE-14 · `docs/api/sprint-1.md`.

### AV-DO-006 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** están listos los servicios de Oficina en `@/api`: `productos`, `proveedores`, `sucursales` y `usuarios`, cada uno con `listar({ q })`, `obtener(id)`, `crear(datos)`, `editar(id, cambios)` y `eliminar(id)`; `usuarios.restablecer(id)`; `ROLES` y `ESTADOS` con etiqueta y chip; y `obtenerIndicadoresOficina()` con los valores del prototipo hasta BE-44. Los mocks aplican las reglas y textos del contrato del sprint 1.
- **Qué tienes que hacer:** en FE-12 y FE-13, mostrar «Registro eliminado» tanto si `eliminar` responde `eliminado` como `desactivado`; mostrar `contrasena_generada` una sola vez al crear o restablecer un usuario; y usar `ROLES` para el rol. El formulario de Usuarios necesita un selector de sucursal o proveedor que el prototipo no dibuja (pregunta C1-04 del contrato): Ximena define cómo se ve.
- **Referencia:** DO-11 · `front/src/api/catalogos.js` · `front/src/api/indicadores.js`.

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
