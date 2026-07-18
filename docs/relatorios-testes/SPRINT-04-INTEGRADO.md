# Relatório de QA — Validação integrada da Sprint 4

**Data:** 2026-07-18 · **Branch:** `feat/SPRINT04/PB20` · **Autoridade:** Agente de Teste (QA)

## Veredito

**SPRINT 4 EM VALIDAÇÃO — EVIDÊNCIA E2E REAL PENDENTE (DIFERIDA POR LIMITAÇÃO DE API).**

Todos os PBs individuais (PB-03, PB-18, PB-19, PB-20) estão `VALIDADO` e a **parte automatizável** do
ciclo integrado passou, sem defeito aberto. A única pendência é a demonstração e2e **real**
(`CT-S4-INT-02`), que exige conta Spotify Premium. A assinatura `SPRINT 4 CONCLUÍDA` só sai após essa
demonstração.

## Escopo executado

Ciclo integrado `CT-S4-INT-01..05` com Spotify/LLM/Last.fm mockados, dirigindo o fluxo real via API
(`POST /rooms/{code}/generate`, `GET /rooms/{code}/result`, rotas de feedback, `POST /auth/logout`).
Reprodutor: [`backend/tests/test_s4_integration_qa.py`](../../backend/tests/test_s4_integration_qa.py).

| Caso | Resultado | Evidência |
|---|---|---|
| CT-S4-INT-01 — Last.fm melhora o contexto sem quebrar | **Aprovado** | Com Last.fm mockado, a geração conclui (202/completed) e o `track_context_cache` é populado com `source=lastfm_track_tags`/`confidence=0.95` e tags anexadas. Com Last.fm falhando, a cascata cai para `spotify_genres`/`consensus` e a geração conclui mesmo assim. |
| CT-S4-INT-02 — Sequenciador na playlist real | **Pendente (diferido)** | Não automatizável; exige conta Spotify real. A lógica de sequenciamento e a ordem persistida↔URIs foram validadas no PB-19 (unit/integração mockada). |
| CT-S4-INT-03 — Feedback vinculado à execução real | **Aprovado** | Após a geração concluir, o membro registra feedback por faixa e geral; persistidos e vinculados ao `run_id`/`user_id` corretos. |
| CT-S4-INT-04 — Regressão Sprints 1–3 | **Aprovado** | Suíte completa → **292 passed / 6 skipped / 0 failed** (298 coletados). |
| CT-S4-INT-05 — Logout durante fluxo ativo | **Aprovado** | Após logout, a sessão some do banco; `GET /result`, `GET /auth/me` e feedback com o mesmo token → **401**; nada persistido. Sem estado inconsistente. |

## Verificações complementares

- **Segurança/privacidade:** logout invalida a sessão no backend; ações subsequentes negadas;
  remoção de conta (PB-03) apaga também os feedbacks pessoais sem afetar terceiros (verificado no PB-20).
- **Persistência:** cache do Last.fm consistente com fonte/confiança; feedback vinculado ao run real.
- **Definition of Done:** motor/serviços com serviços externos mockados; sem segredos em testes/logs
  (a `LASTFM_API_KEY` não vaza — verificado no PB-18).

## Limitações conhecidas (não bloqueiam os casos automatizáveis)

- **CT-S4-INT-02 (e2e real)** e, herdada da Sprint 3, **CT-S3-INT-01** permanecem pendentes por
  exigirem contas Spotify Premium (Development Mode, ≤5 usuários, R-01).
- Last.fm e Ollama reais não exercitados; caminhos externos mockados e fallbacks exercidos.

## Dívida processual anterior (registrada)

As validações integradas das **Sprints 1 e 2** (`CT-S1-INT-*`, `CT-S2-INT-*`) nunca foram assinadas, e
a **Sprint 3** está `EM VALIDAÇÃO` (demo e2e real diferida). O incremento completo do MVP só pode ser
declarado após essas assinaturas e as demonstrações reais.

## Próxima ação

Conduzir as demonstrações e2e reais (`CT-S3-INT-01`, `CT-S4-INT-02`) com conta Spotify Premium e, em
paralelo, executar/assinar as integradas pendentes das Sprints 1–2. Só então emitir
`SPRINT 4 CONCLUÍDA — INCREMENTO VALIDADO`.

---

**SPRINT 4 EM VALIDAÇÃO — EVIDÊNCIA E2E REAL PENDENTE (DIFERIDA POR LIMITAÇÃO DE API)**
