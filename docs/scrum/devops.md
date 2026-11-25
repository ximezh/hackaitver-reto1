# Plan Scrum · DevOps

**Responsable:** Luis Daniel Morales y su agente
**Abarca:** cliente Axios, conexión front ↔ back, CORS, CI/CD, despliegue e instancia en AWS
**IDs:** `DO-NN` · **Épicas:** `DO-E1…` · **Ramas:** `devops-<tipo>/sprint<N>` · **Commits:** `tipo(devops): …`

Reglas generales, hallazgos, preguntas, DoR y DoD: [docs/scrum.md](../scrum.md).

## Reglas de esta área

- Los servicios de `front/src/api/` siguen el contrato de `docs/api/`. Cada servicio tiene su mock con los datos del prototipo, activado con `VITE_API_MOCK=true`.
- Al inicio de cada sprint, los servicios y mocks del sprint se entregan primero, para que front no se detenga.
- Los secretos viven en GitHub Actions y en AWS, nunca en el repositorio.
- Archivos propios: `front/src/api/`, `front/vite.config.js`, `front/.env.example`, `.github/`, `infra/`, `tools/` y los `Dockerfile`.

## Épicas

| Épica | Nombre | Historias |
|---|---|---|
| DO-E1 | Automatización del equipo | DO-01…06 |
| DO-E2 | Conexión y ambiente en AWS | DO-10…14 |
| DO-E3 | Servicios y calidad visual | DO-20…23 |
| DO-E4 | Operación en bodega | DO-30…33 |
| DO-E5 | Producción | DO-40…43 |
| DO-E6 | Complementos y monitoreo | DO-50…51 |

---

## Sprint 0 · Automatización del equipo

**Objetivo:** que cada PR se revise solo y que front tenga cliente HTTP y visor del prototipo.
**Rama:** `devops-ci/sprint0` · **Puntos:** 20

### DO-01 · CI de front y back · 5 pts
Como equipo queremos que cada PR corra lint, pruebas y build para no integrar código roto.
- GitHub Actions con filtros por ruta: `front/**` corre lint, pruebas y build; `back/**` corre Ruff y pytest con un servicio de PostgreSQL.
- Los checks son obligatorios para hacer merge a `dev` y `main`.

### DO-02 · Reglas de ramas y PR · 3 pts
Como equipo queremos que las ramas y PR sigan la convención sin revisarlo a mano.
- Check que valida el nombre de rama `^(front|back|devops)-(feat|fix|test|docs|refactor|style|chore|ci)/sprint[0-9]+$` y el título del PR con Conventional Commits.
- Plantilla de PR con Tareas, Qué cambia, Cómo probarlo y Pendientes.
- `CODEOWNERS` según la tabla de propiedad de archivos (necesita S-04).
- Etiquetas `front`, `back`, `devops` para issues entre áreas.

### DO-03 · Cliente Axios con modo mock · 5 pts
Como front quiero un cliente HTTP listo para consumir la API sin preocuparme por tokens ni errores.
- `front/src/api/http.js`: base `/api`, tiempo de espera, token en cada petición, 401 → login, errores con la forma de BE-04.
- `VITE_API_MOCK=true` responde con mocks sin red.
- Pruebas con Vitest.

### DO-04 · CORS y variables por entorno · 2 pts
- `CORS_ORIGINS` definido para local, staging y producción.
- Documentado en el README; `.env.example` actualizados en front.

### DO-05 · Imágenes de contenedor · 3 pts
- `Dockerfile` del back con uv y Uvicorn; `Dockerfile` del front con build de Vite y Nginx que reenvía `/api`.
- Construyen en CI.

### DO-06 · Visor local del prototipo · 2 pts
Como equipo queremos ver el prototipo en el navegador para comparar cada pantalla (H-16).
- `tools/prototipo/` sirve los `preview.html` inyectando `tokens.css`, `bundle.css` y `bundle.js` y resolviendo `/_blob/<id>` a `assets/Ilustraciones/`, usando `manifest.json`.
- No modifica nada dentro de `design/`.
- Un comando: `npm run prototipo` desde `tools/prototipo/`.

---

## Sprint 1 · Conexión y AWS

**Objetivo:** login y catálogos conectados de punta a punta, en producción desde `main` y en staging desde `dev`, con HTTPS.
**Rama:** `devops-feat/sprint1` · **Puntos:** 21

### DO-10 · Servicios de sesión · 3 pts
- `api/auth.js` con login, `me` y salir; la sesión se guarda según «Recordarme».
- Mocks de los 6 roles del prototipo.

### DO-11 · Servicios de catálogos · 3 pts
- `api/productos`, `proveedores`, `sucursales`, `usuarios` e indicadores de Oficina con sus mocks.

