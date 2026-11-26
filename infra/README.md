# Infraestructura

Lo mantiene DevOps. CEDIS Flow corre en una instancia EC2 de AWS con Podman sin root (docs/scrum.md · A-14, A-15; issue #3).

## Entornos

| Entorno | Se publica desde | URL | Variables |
|---|---|---|---|
| Local | — | `http://localhost:5173` | `back/.env` (de `back/.env.example`) |
| Staging | `dev` | <https://staging.cedis.13-184-89-164.sslip.io> | [entornos/staging.env.example](entornos/staging.env.example) |
| Producción | `main` | <https://cedis.13-184-89-164.sslip.io> | [entornos/produccion.env.example](entornos/produccion.env.example) |

Los dominios usan [sslip.io](https://sslip.io): resuelven a la IP de la instancia sin comprar dominio (supuesto S-05). Si se cambia de instancia o se compra un dominio, se cambian en [caddy/cedis.caddy](caddy/cedis.caddy) y en `CORS_ORIGINS` de cada entorno.

## Cómo está armada la instancia

La instancia `13.184.89.164` (`us-east-2`) es **compartida con otros proyectos** (Tickets y SEVA). CEDIS Flow no toca sus servicios, contenedores ni puertos: corre con su propio usuario y solo agrega un `import` al Caddy del sistema.

```text
Internet ──► Caddy del sistema :80/:443 (HTTPS automático, compartido)
               ├─ cedis.…sslip.io          ──► 127.0.0.1:8180 front ──► back ──► db  (reto1-produccion)
               ├─ staging.cedis.…sslip.io  ──► 127.0.0.1:8181 front ──► back ──► db  (reto1-staging)
               └─ otros proyectos (sin cambios)
```

| Archivo | Qué es |
|---|---|
| [preparar-instancia.sh](preparar-instancia.sh) | Prepara la instancia, dedicada o compartida: Podman, Caddy, usuario `cedis`, clon del repositorio, secretos, Caddy y timers. Idempotente |
| [caddy/cedis.caddy](caddy/cedis.caddy) | Los dos dominios de CEDIS Flow para el Caddy del sistema |
| [compose.entorno.yaml](compose.entorno.yaml) | Un entorno: PostgreSQL 17 con volumen propio, back y front en `127.0.0.1:PUERTO_FRONT` |
| [actualizar.sh](actualizar.sh) · [systemd/](systemd/) | Despliegue continuo de cada entorno |
| `entornos/*.env.example` | Variables de cada entorno. Los `.env` reales, con secretos, solo viven en la instancia |
| [aws/crear-instancia.sh](aws/crear-instancia.sh) · [aws/cloud-init.yaml](aws/cloud-init.yaml) | Solo para crear una instancia **dedicada** nueva; la actual ya existe |

## Primera puesta en marcha

En la instancia, con el usuario `ubuntu` (tiene sudo):

```bash
curl -fsSL https://raw.githubusercontent.com/ximezh/hackaitver-reto1/dev/infra/preparar-instancia.sh | ACTIVAR=1 bash
```

El script:

1. Instala lo que falte: Podman, Caddy y `docker-compose`, que es el proveedor de `podman compose`.
2. Crea el usuario `cedis` con Podman sin root, sin depender del Docker de otros proyectos.
3. Clona el repositorio en `/home/cedis/reto1`.
4. Genera `entornos/produccion.env` y `staging.env` con contraseña de base y `JWT_SECRET` aleatorios y distintos (issue #8).
5. Respalda `/etc/caddy/Caddyfile`, agrega `import /etc/caddy/cedis.caddy`, valida y recarga Caddy sin cortar los otros sitios. Si la validación falla, restaura el respaldo.
6. Activa los timers de despliegue (`ACTIVAR=1`).

**Datos de demostración.** Los entornos corren con `APP_ENV=production`, así que las semillas (BE-03) solo cargan con una bandera explícita (issue #5). Se cargan con una contraseña propia de la instancia, no la de desarrollo:

```bash
sudo -iu cedis
cd ~/reto1/infra
openssl rand -base64 18 > entornos/demo-staging.txt && chmod 600 entornos/demo-staging.txt
podman compose -p reto1-staging run --rm back python -m app.seeds --permitir-produccion --contrasena "$(cat entornos/demo-staging.txt)"
```

## Despliegue continuo

`main` es producción y `dev` es staging (A-15). Nadie despliega a mano:

1. Un merge a `dev` o `main` corre el CI. Si pasa, el job «Publicar imágenes» de [ci.yml](../.github/workflows/ci.yml) sube a GHCR las imágenes `ghcr.io/ximezh/hackaitver-reto1-back` y `-front` con la etiqueta `sha-<commit>`. Los paquetes son públicos, como el repositorio.
2. En la instancia, un timer corre [actualizar.sh](actualizar.sh) cada minuto por entorno. Si la rama avanzó y ya están sus imágenes, corre las migraciones, levanta la versión nueva y revisa `/api/health` a través de Nginx.
3. Si la versión nueva no responde, vuelve a levantar la anterior y no reintenta ese commit; el siguiente commit sí se intenta. Si el CI falló, las imágenes nunca se publican y el entorno no cambia.

```bash
sudo -iu cedis
systemctl --user list-timers 'reto1-*'
journalctl --user -u 'reto1-actualizar@*' -f        # ver los despliegues
cat ~/.local/state/reto1/staging/desplegado          # commit en staging
```

- Las migraciones no se revierten al volver a la versión anterior: cada migración debe ser compatible con la versión previa del back.
- El script y `cedis.caddy` se leen del clon en `~/reto1`; para actualizarlos: `git -C ~/reto1 pull` y, si cambió `cedis.caddy`, volver a correr `preparar-instancia.sh`.

## Probar en local

La misma configuración corre en una laptop con Podman:

```bash
cd infra
cp entornos/produccion.env.example entornos/produccion.env   # y llenar secretos
podman compose -f compose.entorno.yaml --env-file entornos/produccion.env up -d
curl http://127.0.0.1:8180/api/health
```

## CORS

El front llama siempre a `/api` en su mismo origen:

- **Local:** Vite reenvía `/api` al back (`VITE_API_PROXY`). Desde un teléfono en la misma red, `npm run dev -- --host` sigue pasando por el proxy.
- **Staging y producción:** Caddy entrega el dominio al Nginx del front, que reenvía `/api` al back del mismo entorno.

Por eso el navegador no hace peticiones de otro origen y CORS no interviene en el uso normal. `CORS_ORIGINS` solo admite el dominio propio de cada entorno; en local admite `http://localhost:5173` para pruebas directas contra `http://localhost:8000`.

`CORS_ORIGINS` es una lista en formato JSON: `["https://uno", "https://dos"]`.
