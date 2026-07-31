"""Cliente da API do Spotify para autenticação e busca de perfil."""

import base64
import urllib.parse
from collections.abc import Collection
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
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
# playlist-read-private e playlist-read-collaborative (inventário da Sprint 7)
PLAYLIST_READ_PRIVATE_SCOPE = "playlist-read-private"
PLAYLIST_READ_COLLABORATIVE_SCOPE = "playlist-read-collaborative"
PLAYLIST_INVENTORY_SCOPES = frozenset(
    {
        PLAYLIST_READ_PRIVATE_SCOPE,
        PLAYLIST_READ_COLLABORATIVE_SCOPE,
    }
)
SCOPES = (
    "user-top-read playlist-modify-private user-read-private "
    f"{PLAYLIST_READ_PRIVATE_SCOPE} {PLAYLIST_READ_COLLABORATIVE_SCOPE}"
)

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

    def __init__(
        self,
        message: str,
        *,
        missing_scopes: Collection[str] = (),
    ) -> None:
        self.missing_scopes = tuple(sorted(set(missing_scopes)))
        super().__init__(message)


class SpotifyRateLimited(Exception):
    """Indica rate limit da Web API e preserva o Retry-After recebido."""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(f"Spotify temporariamente limitado; tente em {retry_after}s.")


class SpotifyInvalidResponse(Exception):
    """Indica payload inesperado da Web API sem expor seu conteúdo."""


class SpotifyAccessForbidden(Exception):
    """Indica conteúdo Spotify conhecido, porém não legível pelo usuário atual."""


