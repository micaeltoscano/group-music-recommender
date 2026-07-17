"""Schemas para o módulo de Vibe Check (PB-07)."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List

class VibeCheckOption(BaseModel):
    id: str
    letter: str
    text: str
    value: float

class VibeCheckQuestion(BaseModel):
    id: str
    text: str
    options: List[VibeCheckOption]

class VibeCheckResponse(BaseModel):
    """Retorno das perguntas disponíveis para a sala."""
    questions: List[VibeCheckQuestion]

class VibeCheckSubmitRequest(BaseModel):
    """Valores submetidos pelo usuário (0.0 a 1.0)."""
    energy: float = Field(..., ge=0.0, le=1.0)
    valence: float = Field(..., ge=0.0, le=1.0)
    popularity: float = Field(..., ge=0.0, le=1.0)

class VibeCheckSubmitResponse(BaseModel):
    """Resposta ao salvar as escolhas."""
    message: str
