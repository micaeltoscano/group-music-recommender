# 03 — Diagramas de Estados: VibeCheckAnswer e PlaylistRunTrack

![Diagramas de Estados: VibeCheckAnswer e PlaylistRunTrack](03-estados-vibecheck-track.png)

## 3a — VibeCheckAnswer (Resposta do Vibe Check)

```mermaid
stateDiagram-v2
    direction LR

    [*] --> pending : Membro entra na sala\n(sem registro no banco)

    pending --> answered : POST /{code}/vibe-check\n(energy, valence, popularity)
    pending --> skipped : POST /{code}/vibe-check/skip

    answered --> skipped : POST /{code}/vibe-check/skip\n(zera métricas)
    skipped --> answered : POST /{code}/vibe-check\n(novos valores)
```

## 3b — PlaylistRunTrack (Faixa Candidata Resolvida)

```mermaid
stateDiagram-v2
    [*] --> Resolução : resolve_candidates()\ngeneration_service.py:180

    state Resolução {
        [*] --> matched : Spotify retorna resultado\nplayable com match_confidence ≥ 0.8\ne URI válida
        [*] --> discarded_missing : Candidata sem nome/artista
        [*] --> discarded_unavailable : Indisponível no mercado
        [*] --> discarded_search_error : Erro na busca do Spotify
        [*] --> discarded_no_results : 0 resultados encontrados
        [*] --> discarded_low_confidence : Confiança abaixo de 0.8
        [*] --> discarded_no_uri : Resultado sem URI
        [*] --> discarded_unplayable : Todos itens indisponíveis
    }

    state PósSeleção {
        matched_selected : status=matched (na playlist final)
        matched_artist_cap : status=discarded (discard_reason=artist_cap)
        matched_playlist_limit : status=discarded (discard_reason=playlist_limit)
    }

    matched --> PósSeleção : create_spotify_playlist_for_run()\n+ sequence_tracks()

    matched --> matched_selected : Selecionada pelo sequenciador
    matched --> matched_artist_cap : Excede limite por artista (máx 2)
    matched --> matched_playlist_limit : Excede tamanho da playlist (máx 30)
```

Este documento descreve os estados operacionais das duas entidades de apoio no processo de customização e recomendação.

### Detalhamento do Racional

1. **Estado Virtual `pending` em `VibeCheckAnswer` (PB-07, PB-29):**
   Para evitar a criação de linhas nulas ou desnecessárias, a ausência de um registro `VibeCheckAnswer` para a tupla `(session_id, user_id)` é interpretada pela API e pelo frontend como o estado virtual `"pending"`. Transições entre `"answered"` e `"skipped"` permitem que os membros alterem suas opções livremente antes da geração. Respostas em `"skipped"` possuem suas métricas salvas como `None`, assegurando que `load_vibe_preferences()` filtre apenas palpites ativos (`status == "answered"`).

2. **Duas Fases de Vida em `PlaylistRunTrack` (PB-10, PB-14, PB-19):**
   - **Fase de Resolução:** `resolve_candidates()` busca a faixa na API do Spotify e calcula a pontuação de similaridade de texto (`match_confidence`). Se `match_confidence >= 0.8`, a faixa avança como `"matched"`. Caso contrário, é marcada como `"discarded"` anotando o motivo exato em `discard_reason`.
   - **Fase de Pós-Seleção:** O sequenciador (`engine/sequencer.py`) impõe as regras de negócio de finalização (teto de no máximo 2 faixas por artista e limite da playlist de 20 a 30 faixas). Faixas que excedem esses tetos são reclassificadas de `"matched"` para `"discarded"` com `discard_reason="artist_cap"` ou `"playlist_limit"`, mantendo total transparência na auditoria.