### DO-12 · Instancia en AWS · 8 pts
Como equipo queremos un servidor en AWS con HTTPS para probar en teléfonos reales.
- Todo dentro de una instancia EC2 (P-09, A-14): contenedores para front, back y PostgreSQL, con volumen persistente.
- Producción y staging en la misma instancia, cada uno con su base y su subdominio.
- Dominio y HTTPS en los dos (requisito de la cámara, A-13).
- Grupos de seguridad mínimos; secretos fuera del repositorio.
- Infraestructura documentada en `infra/`.

### DO-13 · Despliegue continuo · 5 pts
Como equipo queremos que la instancia se actualice sola para que el producto funcione siempre desde `main` (P-12, A-15).
- Merge a `main` despliega a producción; merge a `dev` despliega a staging. Ambos corren las migraciones.
- Solo despliega si el CI pasó.
- Si el despliegue falla, la versión anterior sigue en servicio.

### DO-14 · Conexión de punta a punta · 2 pts
- Con `VITE_API_MOCK=false`, el login y los catálogos funcionan en staging y en producción contra el back real, desde un teléfono.

---

## Sprint 2 · Servicios y calidad visual

**Objetivo:** servicios del pedido y la cita, PDF desde el front y comparación visual automática.
**Rama:** `devops-feat/sprint2` · **Puntos:** 18

### DO-20 · Servicios de pedidos, citas y facturas · 5 pts
- Servicios y mocks del contrato del sprint 2.

### DO-21 · Descarga de PDF · 2 pts
- Ayuda para descargar etiquetas y relación como archivo con su nombre (`EMB-0412.pdf`).

### DO-22 · Comparación visual contra el prototipo · 8 pts
Como equipo queremos detectar en CI si una pantalla se aleja del prototipo.
- Playwright toma capturas de cada pantalla del front con datos mock y del visor (DO-06) en el mismo tamaño.
- El check falla si la diferencia supera el umbral acordado y deja las imágenes como artefacto.

### DO-23 · Respaldos de la base · 3 pts
- `pg_dump` diario de producción en un volumen aparte dentro de la instancia (P-09), con retención de 7 días.
- Procedimiento de restauración probado en staging.

---

## Sprint 3 · Operación en bodega

**Objetivo:** servicios de caseta y recepción, actualización periódica y pruebas en tamaños de teléfono.
**Rama:** `devops-feat/sprint3` · **Puntos:** 19

### DO-30 · Servicios de caseta, recepción y bultos · 5 pts
- Servicios y mocks del contrato del sprint 3.

### DO-31 · Actualización periódica · 3 pts
- Composable de consulta cada 15 s (A-11) que se pausa con la pantalla oculta.

### DO-32 · Pruebas de punta a punta · 8 pts
- Playwright en staging: proveedor agenda → caseta registra la entrada → desembarque recibe y rechaza un excedente.

### DO-33 · Pruebas en tamaños de teléfono · 3 pts
- Playwright revisa las pantallas móviles en 360, 390 y 412 px de ancho (web responsiva, P-01) y falla si algo se desborda o se corta.

---

## Sprint 4 · Producción

**Objetivo:** el ciclo completo en producción en AWS.
**Rama:** `devops-feat/sprint4` · **Puntos:** 13

### DO-40 · Servicios de tarimas, embarques e indicadores · 5 pts
- Servicios y mocks del contrato del sprint 4.

### DO-41 · Versiones y vuelta atrás · 3 pts
- Cada despliegue a producción queda etiquetado con su versión.
- Un comando documentado vuelve a la versión anterior, incluida la imagen del back.

### DO-42 · Seguridad básica · 3 pts
- Límite de intentos en login, cabeceras de seguridad en Nginx y revisión de secretos.

### DO-43 · Manual de operación · 2 pts
- Cómo desplegar, restaurar un respaldo y revisar logs, en `infra/README.md`.

---

## Sprint 5 · Complementos y monitoreo

**Objetivo:** servicios de las pantallas nuevas y monitoreo de la instancia.
**Rama:** `devops-feat/sprint5` · **Puntos:** 8

### DO-50 · Servicios de complementos · 3 pts
- Servicios y mocks del contrato del sprint 5: recuperación de contraseña, avisos, búsqueda y pestañas móviles.

### DO-51 · Monitoreo y alertas · 5 pts
- Revisión de salud de producción cada minuto con `GET /api/health`.
- Alerta si la API o la base no responden, o si el disco de la instancia pasa del 80 %.

---

## Backlog de DevOps

| ID | Historia | Origen |
|---|---|---|
| — | Sin historias todavía | — |

## Avance

| Sprint | Estado | PR |
|---|---|---|
| 0 | Pendiente | — |
| 1 | Pendiente | — |
| 2 | Pendiente | — |
| 3 | Pendiente | — |
| 4 | Pendiente | — |
| 5 | Pendiente | — |
