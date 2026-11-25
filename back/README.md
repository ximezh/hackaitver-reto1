# Back · CEDIS Flow

API en FastAPI sobre PostgreSQL 17. Plan del área: [docs/scrum/back.md](../docs/scrum/back.md). Contratos: [docs/api/](../docs/api/).

## Base de datos

`compose.yaml`, en la raíz, levanta un PostgreSQL 17 con dos bases:

| Base | Uso | Variable |
|---|---|---|
| `reto1` | Desarrollo: la API y las semillas | `DATABASE_URL` |
| `reto1_test` | Solo pytest: se migra al inicio de cada corrida | `TEST_DATABASE_URL` |

Usuario y contraseña `reto1`, puerto `5432`. Se cambian con `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_PORT`.

### Con Podman

```bash
podman machine init      # solo la primera vez (Windows y macOS)
podman machine start
podman compose up -d
```

`podman compose` usa por dentro `docker-compose` o `podman-compose`, el que esté instalado.

### Con Docker

```bash
docker compose up -d
```

### Comandos útiles

| Tarea | Podman | Docker |
|---|---|---|
| Ver si está lista | `podman compose ps` | `docker compose ps` |
| Abrir `psql` | `podman compose exec db psql -U reto1 reto1` | `docker compose exec db psql -U reto1 reto1` |
| Detener | `podman compose down` | `docker compose down` |
| Borrar los datos | `podman compose down -v` | `docker compose down -v` |

### Si ya tenías el volumen antes de `reto1_test`

`back/db/init/` solo corre cuando el volumen está vacío. Si la base se creó antes, crea la de pruebas una vez:

```bash
podman compose exec db createdb -U reto1 reto1_test   # o: docker compose exec …
```

## Puesta en marcha

```bash
cd back
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

## Pruebas

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest
```

- Las pruebas corren contra PostgreSQL real, nunca contra la base de desarrollo.
- Antes de empezar, `tests/conftest.py`:
  1. Lee `TEST_DATABASE_URL` del entorno o de `back/.env`. Si falta, o si apunta a la misma base que `DATABASE_URL`, se detiene con un mensaje que dice qué corregir.
  2. Apunta la app y Alembic a esa base.
  3. Aplica la última migración (`alembic upgrade head`).
- Si la base no responde, el mensaje pide levantarla con `podman compose up -d`.
