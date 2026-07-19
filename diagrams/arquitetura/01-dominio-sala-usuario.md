# 01 — Domínio persistente: Usuário, Sala e Contexto

![Domínio persistente: Usuário, Sala e Contexto](01-dominio-sala-usuario.png)

```mermaid
classDiagram
    class User {
        +id: int
        +spotify_id: str
        +display_name: str
        +image_url: str
        +created_at: datetime
        +updated_at: datetime
    }

    class SpotifyToken {
        +user_id: int
        +access_token: str «cifrado»
        +refresh_token: str «cifrado»
        +token_expires_at: datetime
        +refresh_token_expires_at: datetime
        +reauth_required_at: datetime
        +scopes: str
    }

    class AppSession {
        +id: UUID
        +user_id: int
        +session_token_hash: str
        +expires_at: datetime
        +created_at: datetime
    }

    class MusicSession {
        +id: UUID
        +code: str
        +host_user_id: int
        +occasion: str
        +description: str
        +mode: str
        +status: str
        +created_at: datetime
        +expires_at: datetime
    }

    class MusicSessionMember {
        +session_id: UUID
        +user_id: int
        +role: str
        +joined_at: datetime
    }

    class ModoConsenso {
        <<Value Object>>
        +chave: str
        +pesos_individuais: Dict~str, float~
        +pesos_coletivos: Dict~str, float~
        +rejection_penalty: float
    }

    class UserMusicSnapshot {
        +id: UUID
        +user_id: int
        +time_range: str
        +top_tracks_json: List~Dict~
        +top_artists_json: List~Dict~
        +fetched_at: datetime
    }

    class VibeCheckAnswer {
        +id: UUID
        +session_id: UUID
        +user_id: int
        +status: str
        +energy: float
        +valence: float
        +popularity: float
    }

    class PlaylistRun {
        +id: UUID
        +session_id: UUID
        +status: str
        +progress_stage: str
        +progress_percent: int
        +spotify_playlist_id: str
        +spotify_playlist_url: str
        +compatibility_score: int
        +fairness_score: int
        +explanation_json: str
        +llm_context_json: str
        +subgroup_balancing_applied: bool
        +created_at: datetime
        +updated_at: datetime
    }

    class PlaylistRunTrack {
        +id: UUID
        +run_id: UUID
        +candidate_id: str
        +spotify_id: str
        +spotify_uri: str
        +name: str
        +artist: str
        +match_confidence: float
        +discard_reason: str
        +status: str
        +source: str
        +is_bridge: bool
        +selection_rank: int
    }

    class TrackContextCache {
        +id: UUID
        +spotify_track_id: str
        +track_name: str
        +artist_name: str
        +lastfm_track_tags_json: List~str~
        +lastfm_artist_tags_json: List~str~
        +spotify_artist_genres_json: List~str~
        +context_scores_json: Dict
        +source: str
        +confidence: float
        +fetched_at: datetime
    }

    class MemberTrackFeedback {
        +id: UUID
        +user_id: int
        +playlist_run_id: UUID
        +spotify_track_id: str
        +liked: bool
        +disliked: bool
        +more_like_this: bool
        +never_again: bool
    }

    class PlaylistFeedback {
        +id: UUID
        +user_id: int
        +playlist_run_id: UUID
        +representation_score: int
        +satisfaction_score: int
        +comments: str
    }

    User "1" *-- "0..1" SpotifyToken : possui
    User "1" *-- "0..*" AppSession : possui
    User "1" --> "0..*" MusicSession : hospeda (host_user_id)
    User "1" *-- "0..*" UserMusicSnapshot : possui
    User "1" -- "0..*" MusicSessionMember : participa como
    MusicSession "1" *-- "1..5" MusicSessionMember : agrega
    MusicSession "1" --> "0..1" ModoConsenso : configurada por
    MusicSession "1" *-- "0..*" PlaylistRun : gera
    MusicSession "1" *-- "0..*" VibeCheckAnswer : coleta
    User "1" -- "0..*" VibeCheckAnswer : responde
    PlaylistRun "1" *-- "0..*" PlaylistRunTrack : contém
    PlaylistRun "1" -- "0..*" MemberTrackFeedback : recebe
    PlaylistRun "1" -- "0..*" PlaylistFeedback : recebe
    User "1" -- "0..*" MemberTrackFeedback : registra
    User "1" -- "0..*" PlaylistFeedback : registra
    PlaylistRunTrack ..> TrackContextCache : consulta por spotify_track_id (sem FK)
```

Este diagrama corresponde 1:1 às 12 tabelas ORM de `app/db/models.py`, sem introduzir camadas de
`schemas`/`routers` (infraestrutura), que é onde a arquitetura FastAPI + SQLAlchemy + Alembic
efetivamente guarda o estado do produto. `MusicSessionMember` é modelada como uma classe associativa
explícita — não apenas uma associação N-N simples entre `User` e `MusicSession` — porque ela carrega o
atributo `role` ("host"/"member") que distingue o anfitrião dos convidados, e a composição
`MusicSession "1" *-- "1..5"` reproduz o limite de cinco integrantes por sala do RNF-05. `ModoConsenso`
foi modelada como um Value Object (não uma hierarquia de subclasses) porque é exatamente isso que o
código implementa: `CONSENSUS_MODES`, em `engine/weights.py`, é um dicionário de configuração
(pesos individuais, pesos coletivos e `rejection_penalty` por modo), e `MusicSession.mode` é apenas uma
string validada contra esse conjunto — não existe polimorfismo real a representar. Por fim,
`TrackContextCache` aparece sem associação formal (FK) com `PlaylistRunTrack`, porque no código ela é
de fato uma tabela de cache independente, consultada por `spotify_track_id` a partir do motor (ver
diagrama 02) e não referenciada por chave estrangeira — a dependência tracejada deixa essa
particularidade explícita em vez de forçar uma associação que não existe no schema.
