"""Configurações da aplicação.

Todos os valores sensíveis são obtidos de variáveis de ambiente (ou de um
arquivo `.env` na raiz do repositório, que NÃO é versionado). Nada de segredos
embutido no código. Veja `.env.example` para a lista de variáveis.

Escopo PB-01: apenas `DATABASE_URL` e as configurações básicas do app são
necessárias para a fundação técnica. As chaves de Spotify / Last.fm são
declaradas como opcionais para histórias futuras e NÃO são exigidas aqui. O
LLM (PB-17) roda localmente via Ollama e não precisa de chave.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> parents[2] == raiz do repositório
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configurações carregadas do ambiente / arquivo `.env` da raiz."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Aplicação -----------------------------------------------------------
    app_name: str = "Vibe Check API"
    app_env: str = "development"
    api_v1_prefix: str = ""

    # --- Banco de dados (PB-01) ---------------------------------------------
    # Default aponta para o Postgres do docker-compose local. Não é um segredo:
    # é uma credencial descartável de desenvolvimento definida no compose.
    database_url: str = Field(
        default="postgresql+psycopg2://vibe:vibe@localhost:5432/vibe",
    )

    # --- Snapshots musicais (PB-08) -----------------------------------------
    music_snapshot_ttl_days: int = Field(default=7, ge=1)
    spotify_top_items_limit: int = Field(default=50, ge=1, le=50)

    # --- CORS ----------------------------------------------------------------
    # Origens permitidas para o frontend Vite (separadas por vírgula).
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    frontend_url: str = "http://localhost:5173"

    # --- Segredos de histórias FUTURAS (fora do escopo do PB-01) -------------
    # Declarados como opcionais para que o app suba sem eles. Serão exigidos
    # apenas quando as respectivas histórias forem implementadas.
    spotify_client_id: str | None = None
    spotify_client_secret: str | None = None
    spotify_redirect_uri: str | None = None
    lastfm_api_key: str | None = None
    fernet_key: str | None = None

    # --- LLM local (PB-17) ----------------------------------------------------
    # Ollama rodando localmente; sem chave de API. Se indisponível, o pipeline
    # usa o fallback determinístico automaticamente (ver `llm_client.py`).
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_seconds: float = Field(default=8.0, gt=0)

    @property
    def secure_cookies(self) -> bool:
        return self.app_env.lower() not in {"development", "test"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()
