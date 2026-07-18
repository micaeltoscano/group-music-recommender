# Relatório de QA — Validação integrada da Sprint 3

**Autoridade:** Agente de Teste (QA) · **Branch:** `feat/SPRINT03/PB17`

## Fechamento (2026-07-18) — validação e2e real diferida

**Assinatura oficial:** `SPRINT 3 EM VALIDAÇÃO — EVIDÊNCIA E2E REAL PENDENTE (DIFERIDA POR LIMITAÇÃO DE API)`.

Todos os PBs (PB-07, PB-14, PB-15, PB-16, PB-17) e a parte **automatizável** do ciclo integrado estão
`VALIDADO`, sem defeito Alta/bloqueante aberto (`DEF-S3-INT-03-01` fechado). O único critério de
encerramento em aberto é a **playlist real demonstrável de ponta a ponta** (`CT-S3-INT-01`): a
**validação está pendente e será feita futuramente devido a limitações de API** (conta Spotify
Premium / Development Mode, ≤5 usuários). Não há trabalho de código pendente — a lacuna é de
evidência/ambiente. A assinatura `SPRINT 3 CONCLUÍDA — INCREMENTO VALIDADO` só deve ser emitida após
essa demonstração real.

## Rodada 2 — revalidação após correção (2026-07-18)

**Veredito da parte automatizável: Aprovado** *(a conclusão formal da Sprint aguarda a e2e real acima).*

O Dev corrigiu `DEF-S3-INT-03-01` no commit `088597b` (`feat(PB-07): integrar Vibe Check ao ranking`):
novo motor puro `app/engine/vibe_scoring.py`, `execute_generation` agora consulta `vibe_check_answers`,
agrega as respostas (membros que pulam contam como neutro `0.5`; sem respostas → comportamento
anterior) e mistura um `vibe_score` ao `group_score` com influência limitada `VIBE_CHECK_INFLUENCE = 0.20`.
`valence` mapeia tolerância a tristeza (baixa penaliza faixas `sad`).

Verificação independente do QA:

- **Reprodutor original intocado** `tests/test_s3_integration_qa.py` — **5 passed** (o Dev não alterou
  este arquivo de QA); `CT-S3-INT-03` que antes reprovava **agora passa**: com `valence=0.0` as faixas
  `sad` caem no ranking em relação a `valence=1.0`.
- **Sondagem adversarial nova** `tests/test_s3_vibe_scoring_qa.py` — **6 passed**: influência limitada
  (0.20) **não inverte consenso forte** (faixa amada triste continua em 1º); pular preserva o ranking
  anterior; respostas parciais diluem o sinal sem quebrar; `valence` é monotônica para faixas tristes
  e neutra para não-tristes.
- **Regressão / suíte completa** `APP_ENV=test pytest` → **217 passed / 6 skipped / 0 failed**.

| Caso | Rodada 2 |
|---|---|
| CT-S3-INT-01 | Aprovado (parcial) — demo e2e **real** ainda pendente |
| CT-S3-INT-02 | Aprovado |
| CT-S3-INT-03 | **Aprovado** (defeito corrigido) |
| CT-S3-INT-04 | Aprovado (217 passed) |
| CT-S3-INT-05 | Aprovado |

`DEF-S3-INT-03-01`: **Fechado.** Nenhum defeito Alta/bloqueante aberto.

**Limitação remanescente (não bloqueia os casos automatizáveis):** a criação de playlist em conta
Spotify **real** variando a ocasião (`CT-S3-INT-01` "grupo real") ainda não foi demonstrada — Spotify
mockado em todos os testes; requer contas Premium autorizadas (Development Mode, ≤5 usuários, R-01).
O encerramento formal da Sprint no incremento demonstrável depende dessa evidência manual.

---

## Rodada 1 — validação inicial (2026-07-18)

**Veredito: SPRINT 3 REPROVADA NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS.**

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
