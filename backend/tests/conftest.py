"""Fixtures de teste.

Os testes de saúde não dependem do Postgres: a dependência `get_db` é
sobrescrita por uma sessão SQLite em memória (caminho feliz) ou por uma sessão
que falha (caminho de indisponibilidade). Assim a suíte roda em qualquer
ambiente, inclusive sem banco no ar.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.main import app

# SQLite em memória compartilhado durante a sessão de testes.
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    future=True,
)
_TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


def _override_get_db() -> Iterator[Session]:
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """TestClient com um banco de testes (SQLite) no lugar do Postgres."""
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
