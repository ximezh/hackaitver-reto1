# Avisos para back

Buzón de Jesus y su agente. Cómo funciona: [AVISOS.md](AVISOS.md).

## Pendientes

Ninguno todavía.

## Atendidos

### AV-DO-008 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** hay una prueba de contrato del sprint 1 contra el back real: salud, credenciales inválidas, canal incorrecto, login de Oficina, perfil, los cuatro catálogos, `403 sin_permiso` y `401 no_autenticado`. Hoy, contra `dev`, solo pasa la salud: las rutas de BE-10 a BE-14 responden `404 no_encontrado`.
- **Cómo se atendió:** con BE-10 a BE-15 en `back-feat/sprint1`, las semillas cargadas y `API_REAL=http://localhost:8000`, `contrato.real.spec.js` pasa 7 de 7. Los errores que se sumaron al contrato están en AV-BE-001 de `AVISOS-devops.md`.

### AV-DO-007 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** issues #5, #7 y #8 resueltos en `devops-feat/sprint1`: `ErrorApi` lee `campos`; el revisor de convenciones corre desde la rama base; `JWT_SECRET` está en los entornos de staging y producción y el despliegue se detiene si falta. La imagen del back corre tus migraciones 0001 y 0002 y las semillas con `--permitir-produccion`.
- **Cómo se atendió:** el back lee `JWT_SECRET` y en producción no arranca si falta o tiene menos de 32 caracteres. El sprint 1 agrega la migración `0003` (extensión `unaccent`), que `alembic upgrade head` aplica sin pasos extra. No hay variables obligatorias nuevas.

### AV-DO-005 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** los servicios del front siguen el contrato del sprint 1 tal como está en `back-chore/sprint0`: errores `{ detail, code, campos }`, `401 no_autenticado` y `token_expirado` regresan al login, `401 credenciales_invalidas` no, y `403 cambio_contrasena_requerido` lleva al cambio de contraseña.
- **Cómo se atendió:** el back responde esos `code` tal cual. Ningún `code`, ruta ni campo existente cambió; los errores nuevos del sprint 1 se avisaron en AV-BE-001 de `AVISOS-devops.md`.

### AV-DO-004 · 2026-11-25 · de devops · Atendido
- **Qué cambió:** el job de back del CI levanta `postgres:17`, crea `reto1_test` y define `TEST_DATABASE_URL` y `DATABASE_URL` (issue #3). La imagen del back (`back/Dockerfile`, de DevOps) copia solo `app/`, `migrations/` y `alembic.ini`, sin `tests/` ni dependencias de desarrollo.
- **Cómo se atendió:** el back del sprint 1 solo usa `app/` y `migrations/`. Las dependencias nuevas (`pyjwt`, `argon2-cffi`, `tzdata`) son de Python y entran con `uv sync`; no hay dependencias de sistema.
