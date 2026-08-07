"""Base declarativa do SQLAlchemy.

`Base.metadata` é o alvo do autogenerate do Alembic. Todos os modelos devem
herdar de `Base` e ser importados antes de gerar/aplicar migrações.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM."""
