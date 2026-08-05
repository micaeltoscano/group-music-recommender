# 02 — Núcleo de Usuário, Sessão e Biblioteca

![Núcleo de Usuário, Sessão e Biblioteca](02-erd-nucleo-usuario-sessao.png)

```mermaid
erDiagram
    users {
        int id PK
        str spotify_id UK
        str display_name
        str image_url
        datetime created_at
        datetime updated_at
    }

    spotify_tokens {
        int user_id PK, FK
        str access_token
        str refresh_token
        datetime token_expires_at
        datetime refresh_token_expires_at
        datetime reauth_required_at
        str scopes
        datetime updated_at
    }

    app_sessions {
        uuid id PK
        int user_id FK
        str session_token_hash UK
        datetime expires_at
        datetime created_at
    }

    music_sessions {
        uuid id PK
        str code UK
        int host_user_id FK
        str occasion
        str description
        str mode
        str status
        datetime created_at
        datetime expires_at
    }

    music_session_members {
        uuid session_id PK, FK
        int user_id PK, FK
        str role
        datetime joined_at
    }

    user_music_snapshots {
        uuid id PK
        int user_id FK
        str time_range
        json top_tracks_json
        json top_artists_json
        datetime fetched_at
    }

    user_playlist_inventory {
        uuid id PK
        int user_id FK
        str spotify_playlist_id
        str access_type
        int tracks_total
        str snapshot_id
        datetime verified_at
    }

    user_music_library_snapshots {
        uuid id PK
        int user_id FK
        int track_count
        datetime built_at
        datetime last_sync_attempt_at
        str last_sync_error_code
        int last_sync_retry_after
    }

    user_music_library_playlist_states {
        uuid id PK
        uuid snapshot_id FK
        int user_id FK
        str spotify_playlist_id
        str playlist_snapshot_id
        str access_type
        int tracks_total
    }

    user_music_library_tracks {
        uuid id PK
        uuid snapshot_id FK
        int user_id FK
        str spotify_track_id
        str spotify_uri
        str track_name
        str artist_id
        str artist_name
        int position
    }

    user_music_library_sources {
        uuid id PK
        uuid library_track_id FK
        str source_type
        str source_ref
        str source_key
        int source_rank
        str access_type
        str playlist_snapshot_id
    }

    users ||--o| spotify_tokens : "possui (1:1)"
    users ||--o{ app_sessions : "mantém"
    users ||--o{ music_sessions : "hospeda"
    users ||--o{ music_session_members : "participa"
    music_sessions ||--|{ music_session_members : "integra"
    
    users ||--o{ user_music_snapshots : "gera"
    users ||--o{ user_playlist_inventory : "possui"
    users ||--o| user_music_library_snapshots : "mantém (1:1)"
    
    user_music_library_snapshots ||--o{ user_music_library_playlist_states : "contém estados"
    users ||--o{ user_music_library_playlist_states : "associa"
    
    user_music_library_snapshots ||--o{ user_music_library_tracks : "agrega faixas"
    users ||--o{ user_music_library_tracks : "associa"
    
    user_music_library_tracks ||--o{ user_music_library_sources : "deriva de"

```

Este diagrama detalha o subconjunto de tabelas responsável pela gestão do ciclo de vida do usuário, sessões do aplicativo e o gerenciamento de salas (grupos) e biblioteca musical pessoal.

A relação de composição entre `users` e `spotify_tokens` é estritamente 1:1, modelada com o comportamento de `cascade="all, delete-orphan"`, garantindo que não haja tokens órfãos caso o usuário seja deletado. Esse modelo atende ao RF-01 e PB-02 de autenticação de conta via Spotify.

Para a formação dos grupos, a associação (N:M) entre `users` e `music_sessions` é reificada na tabela associativa `music_session_members`. Esta possui uma **Chave Primária Composta** (`session_id`, `user_id`) que não só impede duplicidade de inscrições em uma mesma sala, como embute o atributo `role` ("host" ou "guest") e atende diretamente ao RF-02, PB-04 e PB-05 (criação e acesso às salas de recomendação).

A hierarquia da biblioteca (PB-30 a PB-34) reflete uma complexa engenharia de dados offline. Ela inicia no `user_music_library_snapshots` (limitada a 1:1 com o usuário, com exclusão em cascata). Dali derivam os estados de playlist (`user_music_library_playlist_states`) e os rastreios de música (`user_music_library_tracks`), garantindo idempotência durante a sincronização incremental da biblioteca. A rastreabilidade das origens se dá em `user_music_library_sources`.

Os dados obedecem a **UniqueConstraints** (como a de usuário e `time_range` em `user_music_snapshots` para RF-04/PB-08) e **CheckConstraints** rigorosas de validação de domínio. Por exemplo: limites de 0 a 500 no `track_count`, checagem de tipos de acesso a playlists em inventário (`access_type IN ('owned', 'collaborative')`), e ranqueamentos positivos (`position >= 1`).
