# 03 — Geração de Playlist e Feedback

![Geração de Playlist e Feedback](03-erd-geracao-playlist-feedback.png)

```mermaid
erDiagram
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

    music_sessions ||--o{ vibe_check_answers : "coleta respostas de"
    music_sessions ||--o{ playlist_runs : "gera execuções de"
    playlist_runs ||--o{ playlist_run_tracks : "seleciona faixas para"
    
    playlist_runs ||--o{ member_track_feedback : "avaliação por faixa"
    playlist_runs ||--o{ playlist_feedback : "avaliação global"
    
    playlist_run_tracks }|..|{ track_context_cache : "consulta lógica via spotify_track_id"

```

Este diagrama enfoca a porção do sistema encarregada pela inteligência de recomendação, ciclo de geração de playlist e a retroalimentação de seus usuários.

O modelo central, `playlist_runs`, orquestra o ciclo de vida e andamento das gerações do motor de recomendação. A tabela é desenhada para acomodar estados de falha, execução ou sucesso (`status`: running, completed, failed), possuindo também rastreio da progressão via `progress_stage` e `progress_percent`. O registro consolida os relatórios descritivos da LLM (`explanation_json` e `llm_context_json`) que viabilizam o RF-05, RF-06 e as PBs atreladas à geração (PB-09 ao PB-17).

As faixas vinculadas a esta execução (`playlist_run_tracks`) realizam consultas à tabela de cache `track_context_cache`. É fundamental observar no diagrama o uso da relação pontilhada: isso representa uma busca lógica baseada no identificador `spotify_track_id` sem aplicar chave estrangeira (FK) real, visto que `track_context_cache` atua como cache independente para os dados enriquecidos que não devem falhar integridade por ações noutras tabelas.

A etapa final do domínio abrange as instâncias de feedback explícito, rastreadas em `member_track_feedback` (feedback detalhado da música) e `playlist_feedback` (satisfação da sala). Tais estruturas garantem unicidade das análises através de constraints específicas (como `uq_playlist_feedback_user_run`) que impedem duplo preenchimento do formulário. Adicionalmente, as notas (`representation_score` e `satisfaction_score`) possuem validação restrita com `CheckConstraint` exigindo valores de 0 a 5. Isto consolida inteiramente os RF-07, RF-08 e RF-09 relacionados aos resultados (PB-19) e avaliações dos membros (PB-20).
