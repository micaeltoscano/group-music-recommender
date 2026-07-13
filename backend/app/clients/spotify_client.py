"""Cliente da API do Spotify para autenticação e busca de perfil."""

import base64
import urllib.parse
from httpx import AsyncClient, HTTPStatusError
from app.config import settings

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

async def get_current_user_profile(access_token: str) -> dict:
    """Busca o perfil do usuário atual na API do Spotify."""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with AsyncClient() as client:
        response = await client.get(f"{SPOTIFY_API_BASE}/me", headers=headers)
        response.raise_for_status()
        return response.json()
