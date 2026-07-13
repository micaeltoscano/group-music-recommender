"""Cliente da API do Spotify para autenticação e busca de perfil."""

import base64
import urllib.parse
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient, HTTPStatusError
from sqlalchemy.orm import Session

from app.clients import crypto
from app.config import settings
from app.db.models import SpotifyToken

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

# Escopos exigidos para o MVP (conforme o README)
# playlist-modify-private (padrão)
# user-top-read (para snapshots)
# user-read-private (para mercado/país)
SCOPES = "user-top-read playlist-modify-private user-read-private"

def get_auth_url(state: str) -> str:
    """Gera a URL de redirecionamento para o fluxo de autorização do Spotify."""
    if not settings.spotify_client_id or not settings.spotify_redirect_uri:
        raise ValueError("Chaves do Spotify não estão configuradas.")

    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "state": state,
        "scope": SCOPES,
        "show_dialog": "true", # Força a mostrar o dialog para facilitar testes de logout/login
    }
    
    query = urllib.parse.urlencode(params)
    return f"{SPOTIFY_AUTH_URL}?{query}"

async def exchange_code_for_token(code: str) -> dict:
    """Troca o código de autorização pelos tokens de acesso."""
    if not settings.spotify_client_id or not settings.spotify_client_secret or not settings.spotify_redirect_uri:
        raise ValueError("Chaves do Spotify não estão configuradas.")

    auth_str = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.spotify_redirect_uri
    }

    async with AsyncClient() as client:
        response = await client.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Renova um access token usando o refresh token persistido."""
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        raise ValueError("Chaves do Spotify não estão configuradas.")

    credentials = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
    headers = {
        "Authorization": f"Basic {base64.b64encode(credentials.encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    async with AsyncClient() as client:
        response = await client.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()


class ReauthenticationRequired(Exception):
    """Indica que o usuário precisa autorizar o aplicativo novamente."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def get_valid_access_token(db: Session, user_id: int) -> str:
    """Retorna token válido, renovando-o e persistindo o resultado quando expirado."""
    stored = db.query(SpotifyToken).filter(SpotifyToken.user_id == user_id).first()
    if not stored or stored.reauth_required_at is not None:
        raise ReauthenticationRequired("Autorização Spotify necessária.")

    now = datetime.now(timezone.utc)
    if _as_utc(stored.token_expires_at) > now:
        return crypto.decrypt(stored.access_token)

    try:
        refresh_value = crypto.decrypt(stored.refresh_token)
        refreshed = await refresh_access_token(refresh_value)
        access_token = refreshed["access_token"]
        stored.access_token = crypto.encrypt(access_token)
        if refreshed.get("refresh_token"):
            stored.refresh_token = crypto.encrypt(refreshed["refresh_token"])
        stored.token_expires_at = now + timedelta(seconds=refreshed.get("expires_in", 3600))
        stored.scopes = refreshed.get("scope", stored.scopes)
        stored.reauth_required_at = None
        db.commit()
        return access_token
    except Exception as exc:
        db.rollback()
        stored = db.query(SpotifyToken).filter(SpotifyToken.user_id == user_id).first()
        if stored:
            stored.reauth_required_at = now
            db.commit()
        raise ReauthenticationRequired("Falha ao renovar autorização Spotify.") from exc

async def get_current_user_profile(access_token: str) -> dict:
    """Busca o perfil do usuário atual na API do Spotify."""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with AsyncClient() as client:
        response = await client.get(f"{SPOTIFY_API_BASE}/me", headers=headers)
        response.raise_for_status()
        return response.json()
