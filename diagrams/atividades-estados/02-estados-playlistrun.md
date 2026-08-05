# 02 — Diagrama de Estados: PlaylistRun

![Diagrama de Estados: PlaylistRun](02-estados-playlistrun.png)

```mermaid
stateDiagram-v2
    [*] --> running : start_generation()\ngeneration_service.py:118-123

    state running {
        [*] --> starting : progress_stage=starting\nprogress_percent=0

        starting --> interpreting_context : 0% → 8%\nLLM interpreta contexto do host\n(occasion + description)
        interpreting_context --> collecting_tastes : 8% → 20%\nCarrega snapshots e monta\nUserTasteProfile[]
        collecting_tastes --> discovering_context : 20% → 40%\nEnriquece candidatas via\nLast.fm + Spotify genres
        discovering_context --> ranking : 40% → 55%\nScoring individual/grupo +\nfairness + bridges
        ranking --> matching_spotify : 55% → 70%\nResolve candidatas no\ncatálogo Spotify
        matching_spotify --> creating_playlist : 70% → 90%\nCria playlist privada\nna conta do host
        creating_playlist --> finalizing : 90% → 97%\nCalcula métricas finais\n(compatibility + fairness)
    }

    running --> completed : complete_generation()\ngeneration_service.py:148-164\nprogress_stage=completed\nprogress_percent=100
    running --> failed : fail_generation()\ngeneration_service.py:167-177\nerror_message registrado

    completed --> [*]
    failed --> [*]
```

Este diagrama mapeia o ciclo de vida detalhado do registro `PlaylistRun` (`app/db/models.py:482-534`), que monitora e auditoria cada tentativa de geração do motor de recomendação (PNE).

### Racional Arquitetural e Transição Monotônica de Progresso

1. **Garantia de Progresso Monotônico (PB-13):**
   A função `update_generation_progress(db, run_id, stage)` em `generation_service.py:129-145` utiliza o dicionário de estágios `GENERATION_STAGES`:
   - `starting` (0%) → `interpreting_context` (8%) → `collecting_tastes` (20%) → `discovering_context` (40%) → `ranking` (55%) → `matching_spotify` (70%) → `creating_playlist` (90%) → `finalizing` (97%) → `completed` (100%).
   A instrução `if next_percent < run.progress_percent: return run` impede regressões visuais, garantindo que o progresso da barra exibida no frontend seja estritamente não-decrescente.

2. **Categorização de Erros e Recuperação (PB-17, PB-25):**
   Caso a esteira interrompa por exceção, a função `fail_generation()` anota o erro no campo `error_message` e altera o status para `"failed"`. O bloco `except` de `execute_generation()` captura e classifica o erro em quatro motivos acionáveis no cliente:
   - `reauth_required`: Exige nova autorização OAuth no Spotify.
   - `rate_limited`: Notifica tempo de espera (`retry_after` em segundos).
   - `insufficient_tracks`: Alerta que as escolhas dos membros resultaram em candidatos insuficientes.
   - `unavailable`: Trata indisponibilidades temporárias genéricas.

3. **Imutabilidade e Registro de Histórico:**
   Cada tentativa de geração gera uma nova instância de `PlaylistRun`, mantendo o histórico de auditoria preservado para análises de satisfação e feedback pós-playlist.
