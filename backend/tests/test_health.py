"""Testes dos endpoints de saúde e da raiz (PB-01)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


def test_root(client) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["app"]
    assert body["version"]


def test_health_liveness(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_health_db_ok(client) -> None:
    """Com um banco alcançável (SQLite de teste), /health/db responde 200."""
    resp = client.get("/health/db")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok"}


def test_health_db_unavailable(client) -> None:
    """Se o banco falhar, /health/db responde 503 sem vazar detalhes."""

    class _BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

        def close(self) -> None:  # noqa: D401 - simples
            pass

    def _broken_db() -> Iterator[_BrokenSession]:
        yield _BrokenSession()

    app.dependency_overrides[get_db] = _broken_db
    try:
        resp = client.get("/health/db")
    finally:
        # o fixture 'client' restaura para o override padrão de banco no teardown
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 503
    assert resp.json()["database"] == "unavailable"
