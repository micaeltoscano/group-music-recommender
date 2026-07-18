"""Rotas autenticadas de feedback pós-playlist (PB-20)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.schemas.feedback import (
    PlaylistFeedbackRequest,
    PlaylistFeedbackResponse,
    TrackFeedbackRequest,
    TrackFeedbackResponse,
)
from app.services.feedback_service import (
    FUTURE_USE_NOTICE,
    FeedbackAccessDeniedError,
    FeedbackRunNotCompletedError,
    FeedbackRunNotFoundError,
    FeedbackTrackNotFoundError,
    save_playlist_feedback,
    save_track_feedback,
)

router = APIRouter()


def _raise_feedback_http_error(exc: Exception) -> None:
    if isinstance(exc, FeedbackAccessDeniedError):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, FeedbackRunNotCompletedError):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_404_NOT_FOUND
    raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.post(
    "/{run_id}/tracks/{track_id}/feedback",
    response_model=TrackFeedbackResponse,
)
def post_track_feedback(
    run_id: UUID,
    payload: TrackFeedbackRequest,
    track_id: str = Path(min_length=1, max_length=255),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrackFeedbackResponse:
    try:
        feedback = save_track_feedback(db, run_id, track_id, current_user["id"], payload)
    except (
        FeedbackAccessDeniedError,
        FeedbackRunNotCompletedError,
        FeedbackRunNotFoundError,
        FeedbackTrackNotFoundError,
    ) as exc:
        _raise_feedback_http_error(exc)

    return TrackFeedbackResponse.model_validate(
        {**feedback.__dict__, "future_use_notice": FUTURE_USE_NOTICE}
    )


@router.post("/{run_id}/feedback", response_model=PlaylistFeedbackResponse)
def post_playlist_feedback(
    run_id: UUID,
    payload: PlaylistFeedbackRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlaylistFeedbackResponse:
    try:
        feedback = save_playlist_feedback(db, run_id, current_user["id"], payload)
    except (
        FeedbackAccessDeniedError,
        FeedbackRunNotCompletedError,
        FeedbackRunNotFoundError,
    ) as exc:
        _raise_feedback_http_error(exc)

    return PlaylistFeedbackResponse.model_validate(
        {**feedback.__dict__, "future_use_notice": FUTURE_USE_NOTICE}
    )