class SpotifyAPIUnavailable(Exception):
    """Indica falha HTTP externa sanitizada que não é 401, 403 ou 429."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _scope_set(value: str | None) -> set[str]:
    return {scope for scope in (value or "").split() if scope}


def _require_stored_scopes(
    db: Session,
    stored: SpotifyToken,
    required_scopes: Collection[str],
    now: datetime,
) -> None:
    missing = set(required_scopes) - _scope_set(stored.scopes)
    if not missing:
        return
    stored.reauth_required_at = now
    db.commit()
    raise ReauthenticationRequired(
        "Novo consentimento Spotify necessário.",
        missing_scopes=missing,
    )


async def get_valid_access_token(
    db: Session,
    user_id: int,
    *,
    required_scopes: Collection[str] = (),
) -> str:
    """Retorna token válido, renovando-o e persistindo o resultado quando expirado."""
    stored = db.query(SpotifyToken).filter(SpotifyToken.user_id == user_id).first()
    if not stored or stored.reauth_required_at is not None:
        raise ReauthenticationRequired("Autorização Spotify necessária.")

    now = datetime.now(timezone.utc)
    _require_stored_scopes(db, stored, required_scopes, now)
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
        _require_stored_scopes(db, stored, required_scopes, now)
        db.commit()
        return access_token
    except ReauthenticationRequired:
        raise
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


def _retry_after_seconds(value: str | None) -> int:
    try:
        return max(1, int(value or "1"))
    except ValueError:
        return 1


async def get_user_top_items(
    access_token: str,
    item_type: str,
    *,
    time_range: str = "medium_term",
    limit: int = 50,
) -> list[dict]:
    """Busca top tracks ou artists usando somente o endpoint autorizado do MVP."""
    if item_type not in {"tracks", "artists"}:
        raise ValueError("Tipo de top item inválido.")
    if time_range not in {"short_term", "medium_term", "long_term"}:
        raise ValueError("Faixa temporal inválida.")

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"time_range": time_range, "limit": limit, "offset": 0}
    async with AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/me/top/{item_type}",
            headers=headers,
            params=params,
        )
        if response.status_code == 429:
            raise SpotifyRateLimited(_retry_after_seconds(response.headers.get("Retry-After")))
        response.raise_for_status()
        payload = response.json()

    items = payload.get("items")
    if not isinstance(items, list):
        raise SpotifyInvalidResponse("Spotify retornou um payload de top items inválido.")
    return items


async def get_top_tracks(
    access_token: str,
    *,
    time_range: str = "medium_term",
    limit: int = 50,
) -> list[dict]:
    return await get_user_top_items(
        access_token,
        "tracks",
        time_range=time_range,
        limit=limit,
    )


async def get_top_artists(
    access_token: str,
    *,
    time_range: str = "medium_term",
    limit: int = 50,
) -> list[dict]:
    return await get_user_top_items(
        access_token,
        "artists",
        time_range=time_range,
        limit=limit,
    )


def _raise_playlist_access_error(response) -> None:
    if response.status_code == 401:
        raise ReauthenticationRequired("Autorização Spotify expirada ou inválida.")
    if response.status_code == 403:
        raise SpotifyAccessForbidden("Conteúdo da playlist não permitido para este usuário.")
    if response.status_code == 429:
        raise SpotifyRateLimited(_retry_after_seconds(response.headers.get("Retry-After")))
    if response.status_code >= 400:
        raise SpotifyAPIUnavailable("Spotify indisponível ao consultar playlists.")


def _playlist_page_payload(response, *, resource: str) -> dict:
    _raise_playlist_access_error(response)
    try:
        payload = response.json()
    except ValueError as exc:
        raise SpotifyInvalidResponse(
            f"Spotify retornou um payload de {resource} inválido."
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise SpotifyInvalidResponse(f"Spotify retornou um payload de {resource} inválido.")
    next_url = payload.get("next")
    if next_url is not None and not isinstance(next_url, str):
        raise SpotifyInvalidResponse(f"Spotify retornou paginação de {resource} inválida.")
    return payload


async def get_current_user_playlists(
    access_token: str,
    *,
    limit: int = 50,
) -> list[dict]:
    """Pagina todo o inventário de playlists visível ao usuário atual."""
    if not 1 <= limit <= 50:
        raise ValueError("O limite de playlists deve estar entre 1 e 50.")

    headers = {"Authorization": f"Bearer {access_token}"}
    playlists: list[dict] = []
    offset = 0
    seen_offsets: set[int] = set()
    async with AsyncClient() as client:
        while True:
            if offset in seen_offsets:
                raise SpotifyInvalidResponse("Spotify retornou paginação de playlists cíclica.")
            seen_offsets.add(offset)
            response = await client.get(
                f"{SPOTIFY_API_BASE}/me/playlists",
                headers=headers,
                params={"limit": limit, "offset": offset},
            )
            payload = _playlist_page_payload(response, resource="playlists")
            items = payload["items"]
            playlists.extend(items)
            if payload.get("next") is None:
                break
            if not items:
                raise SpotifyInvalidResponse("Spotify retornou paginação de playlists sem avanço.")
            offset += len(items)
    return playlists


def _validate_playlist_id(playlist_id: str) -> None:
    if not playlist_id or not playlist_id.isalnum():
        raise ValueError("ID de playlist Spotify inválido.")


async def get_playlist_items_page(
    access_token: str,
    playlist_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Busca uma página de itens, usada também para verificar acesso ao conteúdo."""
    _validate_playlist_id(playlist_id)
    if not 1 <= limit <= 50 or offset < 0:
        raise ValueError("Paginação de itens da playlist inválida.")
    headers = {"Authorization": f"Bearer {access_token}"}
    async with AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/items",
            headers=headers,
            params={"limit": limit, "offset": offset},
        )
    return _playlist_page_payload(response, resource="itens da playlist")


async def get_playlist_items(
    access_token: str,
    playlist_id: str,
    *,
    limit: int = 50,
) -> list[dict]:
    """Pagina os itens de uma playlist sem consultar detalhes faixa a faixa."""
    items: list[dict] = []
    offset = 0
    seen_offsets: set[int] = set()
    while True:
        if offset in seen_offsets:
            raise SpotifyInvalidResponse("Spotify retornou paginação de itens cíclica.")
        seen_offsets.add(offset)
        page = await get_playlist_items_page(
            access_token,
            playlist_id,
            limit=limit,
            offset=offset,
        )
        page_items = page["items"]
        items.extend(page_items)
        if page.get("next") is None:
            break
        if not page_items:
            raise SpotifyInvalidResponse("Spotify retornou paginação de itens sem avanço.")
        offset += len(page_items)
    return items


