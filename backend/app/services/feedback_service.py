"""Persistência e autorização do feedback pós-playlist (PB-20)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import (
    MemberTrackFeedback,
    MusicSessionMember,
    PlaylistFeedback,
    PlaylistRun,
    PlaylistRunTrack,
)
from app.schemas.feedback import PlaylistFeedbackRequest, TrackFeedbackRequest

FUTURE_USE_NOTICE = (
    "Este feedback será usado em evoluções futuras e não altera o ranking do MVP."
)


class FeedbackRunNotFoundError(Exception):
    pass


class FeedbackAccessDeniedError(Exception):
    pass


class FeedbackRunNotCompletedError(Exception):
    pass


class FeedbackTrackNotFoundError(Exception):
    pass


def _authorized_completed_run(db: Session, run_id: UUID, user_id: int) -> PlaylistRun:
    run = db.get(PlaylistRun, run_id)
    if run is None:
        raise FeedbackRunNotFoundError("Execução de playlist não encontrada.")

    membership = db.get(MusicSessionMember, (run.session_id, user_id))
    if membership is None:
        raise FeedbackAccessDeniedError(
            "Você não participa da sala desta execução de playlist."
        )
    if run.status != "completed":
        raise FeedbackRunNotCompletedError(
            "O feedback só pode ser enviado após a conclusão da playlist."
        )
    return run


def save_track_feedback(
    db: Session,
    run_id: UUID,
    spotify_track_id: str,
    user_id: int,
    payload: TrackFeedbackRequest,
) -> MemberTrackFeedback:
    """Cria ou atualiza os sinais do usuário para uma faixa selecionada."""

    _authorized_completed_run(db, run_id, user_id)
    track = (
        db.query(PlaylistRunTrack)
        .filter(
            PlaylistRunTrack.run_id == run_id,
            PlaylistRunTrack.spotify_id == spotify_track_id,
            PlaylistRunTrack.status == "matched",
        )
        .first()
    )
    if track is None:
        raise FeedbackTrackNotFoundError(
            "Faixa não encontrada entre as músicas selecionadas desta execução."
        )

    feedback = (
        db.query(MemberTrackFeedback)
        .filter(
            MemberTrackFeedback.user_id == user_id,
            MemberTrackFeedback.playlist_run_id == run_id,
            MemberTrackFeedback.spotify_track_id == spotify_track_id,
        )
        .first()
    )
    if feedback is None:
        feedback = MemberTrackFeedback(
            user_id=user_id,
            playlist_run_id=run_id,
            spotify_track_id=spotify_track_id,
        )
        db.add(feedback)

    feedback.liked = payload.liked
    feedback.disliked = payload.disliked
    feedback.more_like_this = payload.more_like_this
    feedback.never_again = payload.never_again
    db.commit()
    db.refresh(feedback)
    return feedback


def save_playlist_feedback(
    db: Session,
    run_id: UUID,
    user_id: int,
    payload: PlaylistFeedbackRequest,
) -> PlaylistFeedback:
    """Cria ou atualiza a avaliação geral do usuário para a execução."""

    _authorized_completed_run(db, run_id, user_id)
    feedback = (
        db.query(PlaylistFeedback)
        .filter(
            PlaylistFeedback.user_id == user_id,
            PlaylistFeedback.playlist_run_id == run_id,
        )
        .first()
    )
    if feedback is None:
        feedback = PlaylistFeedback(user_id=user_id, playlist_run_id=run_id)
        db.add(feedback)

    feedback.representation_score = payload.representation_score
    feedback.satisfaction_score = payload.satisfaction_score
    feedback.comments = payload.comments.strip() if payload.comments else None
    db.commit()
    db.refresh(feedback)
    return feedback
