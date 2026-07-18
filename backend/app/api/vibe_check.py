"""Rotas do Vibe Check (PB-07)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.db.models import MusicSession, MusicSessionMember, VibeCheckAnswer
from app.schemas.vibe_check import (
    VibeCheckResponse,
    VibeCheckSubmitRequest,
    VibeCheckSubmitResponse,
    VibeCheckQuestion,
    VibeCheckOption,
)

router = APIRouter()

QUESTIONS = [
    VibeCheckQuestion(
        id="energy",
        text="Como deve ser o ritmo da playlist?",
        options=[
            VibeCheckOption(id="A", letter="A", text="Bem calmo e relaxante", value=0.1),
            VibeCheckOption(id="B", letter="B", text="Tranquilo, mas com um pouco de ritmo", value=0.4),
            VibeCheckOption(id="C", letter="C", text="Animado, bom pra dançar", value=0.7),
            VibeCheckOption(id="D", letter="D", text="Ritmo intenso, festa total!", value=1.0),
        ],
    ),
    VibeCheckQuestion(
        id="valence",
        text="Quanto espaço a playlist pode dar para músicas melancólicas?",
        options=[
            VibeCheckOption(
                id="A", letter="A", text="Quase nenhum, quero evitar tristeza", value=0.1
            ),
            VibeCheckOption(
                id="B", letter="B", text="Um pouco, de forma equilibrada", value=0.5
            ),
            VibeCheckOption(
                id="C", letter="C", text="Pode ter uma vibe bem reflexiva", value=0.9
            ),
        ],
    ),
    VibeCheckQuestion(
        id="popularity",
        text="O que vamos ouvir?",
        options=[
            VibeCheckOption(id="A", letter="A", text="Lado B / Desconhecidas", value=0.2),
            VibeCheckOption(id="B", letter="B", text="Mistura de hits e novidades", value=0.6),
            VibeCheckOption(id="C", letter="C", text="Só os hits que todo mundo conhece", value=1.0),
        ],
    ),
]


def _check_membership(db: Session, code: str, user_id: int) -> MusicSession:
    """Verifica se a sala existe e se o usuário é membro dela."""
    room = db.query(MusicSession).filter(MusicSession.code == code).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala não encontrada.",
        )

    is_member = (
        db.query(MusicSessionMember)
        .filter(
            MusicSessionMember.session_id == room.id,
            MusicSessionMember.user_id == user_id,
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não é membro desta sala.",
        )
    return room


@router.get("/{code}/vibe-check", response_model=VibeCheckResponse)
def get_vibe_check(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> VibeCheckResponse:
    """
    Retorna as perguntas do Vibe Check e verifica se o usuário tem permissão.
    """
    _check_membership(db, code, current_user["id"])
    return VibeCheckResponse(questions=QUESTIONS)


@router.post("/{code}/vibe-check", response_model=VibeCheckSubmitResponse)
def submit_vibe_check(
    code: str,
    payload: VibeCheckSubmitRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> VibeCheckSubmitResponse:
    """
    Salva as preferências numéricas do usuário para esta sala.
    """
    room = _check_membership(db, code, current_user["id"])

    # Upsert logic (se já existir, atualiza; senão, cria)
    existing_answer = (
        db.query(VibeCheckAnswer)
        .filter(
            VibeCheckAnswer.session_id == room.id,
            VibeCheckAnswer.user_id == current_user["id"],
        )
        .first()
    )

    if existing_answer:
        existing_answer.energy = payload.energy
        existing_answer.valence = payload.valence
        existing_answer.popularity = payload.popularity
    else:
        new_answer = VibeCheckAnswer(
            session_id=room.id,
            user_id=current_user["id"],
            energy=payload.energy,
            valence=payload.valence,
            popularity=payload.popularity,
        )
        db.add(new_answer)

    db.commit()

    return VibeCheckSubmitResponse(message="Vibe Check salvo com sucesso.")
