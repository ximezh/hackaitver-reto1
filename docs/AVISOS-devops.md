# Avisos para DevOps

Buzón de Luis Daniel y su agente. Cómo funciona: [AVISOS.md](AVISOS.md).

## Pendientes

### AV-BE-003 · 2026-11-25 · de back · Pendiente
- **Qué cambió:** el back del sprint 2 (BE-20 a BE-24) quedó en `back-feat/sprint2`, y está publicado el contrato del sprint 3 en `docs/api/sprint-3.md`: caseta (`GET /api/caseta/hoy`, check-in y check-out), QR de la cita, recepción por escaneo, incidencias y detalle de bulto. El contrato del sprint 2 sumó `422` «Ese horario ya pasó» en `POST /api/citas`.
- **Qué tienes que hacer:** crear los servicios y mocks del sprint 3 con ese contrato. Dependencias nuevas del back (Python puro, sin paquetes de sistema): `segno`, `fpdf2` (trae `pillow` y `fonttools`) y, solo en desarrollo, `pypdf`. Migraciones `0004` a `0006`; la `0005` crea la extensión `btree_gist`, que la imagen `postgres:17` ya trae. El back lee sus fuentes de `app/etiquetas/fuentes/`, dentro de `app/`.
- **Referencia:** BE-20 a BE-25 · `docs/api/sprint-2.md` · `docs/api/sprint-3.md`.

### AV-BE-002 · 2026-11-25 · de back · Pendiente
- **Qué cambió:** está publicado el contrato del sprint 2 en `docs/api/sprint-2.md`: pedidos de sucursal, órdenes del proveedor, disponibilidad y citas por andén, verificación del folio, facturas por bulto, QR en SVG y etiquetas en PDF. Sucursal ahora también puede leer `GET /api/productos` (solo activos).
- **Qué tienes que hacer:** crear los servicios y mocks de DO-20 con ese contrato. Para DO-21: los PDF llegan con `Content-Disposition: attachment; filename="B-0003.pdf"` o `"FAC-A-20418-etiquetas.pdf"`, y `qr.svg` también pide `Authorization`, así que se descarga como `blob`.
- **Referencia:** BE-16 · `docs/api/sprint-2.md`.

### AV-BE-001 · 2026-11-25 · de back · Pendiente
- **Qué cambió:** el back del sprint 1 (BE-10 a BE-15) quedó en `back-feat/sprint1` y tu prueba de contrato pasa contra él (7 de 7). El contrato del sprint 1 sumó errores (ningún `code` ni campo existente cambió):
  - Productos: `422` «El peso no puede pasar de 1,000 kg, la capacidad de una tarima», «El volumen no puede pasar de 2.576 m³, la capacidad de una tarima», «El SKU no es válido» y «La ilustración no es válida».
  - Usuarios: `409 no_puedes_cambiar_tu_rol` «No puedes cambiar tu propio rol» y `422` «El usuario admite de 3 a 40 letras, números, punto, guion o guion bajo».
  - Generales (README): `405 metodo_no_permitido` y `409 conflicto`.
  - La migración `0003` crea la extensión `unaccent` (búsqueda sin acentos). La imagen oficial `postgres:17` ya la trae; `alembic upgrade head` la aplica.
- **Qué tienes que hacer:** agregar esos casos a los mocks si los quieres reflejar. No hay variables de entorno nuevas además de `JWT_SECRET` (#8).
- **Referencia:** BE-11, BE-14 · `docs/api/sprint-1.md` · `docs/api/README.md`.

## Atendidos

### Issues #5, #7 y #8 · 2026-11-25 · de back · Atendido
- **Qué cambió:** `campos` en los errores de validación (#5), revisor de convenciones en ramas viejas (#7) y `JWT_SECRET` obligatorio en producción (#8).
- **Cómo se atendió:** commits `594a05a`, `9603f60` y `6c0d432` en `devops-feat/sprint1`; respuesta en cada issue.

### Issue #3 · 2026-11-25 · de back · Atendido
- **Qué cambió:** el CI de back necesita PostgreSQL y `TEST_DATABASE_URL`, y en local se usa solo Podman.
- **Cómo se atendió:** DO-01 y cierre del sprint 0 de DevOps (PR #4).
