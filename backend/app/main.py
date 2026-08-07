"""Ponto de entrada da API FastAPI do Vibe Check."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import auth, feedback, health, music, rooms, vibe_check
from app.config import settings


def create_app() -> FastAPI:
    if settings.app_env.lower() not in {"development", "test"} and not settings.fernet_key:
        raise RuntimeError("FERNET_KEY é obrigatória fora do ambiente de desenvolvimento/teste.")

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        summary="API de recomendação musical coletiva do Vibe Check.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
    app.include_router(vibe_check.router, prefix="/rooms", tags=["vibe_check"])
    app.include_router(music.router, prefix="/me", tags=["music"])
    app.include_router(feedback.router, prefix="/playlist-runs", tags=["feedback"])

    @app.get("/", tags=["root"], summary="Raiz")
    def root() -> dict[str, str]:
        return {"app": settings.app_name, "version": __version__, "docs": "/docs"}

    return app


app = create_app()
