"""Ponto de entrada da API FastAPI (Vibe Check).

Escopo PB-01 (fundação técnica): apenas o app, CORS e os health checks.
Rotas de auth, salas, motor, etc. entram nas histórias seguintes.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        summary="Group Music Recommender — fundação técnica (PB-01).",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)

    @app.get("/", tags=["root"], summary="Raiz")
    def root() -> dict[str, str]:
        return {"app": settings.app_name, "version": __version__, "docs": "/docs"}

    return app


app = create_app()
