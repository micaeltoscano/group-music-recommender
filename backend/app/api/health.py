"""Endpoints de saúde (health checks).

- `GET /health`     -> liveness: o processo está de pé (não toca o banco).
- `GET /health/db`  -> readiness: o backend consegue falar com o PostgreSQL.

Nenhum segredo é exposto nas respostas.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import __version__
from app.config import settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness check")
def health() -> dict[str, str]:
    """Confirma que a aplicação está no ar."""
    return {"status": "ok", "app": settings.app_name, "version": __version__}


@router.get("/health/db", summary="Readiness check (PostgreSQL)")
def health_db(db: Session = Depends(get_db)) -> JSONResponse:
    """Confirma a conectividade com o banco executando `SELECT 1`.

    Retorna 200 quando o banco responde e 503 caso contrário. A mensagem de erro
    é genérica para não vazar detalhes de conexão.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "database": "ok"},
    )
