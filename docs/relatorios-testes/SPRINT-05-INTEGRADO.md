# Relatório de QA — Validação integrada da Sprint 5

**Data:** 2026-07-18 · **Branch:** `feat/SPRINT05/PB23` · **Autoridade:** Agente de Teste (QA)

## Veredito

**SPRINT 5 — parte automatizável VALIDADA.** Os quatro PBs (PB-21, PB-22, PB-23, PB-24) estão
`VALIDADO` individualmente e o ciclo integrado automatizável passou (`CT-S5-INT-01..03`). Nenhum
defeito aberto.

> A Sprint 5 é **pós-MVP** e todos os recursos são **opt-in** (flags off por padrão). Não há uma
> demonstração e2e real específica da Sprint 5 além das já diferidas nas Sprints 3–4. A assinatura
> formal `SPRINT 5 CONCLUÍDA — INCREMENTO VALIDADO` fica condicionada às demonstrações reais pendentes
> do incremento (contas Spotify).

## Contexto

Os quatro recursos da Sprint 5 — **Modo Descoberta** (PB-21), **agrupamento de perfis** (PB-22),
**faixas-ponte** (PB-23) e **balanceamento entre subgrupos** (PB-24) — são controlados por feature
flags desligadas por padrão. Como não havia casos `CT-S5-INT-*` definidos ("a definir no fechamento"),
o QA os definiu no `PLANO_TESTES.md` e os executou.

## Escopo executado

Reprodutor: [`backend/tests/test_s5_integration_qa.py`](../../backend/tests/test_s5_integration_qa.py),
dirigindo o fluxo real via API (`POST /rooms/{code}/generate`, `GET /rooms/{code}/result`) com
Spotify/LLM mockados e dois subgrupos reais (membros pop {1,2} e rock {3,4}, mais um "hino" comum).

| Caso | Resultado | Evidência |
|---|---|---|
| CT-S5-INT-01 — recursos compõem com todas as flags ligadas | **Aprovado** | Modo Descoberta + as três flags on: a geração conclui (202/completed); a candidata "hino" (comum aos dois subgrupos) é marcada **`is_bridge=true`**; `subgroup_balancing_applied` persistido; o resultado traz as explicações de **Descoberta** e de **faixa-ponte**. Os quatro recursos compõem sem quebrar o pipeline. |
| CT-S5-INT-02 — flags desligadas preservam o MVP | **Aprovado** | Com as flags no padrão (off): nenhuma faixa marcada como ponte, `subgroup_balancing_applied=false`, nenhuma explicação pós-MVP no resultado; a geração conclui normalmente. |
| CT-S5-INT-03 — regressão Sprints 1–4 | **Aprovado** | Suíte completa → **381 passed / 6 skipped / 0 failed**. |

## Verificações complementares

- **Composição real dos quatro recursos:** o agrupamento produz `clustered` a partir dos snapshots;
  a faixa comum a ambos os subgrupos é corretamente identificada como ponte; o balanceamento é avaliado
  sobre o prefixo; o modo Descoberta pondera novidade/diversidade. Tudo numa única geração real.
- **Isolamento por flag:** cada recurso só atua quando sua flag está ligada — confirmado pelo caso
  INT-02 (inércia total no padrão).
- **Sem regressão do MVP:** a suíte completa das Sprints 1–4 permanece verde.

## Limitações conhecidas (não bloqueiam os casos automatizáveis)

- **Demonstração e2e real** (playlist criada em conta Spotify com os recursos ligados) não executada —
  Spotify mockado; herda a mesma limitação das Sprints 3–4 (Development Mode, ≤5 usuários).
- Heurísticas iniciais (limiares de similaridade 0,35, aceitação de ponte 0,25, teto 0,60) são
  pós-MVP e passíveis de calibração antes de habilitação geral.

## Dívida processual do incremento (registrada)

Continuam pendentes: as demonstrações e2e reais das Sprints 3–4 (`CT-S3-INT-01`, `CT-S4-INT-02`) e as
validações integradas das Sprints 1–2 (`CT-S1-INT-*`, `CT-S2-INT-*`). O fechamento formal do produto
depende dessas assinaturas.

---

**SPRINT 5 — PARTE AUTOMATIZÁVEL VALIDADA; DEMONSTRAÇÃO E2E REAL DIFERIDA**
