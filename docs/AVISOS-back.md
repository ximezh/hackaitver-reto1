# Avisos para back

Buzón de Jesus y su agente. Cómo funciona: [AVISOS.md](AVISOS.md).

## Pendientes

### AV-DO-005 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** los servicios del front siguen el contrato del sprint 1 tal como está en `back-chore/sprint0`: errores `{ detail, code, campos }`, `401 no_autenticado` y `token_expirado` regresan al login, `401 credenciales_invalidas` no, y `403 cambio_contrasena_requerido` lleva al cambio de contraseña.
- **Qué tienes que hacer:** si cambia algún `code`, ruta o campo del contrato, deja un aviso en `AVISOS-devops.md` en el mismo commit para ajustar los servicios y mocks.
- **Referencia:** DO-10 · `front/src/api/` · `docs/api/sprint-1.md`.

### AV-DO-004 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** el job de back del CI levanta `postgres:17`, crea `reto1_test` y define `TEST_DATABASE_URL` y `DATABASE_URL` (issue #3). La imagen del back (`back/Dockerfile`, de DevOps) copia solo `app/`, `migrations/` y `alembic.ini`, sin `tests/` ni dependencias de desarrollo.
- **Qué tienes que hacer:** si el back necesita en producción otra carpeta o archivo fuera de `app/` y `migrations/`, o una dependencia de sistema, déjalo en `AVISOS-devops.md`. Las semillas dentro de `app/` ya entran a la imagen.
- **Referencia:** DO-01, DO-05 · PR #4.

## Atendidos

Ninguno todavía.
