"""Rotas de autenticação (Spotify OAuth) e sessão."""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, SpotifyToken, AppSession
from app.clients import spotify_client, crypto
from app.config import settings
from app.services.privacy_service import invalidate_session, remove_personal_data

router = APIRouter()

# Constantes de configuração
STATE_COOKIE_NAME = "spotify_auth_state"
SESSION_COOKIE_NAME = "vibe_session"
SESSION_EXPIRY_DAYS = 30

@router.get("/login")
def login(response: Response):
    """Inicia o fluxo OAuth gerando um state e redirecionando."""
    state = secrets.token_urlsafe(32)
    url = spotify_client.get_auth_url(state)
    
    # Adiciona o cookie de state
    response = RedirectResponse(url, status_code=302)
    response.set_cookie(
        key=STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=600 # 10 minutos
    )
    return response

@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """Recebe o callback do Spotify, troca o código por token e cria a sessão."""
    if error:
        raise HTTPException(status_code=400, detail="Autorização Spotify negada.")

    cookie_state = request.cookies.get(STATE_COOKIE_NAME)
    
    if not state or not cookie_state or state != cookie_state:
        raise HTTPException(status_code=400, detail="State inválido ou ausente.")
        
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorização ausente.")

    try:
        token_data = await spotify_client.exchange_code_for_token(code)
    except Exception:
        raise HTTPException(status_code=400, detail="Falha ao trocar código por token.")

    try:
        profile_data = await spotify_client.get_current_user_profile(token_data["access_token"])
    except Exception:
        raise HTTPException(status_code=400, detail="Falha ao buscar perfil do usuário.")

    spotify_id = profile_data.get("id")
    display_name = profile_data.get("display_name")
    
    images = profile_data.get("images", [])
    image_url = images[0].get("url") if images else None

    # Upsert User
    user = db.query(User).filter(User.spotify_id == spotify_id).first()
    if not user:
        user = User(
            spotify_id=spotify_id,
            display_name=display_name,
            image_url=image_url
        )
        db.add(user)
        db.flush() # Para gerar user.id
    else:
        user.display_name = display_name
        user.image_url = image_url

    # Upsert SpotifyToken
    # Calcula expiração baseada em expires_in (segundos)
    expires_in = token_data.get("expires_in", 3600)
    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    
    encrypted_access = crypto.encrypt(token_data["access_token"])
    encrypted_refresh = crypto.encrypt(token_data.get("refresh_token", ""))

    spotify_token = db.query(SpotifyToken).filter(SpotifyToken.user_id == user.id).first()
    if not spotify_token:
        spotify_token = SpotifyToken(
            user_id=user.id,
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            token_expires_at=token_expires_at,
            scopes=token_data.get("scope")
        )
        db.add(spotify_token)
    else:
        spotify_token.access_token = encrypted_access
        if encrypted_refresh: # Só atualiza se vier um novo
            spotify_token.refresh_token = encrypted_refresh
        spotify_token.token_expires_at = token_expires_at
        spotify_token.scopes = token_data.get("scope")

    # Cria AppSession
    raw_session_token = secrets.token_urlsafe(64)
    session_hash = hashlib.sha256(raw_session_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)

    app_session = AppSession(
        user_id=user.id,
        session_token_hash=session_hash,
        expires_at=expires_at
    )
    db.add(app_session)
    db.commit()

    # Redireciona para o frontend com o cookie de sessão
    redirect_response = RedirectResponse(settings.frontend_url, status_code=302)
    redirect_response.delete_cookie(STATE_COOKIE_NAME)
    redirect_response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_session_token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=SESSION_EXPIRY_DAYS * 24 * 60 * 60
    )
    
    return redirect_response

@router.get("/me")
def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Retorna os dados do usuário atual se a sessão for válida."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        raise HTTPException(status_code=401, detail="Não autenticado.")
        
    session_hash = hashlib.sha256(session_token.encode()).hexdigest()
    app_session = db.query(AppSession).filter(AppSession.session_token_hash == session_hash).first()
    
    expires_at = app_session.expires_at if app_session else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if not app_session or expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
        
    user = db.query(User).filter(User.id == app_session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
        
    return {
        "id": user.id,
        "spotify_id": user.spotify_id,
        "display_name": user.display_name,
        "image_url": user.image_url
    }


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> None:
    """Invalida a sessao atual no backend e remove o cookie do navegador."""

    invalidate_session(db, request.cookies.get(SESSION_COOKIE_NAME))
    _clear_session_cookie(response)


@router.delete("/me", status_code=204)
def delete_current_user(
    response: Response,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    """Remove dados pessoais e anonimiza a identidade sem apagar dados do grupo."""

    remove_personal_data(db, current_user["id"])
    _clear_session_cookie(response)
