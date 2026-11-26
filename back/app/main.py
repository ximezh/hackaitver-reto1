from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import errores
from app.auth.router import router as auth
from app.config import get_settings
from app.routers import health


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="HackAITver Reto 1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    errores.registrar(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(auth, prefix="/api")
    return app


app = create_app()
