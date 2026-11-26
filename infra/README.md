# Infraestructura

Lo mantiene DevOps. Todo corre en una instancia EC2 de AWS con Podman sin root (docs/scrum.md · A-14, A-15; issue #3).

## Entornos

| Entorno | Se publica desde | Dominio | Variables |
|---|---|---|---|
| Local | — | `http://localhost:5173` | `back/.env` (de `back/.env.example`) |
| Staging | `dev` | `https://staging.<dominio>` | [entornos/staging.env.example](entornos/staging.env.example) |
| Producción | `main` | `https://<dominio>` | [entornos/produccion.env.example](entornos/produccion.env.example) |

El dominio, la cuenta y la región de AWS quedan pendientes (supuesto S-05).

## Cómo está armada la instancia

```text
Internet ──► Caddy :80/:443 (compose.borde.yaml, HTTPS automático)
               ├─ <dominio>          ──► front-produccion ──► back ──► db  (proyecto reto1-produccion)
               └─ staging.<dominio>  ──► front-staging    ──► back ──► db  (proyecto reto1-staging)
```

| Archivo | Qué es |
|---|---|
| [aws/crear-instancia.sh](aws/crear-instancia.sh) | Crea la EC2 (Ubuntu 24.04, `t3.small`, disco cifrado de 30 GB), el grupo de seguridad y la IP fija |
| [aws/cloud-init.yaml](aws/cloud-init.yaml) | Instala Podman y `docker-compose`, crea el usuario `cedis` y deja los contenedores corriendo al reiniciar |
| [compose.borde.yaml](compose.borde.yaml) · [Caddyfile](Caddyfile) | Caddy: certificados de Let's Encrypt y un dominio por entorno |
| [compose.entorno.yaml](compose.entorno.yaml) | Un entorno: PostgreSQL 17 con volumen propio, back y front |
| `entornos/*.env.example` | Variables y secretos de cada entorno. Los `.env` reales solo viven en la instancia |

**Grupo de seguridad:** 80 y 443 abiertos; 22 solo desde la IP de administración. La instancia se actualiza sola consultando el repositorio (DO-13), así que GitHub no necesita entrar por SSH ni guardar secretos de AWS.

## Primera puesta en marcha

Requiere AWS CLI v2 con credenciales, un par de claves EC2 y el dominio.

```bash
# 1. Crear la instancia (genera costos en la cuenta)
REGION=<región> CLAVE=<par-de-claves> IP_ADMIN=<tu-ip> infra/aws/crear-instancia.sh

# 2. DNS: registros A de <dominio> y staging.<dominio> hacia la IP que imprime el script

# 3. En la instancia
ssh cedis@<ip>
cloud-init status --wait
git clone https://github.com/ximezh/hackaitver-reto1.git ~/reto1
cd ~/reto1/infra
cp entornos/borde.env.example entornos/borde.env            # DOMINIO
cp entornos/produccion.env.example entornos/produccion.env  # contraseñas largas y dominio
cp entornos/staging.env.example entornos/staging.env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"  # un JWT_SECRET distinto por entorno
chmod 600 entornos/*.env
podman compose -f compose.borde.yaml --env-file entornos/borde.env up -d
```

Los entornos los levanta el despliegue continuo.

**Datos de demostración en staging.** Staging corre con `APP_ENV=production`, así que las semillas (BE-03) solo cargan con una bandera explícita (issue #5). Una vez desplegado:

```bash
cd ~/reto1/infra
podman compose -p reto1-staging run --rm back python -m app.seeds --permitir-produccion
```

En producción no se cargan semillas.

## Despliegue continuo

`main` es producción y `dev` es staging (A-15). Nadie despliega a mano:

1. Un merge a `dev` o `main` corre el CI. Si pasa, el workflow [Publicar](../.github/workflows/publicar.yml) sube a GHCR las imágenes `ghcr.io/ximezh/hackaitver-reto1-back` y `-front` con la etiqueta `sha-<commit>`.
2. En la instancia, un timer corre [actualizar.sh](actualizar.sh) cada minuto por entorno. Si la rama avanzó y ya están sus imágenes, corre las migraciones, levanta la versión nueva y revisa `/api/health` a través de Nginx.
3. Si la versión nueva no responde, vuelve a levantar la anterior y no reintenta ese commit; el siguiente commit sí se intenta. Si el CI falló, las imágenes nunca se publican y el entorno no cambia.

Activarlo en la instancia, una sola vez:

```bash
mkdir -p ~/.config/systemd/user
ln -sf ~/reto1/infra/systemd/reto1-actualizar@.service ~/reto1/infra/systemd/reto1-actualizar@.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now reto1-actualizar@produccion.timer reto1-actualizar@staging.timer
journalctl --user -u 'reto1-actualizar@*' -f     # ver los despliegues
```

- La primera vez que se publica, GHCR crea los paquetes como privados. Hay que marcarlos como públicos en GitHub (Packages → configuración del paquete), igual que el repositorio, para que la instancia los descargue sin credenciales.
- Las migraciones no se revierten al volver a la versión anterior: cada migración debe ser compatible con la versión previa del back.
- El script y el `Caddyfile` se leen del clon en `~/reto1`; para actualizarlos: `git -C ~/reto1 pull`.

## Probar en local

La misma configuración corre en una laptop con Podman, con `DOMINIO=localhost` y puertos altos:

```bash
cd infra
DOMINIO=localhost PUERTO_HTTP=8088 PUERTO_HTTPS=8443 podman compose -f compose.borde.yaml up -d
podman compose -f compose.entorno.yaml --env-file entornos/produccion.env up -d
curl -k https://localhost:8443/api/health
```

## CORS

El front llama siempre a `/api` en su mismo origen:

- **Local:** Vite reenvía `/api` al back (`VITE_API_PROXY`). Desde un teléfono en la misma red, `npm run dev -- --host` sigue pasando por el proxy.
- **Staging y producción:** Caddy entrega el dominio al Nginx del front, que reenvía `/api` al back del mismo entorno.

Por eso el navegador no hace peticiones de otro origen y CORS no interviene en el uso normal. `CORS_ORIGINS` solo admite el dominio propio de cada entorno; en local admite `http://localhost:5173` para pruebas directas contra `http://localhost:8000`.

`CORS_ORIGINS` es una lista en formato JSON: `["https://uno", "https://dos"]`.
