# 03 — Geração da playlist: do disparo pelo host à criação no Spotify (PNE)

![Geração da playlist pelo motor PNE](03-geracao-playlist-pne.png)

```mermaid
%%{init: {'sequence': {'mirrorActors': false}}}%%
sequenceDiagram
    actor Host
    participant API as API (rooms.py)
    participant Gen as GenerationService
    participant LLM as IA (LLM local)
    participant PNE as Motor PNE (engine/*)
    participant Spotify as Spotify
    participant LastFM as Last.fm
    participant DB as Banco (PlaylistRun, PlaylistRunTrack, snapshots)

    Host->>API: 1: POST /rooms/{code}/generate
    API->>Gen: 1.1: start_generation(db, code, host_id)
    Gen->>DB: 1.1.1: SELECT MusicSession WHERE code FOR UPDATE

    alt usuário não é o host
        Gen-->>API: RoomHostRequiredError
        API-->>Host: 403
    else geração já em andamento (room.status == "generating")
        Gen-->>API: GenerationConflictError
        API-->>Host: 409
    else início válido
        Gen->>DB: 1.1.2: room.status = "generating", CREATE PlaylistRun(status="running")
        Gen-->>API: run
    end

    API->>Gen: 2: execute_generation(db, run.id, host_id)
    activate Gen

    Gen->>DB: 2.1: update_generation_progress("interpreting_context")
    Gen->>LLM: 2.2: interpret_context(occasion, description)
    alt LLM disponível e resposta dentro do schema
        LLM-->>Gen: LLMContext{occasion, mood, energy, tags+/-, avoid}
    else LLM indisponível ou resposta inválida
        Gen->>Gen: 2.3: fallback_context() determinístico
    end
    Gen->>DB: 2.4: persiste llm_context_json no run

    Gen->>DB: 2.5: update_generation_progress("collecting_tastes")
    loop para cada integrante da sala
        Gen->>Spotify: 2.6: get_or_refresh_snapshot (top tracks/artists)
        alt snapshot com menos de 7 dias
            Note over Gen,DB: reutiliza UserMusicSnapshot em cache
        else snapshot vencido ou ausente
            Spotify-->>Gen: novos top tracks / top artists
            Gen->>DB: 2.6.1: upsert UserMusicSnapshot
        end
        Gen->>PNE: 2.7: new UserTasteProfile(member_id, tracks, artists, gêneros)
    end

    Gen->>PNE: 2.8: cluster_taste_profiles(profiles)
    PNE-->>Gen: TasteClusteringResult (subgrupos ou "evidência insuficiente")

    Gen->>PNE: 2.9: generate_candidate_pool(snapshots)
    PNE-->>Gen: CandidateTrack[] (+ descartadas com motivo)
    alt nenhuma candidata válida encontrada
        Gen-->>API: InsufficientTracksError
        API-->>Host: 422
    end

    Gen->>PNE: 2.10: enrich_candidate_genres(candidates, gêneros dos artistas)
    Gen->>LastFM: 2.11: enrich_candidates_context (tags por faixa → artista)
    alt Last.fm indisponível ou sem tags
        Note over Gen,LastFM: mantém gêneros do Spotify já anexados (RNF-08)
    end
    Gen->>DB: 2.12: update_generation_progress("discovering_context")
    Gen->>PNE: 2.13: discover_context_candidates(candidates, ContextCriteria)

    Gen->>DB: 2.14: update_generation_progress("ranking")
    Gen->>DB: 2.15: load_vibe_preferences (agrega VibeCheckAnswer "answered" da sala)
    Gen->>PNE: 2.16: _rank_candidates(candidates, profiles, mode, context, vibe_preferences, clusters)
    activate PNE
    PNE->>PNE: 2.16.1: calculate_group_score + calculate_vibe_score + evaluate_candidate_fairness
    opt bridge_tracks_enabled
        PNE->>PNE: 2.16.2: evaluate_bridge_candidate (músicas-ponte entre subgrupos)
    end
    PNE->>PNE: 2.16.3: elevate_least_represented (eleva o integrante menos representado)
    opt pool contextual habilitado
        PNE->>PNE: 2.16.4: blend_contextual_candidates
    end
    opt subgroup_balancing_enabled
        PNE->>PNE: 2.16.5: balance_subgroup_candidates
    end
    PNE-->>Gen: candidatas ranqueadas
    deactivate PNE

    Gen->>Spotify: 2.17: get_valid_access_token(host)
    Gen->>DB: 2.18: update_generation_progress("matching_spotify")
    Gen->>Spotify: 2.19: resolve_candidates → search_track (por candidata sem ID direto)
    Spotify-->>Gen: resultados de busca
    Gen->>PNE: 2.20: calculate_match_confidence(consulta, resultado)
    Gen->>DB: 2.21: CREATE PlaylistRunTrack (status matched | discarded, motivo)

    Gen->>DB: 2.22: update_generation_progress("creating_playlist")
    Gen->>PNE: 2.23: sequence_tracks(faixas casadas)
    PNE-->>Gen: ordem final (máx. 2 músicas/artista, 20–30 faixas)
    Gen->>Spotify: 2.24: create_playlist(host_token, nome, description, public=false)
    Spotify-->>Gen: playlist_id, playlist_url
    Gen->>Spotify: 2.25: add_items_to_playlist(playlist_id, uris)
    Gen->>DB: 2.26: persiste spotify_playlist_id/url no run

    Gen->>DB: 2.27: update_generation_progress("finalizing")
    Gen->>DB: 2.28: complete_generation → finalize_run_metrics (compatibility/fairness), run.status="completed", room.status="open"
    Gen-->>API: PlaylistRun concluído
    deactivate Gen
    API-->>Host: 202 PlaylistRunResponse

    alt falha em qualquer etapa (reauth necessário | rate limit | faixas insuficientes | serviço indisponível)
        Gen->>DB: 2.29: fail_generation(run, mensagem), room.status="open"
        Gen-->>API: PlaylistGenerationError(reason)
        API-->>Host: 401 | 429 | 422 | 502 conforme o motivo
    end
```

Este é o fluxo mais crítico do sistema: reproduz, passo a passo, a ordem real de
`generation_service.execute_generation`, único ponto onde os quatro atores (Host, Spotify, Last.fm e
LLM) e praticamente todas as entidades do PNE interagem na mesma transação de negócio. Representamos
o motor (`engine/*`) como um único participante "PNE" — em vez de uma lifeline por módulo
(`taste`, `scoring`, `fairness`, `clustering`, `bridge`, `subgroup_balance`, `sequencer`) — porque
essas chamadas são só código puro chamado em sequência pelo `GenerationService`, sem I/O nem estado
próprio (RNF-03/RNF-04); desenhar dez lifelines internas prejudicaria a leitura sem agregar
informação nova. Os blocos `opt` (bridge tracks, pool contextual, balanceamento de subgrupos) refletem
fielmente os parâmetros booleanos de `_rank_candidates`, que só executam essas etapas quando a
configuração do produto os habilita — é a mesma lógica dos `«extend»` do diagrama de casos de uso.
O `alt` final consolida os quatro motivos de falha tratados em `execute_generation`/`rooms.py`
(reautenticação, rate limit do Spotify, faixas insuficientes e indisponibilidade genérica), cada um
mapeado para um código HTTP diferente sem nunca expor detalhes internos ao host (RNF-02).
