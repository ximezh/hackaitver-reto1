# API de FastAPI. Imagen de producción: sin dependencias de desarrollo y con usuario sin privilegios.
#   podman build -t reto1-back back/
#   podman run --env-file back/.env -p 8000:8000 reto1-back
# Las migraciones se corren al desplegar: `alembic upgrade head` dentro del contenedor.

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS dependencias
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

FROM docker.io/library/python:3.13-slim-bookworm
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 1000 api
WORKDIR /app
COPY --from=dependencias /app/.venv /app/.venv
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
USER api
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=2)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
