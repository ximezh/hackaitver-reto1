import os

# `app.main` crea la aplicación al importarse. Las pruebas unitarias no usan una base real,
# así que basta con una URL de ejemplo cuando no hay `back/.env`.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
