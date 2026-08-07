"""Schema do contexto estruturado interpretado a partir da descrição livre do host (PB-17)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Energy = Literal["baixa", "media", "alta"]

MAX_TAGS = 8
MAX_AVOID = 8
MAX_TAG_LENGTH = 40


def _clean_tags(value: list[str]) -> list[str]:
    """Normaliza uma lista de tags: strip, minúsculas, remove vazias/duplicadas."""
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in value:
        if not isinstance(raw, str):
            continue
        tag = raw.strip().lower()[:MAX_TAG_LENGTH]
        if tag and tag not in seen:
            seen.add(tag)
            cleaned.append(tag)
    return cleaned


class LLMContext(BaseModel):
    """Critérios estruturados derivados do contexto do host.

    Não decide músicas: é consumido pelo motor (Preference Negotiation Engine)
    como mais um sinal de scoring, com peso limitado (ver `engine/weights.py`).
    """

    occasion: str = Field(..., max_length=100)
    mood: str = Field(..., max_length=60)
    energy: Energy
    tags_positive: list[str] = Field(default_factory=list)
    tags_negative: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)

    @field_validator("occasion", "mood", mode="before")
    @classmethod
    def _strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("tags_positive", "tags_negative", "avoid", mode="before")
    @classmethod
    def _normalize_lists(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        return _clean_tags(value)

    @field_validator("tags_positive")
    @classmethod
    def _limit_tags_positive(cls, value: list[str]) -> list[str]:
        return value[:MAX_TAGS]

    @field_validator("tags_negative")
    @classmethod
    def _limit_tags_negative(cls, value: list[str]) -> list[str]:
        return value[:MAX_TAGS]

    @field_validator("avoid")
    @classmethod
    def _limit_avoid(cls, value: list[str]) -> list[str]:
        return value[:MAX_AVOID]
