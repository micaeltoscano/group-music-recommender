# Relatório de QA — Validação integrada da Sprint 3

**Data:** 2026-07-18 · **Branch:** `feat/SPRINT03/PB17` · **Autoridade:** Agente de Teste (QA)

## Veredito

**SPRINT 3 REPROVADA NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS.**

Motivo: `DEF-S3-INT-03-01` (Alta) — `CT-S3-INT-03` reprova. Um defeito Alta em critério de aprovação
da Sprint impede o encerramento (Plano de Testes §7 e §8).

## Escopo executado

Ciclo integrado `CT-S3-INT-01..05` com serviços externos (Spotify/LLM) mockados, exercitando o fluxo
real via API (`POST /rooms/{code}/generate`, `GET /rooms/{code}/result`). Reprodutor automatizado:
[`backend/tests/test_s3_integration_qa.py`](../../backend/tests/test_s3_integration_qa.py).

| Caso | Resultado | Evidência |
|---|---|---|
| CT-S3-INT-01 — E2E com playlist real | **Aprovado (parcial)** | 2 membros → 202/completed; run com `spotify_playlist_url`; ≥20 faixas `matched`; `GET /result` → 200; não-membro → 403. Demonstração e2e **real** (conta Spotify) pendente. |
| CT-S3-INT-02 — Contexto consumido pelo motor | **Aprovado** | Mesmos snapshots/modo; só a ocasião muda → ordem final das faixas muda ("festa" no topo vs "estudo" no topo); contexto interpretado difere. |
| CT-S3-INT-03 — Vibe Check influencia o ranking | **REPROVADO** | Ver `DEF-S3-INT-03-01`. |
| CT-S3-INT-04 — Regressão Sprints 1–2 | **Aprovado** | Suíte completa (exceto o novo arquivo integrado) → **201 passed / 6 skipped / 0 failed**. |
| CT-S3-INT-05 — Falha de serviço externo | **Aprovado** | LLM indisponível + 5 buscas sem resultado → 202/completed; contexto de fallback persistido; 5 descartes `No results`; ≥20 `matched`. |

Execução do arquivo integrado: **4 passed / 1 failed** (a falha é CT-S3-INT-03, por design, como
reprodutor do defeito).

## Defeito

### DEF-S3-INT-03-01 (Alta, Aberto) — Vibe Check não influencia o ranking

- **Sintoma:** com o mesmo grupo, pool e modo, um membro com `valence=0.0` (baixa tolerância a
  tristeza) e outro cenário com `valence=1.0` produzem **exatamente a mesma ordem** de faixas
  (soma das posições das faixas `sad` = 190 nos dois casos). Faixas tristes não são penalizadas.
- **Causa (confirmada por inspeção):** as respostas do Vibe Check são persistidas em
  `vibe_check_answers` (PB-07), mas `execute_generation`
  ([backend/app/services/generation_service.py](../../backend/app/services/generation_service.py))
  **nunca** consulta essa tabela, e nenhum módulo de `app/engine/` lê `valence`/`energy`/`popularity`.
  As preferências derivadas não alcançam o cálculo de score. É o mesmo padrão de `INC-PB17-CTX-01`
  (dado persistido, porém não consumido pelo motor), agora afetando o PB-07.
- **Impacto:** critério `CT-S3-INT-03` e a promessa do PB-07/PB-12 (`CT-PB12-07`) de que o Vibe Check
  ajusta o ranqueamento não são cumpridos. A funcionalidade parece integrada, mas não tem efeito.
- **Correção sugerida (Dev):** ler as respostas de Vibe Check da sala em `execute_generation` e
  propagá-las ao motor como um sinal de score adicional (ex.: penalizar tags/energia incompatíveis
  com `valence`/`energy`), com peso limitado — o Vibe Check ajusta na margem, não decide a playlist.
- **Reprodutor:**
  `backend/tests/test_s3_integration_qa.py::test_ct_s3_int_03_vibe_check_penaliza_faixas_tristes`.

## Verificações complementares

- **Segurança/privacidade:** não-membro recebe 403 em `GET /result`; regressão confirma tokens fora
  do frontend e explicações agregadas (CT-PB16-05).
- **Recuperação:** LLM indisponível e faixas não encontradas não interrompem a geração (CT-S3-INT-05).

## Limitações conhecidas (não bloqueantes)

- **Demonstração e2e real** (playlist criada em conta Spotify Premium variando a ocasião) permanece
  pendente — Spotify mockado em todos os testes; requer contas autorizadas (Development Mode, R-01).
- Ollama real não exercitado; fallback determinístico é exercido de fato.

## Próxima ação

Dev corrige `DEF-S3-INT-03-01` com testes e marca o item `AGUARDANDO-QA`. O QA então reexecuta
`CT-S3-INT-03` + regressão e, quando verde, conduz a demonstração e2e real (`CT-S3-INT-01`) antes de
emitir `SPRINT 3 CONCLUÍDA — INCREMENTO VALIDADO`.

---

**SPRINT 3 REPROVADA NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS**