def extract_playlist_tracks(items: Collection[object]) -> list[dict]:
    """Normaliza somente faixas Spotify utilizáveis, sem fazer chamadas adicionais."""
    tracks: list[dict] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        item = entry.get("item")
        if item is None:
            item = entry.get("track")
        if not isinstance(item, dict):
            continue
        if item.get("type", "track") != "track" or item.get("is_local") is True:
            continue
        track_id = item.get("id")
        if not isinstance(track_id, str) or not track_id.isalnum():
            continue
        expected_uri = f"spotify:track:{track_id}"
        if item.get("uri") != expected_uri:
            continue
        tracks.append(item)
    return tracks


async def get_playlist_tracks(
    access_token: str,
    playlist_id: str,
    *,
    limit: int = 50,
) -> list[dict]:
    """Pagina uma playlist e remove episódios, locais, nulos e IDs inválidos."""
    items = await get_playlist_items(access_token, playlist_id, limit=limit)
    return extract_playlist_tracks(items)


async def search_track(
    access_token: str,
    query: str,
    market: str = "from_token",
    limit: int = 3,
) -> list[dict]:
    """Busca faixas no Spotify por termo, retornando os itens encontrados."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": query,
        "type": "track",
        "market": market,
        "limit": limit,
    }
    async with AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_API_BASE}/search",
            headers=headers,
            params=params,
        )
        if response.status_code == 429:
            raise SpotifyRateLimited(_retry_after_seconds(response.headers.get("Retry-After")))
        response.raise_for_status()
        payload = response.json()

    tracks_data = payload.get("tracks", {})
    items = tracks_data.get("items")
    if not isinstance(items, list):
        raise SpotifyInvalidResponse("Spotify retornou um payload de busca inválido.")
    return items


async def create_playlist(
    access_token: str,
    user_spotify_id: str,
    name: str,
    description: str = "",
    public: bool = False,
) -> dict:
    """Cria uma nova playlist para o usuário dono do `access_token`.

    Usa `POST /me/playlists` (não `/users/{id}/playlists`): o Spotify passou a
    recusar o endpoint com id explícito na URL com 403 Forbidden para apps mais
    novos, mesmo com o usuário autorizado e o token válido. `/me/playlists`
    sempre cria a playlist para o dono do token autenticado, que é o
    comportamento desejado aqui (`user_spotify_id` é mantido no parâmetro só
    para compatibilidade da assinatura e não é mais usado na chamada).
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": name,
        "description": description,
        "public": public,
    }
    async with AsyncClient() as client:
        response = await client.post(
            f"{SPOTIFY_API_BASE}/me/playlists",
            headers=headers,
            json=payload,
        )
        if response.status_code == 429:
            raise SpotifyRateLimited(_retry_after_seconds(response.headers.get("Retry-After")))
        response.raise_for_status()
        return response.json()


async def add_items_to_playlist(
    access_token: str,
    playlist_id: str,
    uris: list[str],
) -> dict:
    """Adiciona itens a uma playlist existente.

    Usa `POST /playlists/{id}/items` (não `/tracks`): o Spotify passou a
    recusar `/tracks` com 403 Forbidden para apps novos/em Development Mode —
    confirmado empiricamente (mesmo token/escopo/playlist, só a rota muda o
    resultado de 403 para 201). `/items` é o substituto atual.
    """
    if not uris:
        return {}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "uris": uris,
    }
    async with AsyncClient() as client:
        response = await client.post(
            f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/items",
            headers=headers,
            json=payload,
        )
        if response.status_code == 429:
            raise SpotifyRateLimited(_retry_after_seconds(response.headers.get("Retry-After")))
        response.raise_for_status()
        return response.json()
