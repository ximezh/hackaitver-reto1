# Avisos para back

Buzón de Jesus y su agente. Cómo funciona: [AVISOS.md](AVISOS.md).

## Pendientes

### AV-DO-009 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** el CEDIS está en la Ciudad de México, no en Veracruz (issue #13). `docs/scrum.md` ya lo dice en el alcance y en S-06.
- **Qué tienes que hacer:** si algún texto, semilla, contrato o mensaje nombra la ubicación del CEDIS, cambiarlo a CDMX. La zona horaria `America/Mexico_City` sigue igual y las sucursales de ejemplo no cambian. Comenta en el issue #13 si tuviste que cambiar algo.
- **Referencia:** issue #13.

### AV-DO-008 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** hay una prueba de contrato del sprint 1 contra el back real: salud, credenciales inválidas, canal incorrecto, login de Oficina, perfil, los cuatro catálogos, `403 sin_permiso` y `401 no_autenticado`. Hoy, contra `dev`, solo pasa la salud: las rutas de BE-10 a BE-14 responden `404 no_encontrado`.
- **Qué tienes que hacer:** cuando tengas BE-10 a BE-14, levanta el back con las semillas y corre desde `front/`: `API_REAL=http://localhost:8000 npx vitest run src/api/__tests__/contrato.real.spec.js`. Si algo no coincide con el contrato, avísalo aquí o en `AVISOS-devops.md`.
- **Referencia:** DO-14 · `front/src/api/__tests__/contrato.real.spec.js`.

### AV-DO-007 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** issues #5, #7 y #8 resueltos en `devops-feat/sprint1`: `ErrorApi` lee `campos`; el revisor de convenciones corre desde la rama base; `JWT_SECRET` está en los entornos de staging y producción y el despliegue se detiene si falta. La imagen del back corre tus migraciones 0001 y 0002 y las semillas con `--permitir-produccion`.
- **Qué tienes que hacer:** nada; los issues se cierran al llegar el PR a `main`. Si agregas otra variable obligatoria para producción, déjala en `AVISOS-devops.md` en el mismo commit: el compose de la instancia pasa las variables del back una por una.
- **Referencia:** commits `594a05a`, `6c0d432`, `9603f60` · `infra/compose.entorno.yaml`.

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
