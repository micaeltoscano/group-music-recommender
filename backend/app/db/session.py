"""Engine e sessão do SQLAlchemy.

A URL de conexão vem exclusivamente de `settings.database_url` (variável de
ambiente `DATABASE_URL`). O `get_db` é a dependência usada pelas rotas e pode
ser sobrescrito nos testes.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# pool_pre_ping evita conexões mortas após o Postgres reiniciar.
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """Fornece uma sessão de banco por requisição e a fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
