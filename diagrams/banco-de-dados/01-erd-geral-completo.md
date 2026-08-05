# 01 — ERD Geral Completo

![ERD Geral Completo](01-erd-geral-completo.png)

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

    track_context_cache {
        uuid id PK
        str spotify_track_id UK
        str track_name
        str artist_name
        json lastfm_track_tags_json
        json lastfm_artist_tags_json
        json spotify_artist_genres_json
        json context_scores_json
        str source
        float confidence
        datetime fetched_at
    }

    vibe_check_answers {
        uuid id PK
        uuid session_id FK
        int user_id FK
        str status
        float energy
        float valence
        float popularity
        datetime created_at
        datetime updated_at
    }

    playlist_runs {
        uuid id PK
        uuid session_id FK
        str status
        str error_message
        str progress_stage
        int progress_percent
        str spotify_playlist_id
        str spotify_playlist_url
        int compatibility_score
        int fairness_score
        str explanation_json
        str llm_context_json
        bool subgroup_balancing_applied
        datetime created_at
        datetime updated_at
    }

    playlist_run_tracks {
        uuid id PK
        uuid run_id FK
        str candidate_id
        str spotify_id
        str spotify_uri
        str name
        str artist
        float match_confidence
        str discard_reason
        str status
        str source
        bool is_bridge
        int selection_rank
        datetime created_at
    }

    member_track_feedback {
        uuid id PK
        int user_id FK
        uuid playlist_run_id FK
        str spotify_track_id
        bool liked
        bool disliked
        bool more_like_this
        bool never_again
        datetime created_at
        datetime updated_at
    }

    playlist_feedback {
        uuid id PK
        int user_id FK
        uuid playlist_run_id FK
        int representation_score
        int satisfaction_score
        str comments
        datetime created_at
        datetime updated_at
    }

    users ||--o| spotify_tokens : "tem"
    users ||--o{ app_sessions : "mantém"
    users ||--o{ music_sessions : "hospeda"
    users ||--o{ music_session_members : "participa"
    music_sessions ||--|{ music_session_members : "possui"
    users ||--o{ user_music_snapshots : "gera"
    users ||--o{ user_playlist_inventory : "possui"
    users ||--o| user_music_library_snapshots : "mantém"
    
    user_music_library_snapshots ||--o{ user_music_library_playlist_states : "contém"
    users ||--o{ user_music_library_playlist_states : "associa"
    
    user_music_library_snapshots ||--o{ user_music_library_tracks : "agrega"
    users ||--o{ user_music_library_tracks : "associa"
    
    user_music_library_tracks ||--o{ user_music_library_sources : "origina de"
    
    music_sessions ||--o{ vibe_check_answers : "coleta"
    users ||--o{ vibe_check_answers : "responde"
    
    music_sessions ||--o{ playlist_runs : "executa"
    playlist_runs ||--o{ playlist_run_tracks : "inclui"
    
    users ||--o{ member_track_feedback : "avalia"
    playlist_runs ||--o{ member_track_feedback : "recebe"
    
    users ||--o{ playlist_feedback : "avalia"
    playlist_runs ||--o{ playlist_feedback : "recebe"

```

Este diagrama apresenta o schema geral e completo do banco de dados relacional PostgreSQL do projeto Vibe Check, totalizando **16 tabelas**. Houve uma evolução natural das 12 tabelas originais para as 16 atuais durante a Sprint 7, onde foram incluídas as features de biblioteca musical incremental (Product Backlog PB-30 ao PB-34).

As adições contemplam as tabelas `user_playlist_inventory`, `user_music_library_snapshots`, `user_music_library_playlist_states`, `user_music_library_tracks` e `user_music_library_sources`. Juntas, elas formam um subsistema robusto de sincronização em background que armazena referências incrementais das playlists e faixas favoritas do usuário, mantendo constraints rigorosas (como `track_count 0-500` e tipos de acesso restritos a `owned` ou `collaborative`).

Vale destacar que a tabela `track_context_cache` atua como um repositório de cache totalmente independente, não possuindo chave estrangeira (FK) apontando para outras tabelas estruturais. Ela se liga logicamente às faixas através da coluna `spotify_track_id`. O uso desse design otimiza a performance das requisições a APIs externas como Last.fm e Spotify.

As constraints de unicidade, como `uq_music_snapshot_user_range` e `uq_member_track_feedback_user_run_track`, mapeiam estritamente os requisitos de não-duplicação de avaliações e de limite de snapshot temporal definidos nos requisitos. Os tipos de dados e os relacionamentos de deleção em cascata garantem a integridade relacional quando sessões expiradas ou usuários são removidos.
