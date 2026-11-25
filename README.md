# HackAITver · Reto 1

Aplicación web con front en Vue 3 y API en FastAPI sobre PostgreSQL.

## Stack

| Parte | Tecnología | Carpeta |
|---|---|---|
| Front | Vue 3 (JavaScript), Vite, Vue Router, Pinia, Vitest, ESLint + Oxlint, Prettier | [`front/`](front/) |
| Back | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, Pydantic Settings, pytest, Ruff | [`back/`](back/) |
| Base de datos | PostgreSQL 17 (Docker Compose) | [`compose.yaml`](compose.yaml) |

## Requisitos

- Node.js `^22.18` o `>=24.12` y npm
- [uv](https://docs.astral.sh/uv/) (instala Python 3.13 si hace falta)
- Docker con Docker Compose, o un PostgreSQL local

## Estructura

```text
.
├── back/            API FastAPI
│   ├── app/         código (config, db, routers, models)
│   ├── migrations/  migraciones de Alembic
│   └── tests/       pruebas con pytest
├── front/           aplicación Vue 3
│   └── src/
├── compose.yaml     PostgreSQL de desarrollo
└── README.md
```

## Puesta en marcha

### 1. Base de datos

```bash
docker compose up -d
```

Crea la base `reto1` con usuario y contraseña `reto1` en el puerto `5432`. Se pueden cambiar con `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_PORT`.

### 2. Back

```bash
cd back
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

- API: <http://localhost:8000>
- Documentación interactiva: <http://localhost:8000/docs>
- Salud: `GET /api/health` responde el estado de la API y de la conexión a PostgreSQL.

### 3. Front

```bash
cd front
cp .env.example .env
npm install
npm run dev
```

Abre <http://localhost:5173>. En desarrollo, Vite reenvía las rutas `/api` al back (`VITE_API_PROXY`).

## Variables de entorno

| Archivo | Variable | Uso |
|---|---|---|
| `back/.env` | `DATABASE_URL` | Conexión a PostgreSQL. Obligatoria. Acepta `postgres://` o `postgresql://`. |
| `back/.env` | `APP_ENV` | `development`, `test` o `production`. |
| `back/.env` | `CORS_ORIGINS` | Orígenes permitidos, en formato JSON. |
| `front/.env` | `VITE_API_PROXY` | Destino del proxy de `/api` en `npm run dev`. |
| `front/.env` | `VITE_API_MOCK` | `true` responde con los mocks de `src/api/mocks`, sin back. |

Los archivos `.env` no se versionan. Cada carpeta trae su `.env.example`. Las variables de staging y producción, y por qué CORS no interviene en el uso normal, están en [infra/README.md](infra/README.md).

## Comandos

| Tarea | Back (`back/`) | Front (`front/`) |
|---|---|---|
| Servidor de desarrollo | `uv run fastapi dev app/main.py` | `npm run dev` |
| Lint | `uv run ruff check .` | `npm run lint` |
| Formato | `uv run ruff format .` | `npm run format` |
| Pruebas | `uv run pytest` | `npm test` |
| Build | — | `npm run build` |
| Nueva migración | `uv run alembic revision --autogenerate -m "..."` | — |

## Flujo de trabajo

- `main` es estable y solo recibe PR desde `dev` al cerrar cada sprint.
- `dev` es la rama de integración. Las ramas de trabajo (`feat/…`, `fix/…`, `chore/…`) salen de `dev` y regresan por PR.
- Los commits siguen Conventional Commits en español: `tipo(alcance): descripción`.
