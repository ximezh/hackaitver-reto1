# Infraestructura

Lo mantiene DevOps. Todo corre en una instancia EC2 de AWS (docs/scrum.md · A-14, A-15).

## Entornos

| Entorno | Se publica desde | Dominio | Variables del back |
|---|---|---|---|
| Local | — | `http://localhost:5173` | `back/.env` (de `back/.env.example`) |
| Staging | `dev` | `https://staging.<dominio>` | [entornos/staging.env.example](entornos/staging.env.example) |
| Producción | `main` | `https://<dominio>` | [entornos/produccion.env.example](entornos/produccion.env.example) |

El dominio queda pendiente (supuesto S-05).

## CORS

El front llama siempre a `/api` en su mismo origen:

- **Local:** Vite reenvía `/api` al back (`VITE_API_PROXY`). Desde un teléfono en la misma red, `npm run dev -- --host` sigue pasando por el proxy.
- **Staging y producción:** Nginx sirve el front y reenvía `/api` al back en el mismo dominio.

Por eso el navegador no hace peticiones de otro origen y CORS no interviene en el uso normal. `CORS_ORIGINS` solo admite el dominio propio de cada entorno; en local admite `http://localhost:5173` para pruebas directas contra `http://localhost:8000`.

`CORS_ORIGINS` es una lista en formato JSON: `["https://uno", "https://dos"]`.
