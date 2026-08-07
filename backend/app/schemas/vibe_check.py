"""Schemas para o módulo de Vibe Check (PB-07)."""

from typing import Literal

from pydantic import BaseModel, Field


class VibeCheckOption(BaseModel):
    id: str
    letter: str
    text: str
    value: float

class VibeCheckQuestion(BaseModel):
    id: str
    text: str
    options: list[VibeCheckOption]


class VibeCheckValues(BaseModel):
    """Valores privados retornados somente ao próprio integrante."""

    energy: float = Field(..., ge=0.0, le=1.0)
    valence: float = Field(..., ge=0.0, le=1.0)
    popularity: float = Field(..., ge=0.0, le=1.0)


class VibeCheckResponse(BaseModel):
    """Retorno das perguntas disponíveis para a sala."""
    questions: list[VibeCheckQuestion]
    status: Literal["pending", "answered", "skipped"] = "pending"
    answer: VibeCheckValues | None = None


class VibeCheckSubmitRequest(VibeCheckValues):
    """Valores submetidos pelo usuário (0.0 a 1.0)."""


class VibeCheckSubmitResponse(BaseModel):
    """Resposta ao salvar as escolhas."""
    message: str
