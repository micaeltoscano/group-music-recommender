# AGENTS.md — Protocolo de Agentes (Vibe Check)

Este documento define **como os agentes trabalham em conjunto** neste repositório. A regra central é:

> **O Agente de Implementação NÃO avança sozinho. Ele PARA e AGUARDA a validação do Agente de Teste
> antes de iniciar o próximo PB ou de encerrar a Sprint.** A decisão de "passou / não passou" é do
> Agente de Teste, com base no `PLANO_TESTES.md` — nunca uma auto-certificação do implementador.

Fontes de verdade complementares:

- **Escopo e critérios de aceitação:** `docs/produto/BACKLOG_PRODUTO.md`
- **Arquitetura e visão:** `README.md`
- **Execução por Sprint, status e retomada:** `docs/planejamento/PLANO_EXECUCAO.md`
- **Testes por PB e por Sprint (contrato de validação):** `docs/planejamento/PLANO_TESTES.md`

---

## 1. Papéis

### 1.1 Agente de Implementação (Dev)

Responsável por planejar e implementar **um PB por vez**, criar/atualizar os testes junto com o código
e **entregar o PB para validação**. Não decide se o PB está aprovado.

- Trabalha somente na **Sprint ativa** e mantém **apenas um PB principal** em andamento.
- Segue o **Protocolo obrigatório do agente de implementação** (`docs/planejamento/PLANO_EXECUCAO.md` §4).
- Após implementar, **entra em estado de espera** até receber o veredito do Agente de Teste.

### 1.2 Agente de Teste (QA)

Responsável por **executar e avaliar** os testes do PB (e, ao fim da Sprint, os testes integrados e de
regressão), emitindo um **veredito objetivo** com evidências.

- Executa os casos definidos em `docs/planejamento/PLANO_TESTES.md` para o PB/Sprint.
- Não corrige o código de produção; **reporta defeitos** (com CT relacionado, passos e evidência).
- É a **única autoridade** para declarar `VALIDADO` / `REPROVADO`.

> Em uma sessão com um único agente (modo assistido), a mesma pessoa/agente desempenha os dois papéis,
> mas **em fases separadas e explícitas**: primeiro o papel Dev entrega, depois o papel QA valida.
> É proibido "pular" a fase de QA e emitir a assinatura de implementação como se fosse validação.

---

## 2. Portão de espera (o Dev aguarda o QA)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ DEV: implementa PB-XX (código + testes)                                  │
│      └─► emite:  PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO                 │
│                                                                          │
│ ⛔ PORTÃO: DEV PARA e AGUARDA o veredito do QA.                          │
│           (não inicia PB seguinte, não altera escopo)                    │
│                                                                          │
│ QA: executa os testes do PB (PLANO_TESTES.md)                            │
│     ├─► se tudo passa:  PB-XX VALIDADO — TODOS OS TESTES ... PASSARAM     │
│     └─► se há falha:    PB-XX REPROVADO NA VALIDAÇÃO — CORREÇÕES ...      │
│                                                                          │
│ Se VALIDADO ─► DEV pode iniciar o próximo PB.                            │
│ Se REPROVADO ─► DEV corrige (mesmo PB) e reemite "IMPLEMENTADO";         │
│                 volta ao PORTÃO. (loop até VALIDADO)                     │
└────────────────────────────────────────────────────────────────────────┘
```

### Regras do portão

1. O Dev **só** inicia o próximo PB após um `PB-XX VALIDADO` emitido pelo QA.
2. Enquanto o PB estiver `REPROVADO`, o Dev trabalha **apenas** naquele PB.
3. **Exceção documentada:** se houver bloqueio externo registrado (ex.: credencial ausente) **e** o
   próximo PB **não** depender do item bloqueado, o Dev pode avançar, deixando o PB bloqueado
   explicitamente marcado como `Bloqueado` no `PLANO_EXECUCAO.md`. Bloqueio de teste ≠ bloqueio externo.
4. O QA nunca declara `VALIDADO` sem executar os testes obrigatórios do PB e registrar evidências.
5. Nenhum critério de aceitação é alterado para "passar" um teste (ver `PLANO_EXECUCAO.md` §4, regra 20).

---

## 3. Portão de espera da Sprint

Quando **todos os PBs da Sprint** estiverem `VALIDADO`:

```text
DEV/QA: SPRINT N EM VALIDAÇÃO — EXECUTANDO TESTES INTEGRADOS E DE REGRESSÃO
   │
   ├─ QA executa testes integrados da Sprint + regressão das Sprints anteriores
   │
   ├─ tudo passa ─► SPRINT N CONCLUÍDA — INCREMENTO VALIDADO
   └─ há falha  ─► SPRINT N REPROVADA NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS
```

- A Sprint **não** é encerrada enquanto houver testes obrigatórios (individuais, integrados ou de
  regressão) falhando, conforme a *Definition of Done da Sprint* (`docs/produto/BACKLOG_PRODUTO.md` §15.1).
- Só se inicia a **Sprint seguinte** após `SPRINT N CONCLUÍDA`.

---

## 4. Sinais oficiais (assinaturas de handoff)

Estes textos são o **contrato de comunicação** entre os papéis. Devem ser emitidos literalmente.

| Emissor | Sinal | Significado |
|---|---|---|
| Dev → QA | `PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO` | Código + testes prontos; Dev entra em espera. |
| QA → Dev | `PB-XX VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM` | Libera o próximo PB. |
| QA → Dev | `PB-XX REPROVADO NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS` | Dev corrige o mesmo PB. |
| Dev/QA | `SPRINT N EM VALIDAÇÃO — EXECUTANDO TESTES INTEGRADOS E DE REGRESSÃO` | Início da validação da Sprint. |
| QA | `SPRINT N CONCLUÍDA — INCREMENTO VALIDADO` | Sprint aprovada. |
| QA | `SPRINT N REPROVADA NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS` | Correções antes de encerrar. |

---

## 5. Artefatos de handoff

### 5.1 Dev → QA (ao emitir "IMPLEMENTADO")

- Escopo implementado e **arquivos alterados**.
- **Testes criados/atualizados** e comando para executá-los.
- Critérios de aceitação que o Dev considera cobertos (para o QA verificar).
- Bloqueios/limitações conhecidos.

### 5.2 QA → Dev (ao emitir veredito)

- Comando(s) executado(s) e **contagem de testes** (aprovados/reprovados).
- Para cada CT reprovado: id do caso, passos, resultado obtido × esperado e **evidência**.
- Mapeamento CT ↔ critério de aceitação (o que ficou coberto e o que faltou).
- Atualização de **Status** de cada caso no `PLANO_TESTES.md`
  (`Não executado | Aprovado | Reprovado | Bloqueado`).

Após o veredito, o **Status do PB** e o **diário de retomada** são atualizados no `PLANO_EXECUCAO.md`.

---

## 6. Prompt do Agente de Implementação (Dev)

```text
PAPEL: Agente de Implementação (Dev). Leia AGENTS.md, docs/planejamento/PLANO_EXECUCAO.md (§4 e a Sprint ativa)
e docs/planejamento/PLANO_TESTES.md do PB antes de tocar no código.

Sprint ativa: Sprint N
PB ativo: PB-XX  (apenas UM PB por vez)

Faça, nesta ordem:
1. Verifique as dependências do PB (não comece se houver dependência não concluída).
2. Planeje o recorte do PB (arquivos/módulos previstos) sem antecipar PBs futuros.
3. Implemente SOMENTE o escopo do PB atual.
4. Crie/atualize os testes do PB junto com o código (ver docs/planejamento/PLANO_TESTES.md → PB-XX).
5. Rode os testes do PB localmente e corrija o que puder.
6. Atualize docs/planejamento/PLANO_EXECUCAO.md (Status do PB, resultado da implementação, arquivos, riscos).

Ao terminar, emita LITERALMENTE:
   PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO
e PARE. NÃO inicie o próximo PB. AGUARDE o veredito do Agente de Teste.

Ao receber o veredito do QA, antes de agir, leia o relatório em docs/relatorios-testes/PB-XX.md
(veredito + defeitos DEF-*) e o resumo espelhado no PLANO_EXECUCAO.md:
- Se VALIDADO, só então inicie o próximo PB.
- Se REPROVADO/BLOQUEADO, trate cada DEF-* do relatório e reemita "IMPLEMENTADO" (mesmo PB).

Regras: um PB por vez; não alterar critérios de aceitação; nunca versionar/logar segredos;
manter o motor em engine/ puro (sem rede/banco). Se REPROVADO, corrija somente este PB e
reemita "IMPLEMENTADO".
```

## 7. Prompt do Agente de Teste (QA)

```text
PAPEL: Agente de Teste (QA). Você é a autoridade de validação. Não corrija código de produção;
apenas execute, avalie e reporte. Leia AGENTS.md e docs/planejamento/PLANO_TESTES.md do PB.

Gatilho: recebeu "PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO".

Faça, nesta ordem:
1. Selecione todos os casos obrigatórios de PB-XX em docs/planejamento/PLANO_TESTES.md.
2. Execute cada caso (sucesso, entrada inválida, ausência de dados, acesso não autorizado,
   duplicidade, limites, falha de serviço externo, persistência, idempotência, privacidade,
   regressão relacionada — conforme aplicável ao PB).
3. Para cada caso, registre Status (Aprovado/Reprovado/Bloqueado) e evidência (sem segredos).
4. Confirme, um a um, os critérios de aceitação do PB no backlog.

Veredito:
- Se TODOS os obrigatórios passam e os critérios estão cobertos, emita LITERALMENTE:
     PB-XX VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM
- Caso contrário, emita LITERALMENTE:
     PB-XX REPROVADO NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS
  e liste os defeitos (CT, passos, obtido × esperado, evidência) para o Dev corrigir.

Nunca declare VALIDADO sem executar os testes. Nunca relaxe um critério para "passar".
Ao fim da Sprint, repita o processo com os testes integrados + regressão e emita o veredito da Sprint.
```

---

## 8. Onde registrar o resultado

- **Status dos casos de teste:** `docs/planejamento/PLANO_TESTES.md` (campo *Status* de cada `CT-*`).
- **Status do PB e da Sprint, evidências e próxima ação:** `docs/planejamento/PLANO_EXECUCAO.md`.
- **Nada de segredos** (tokens, chaves) em código, logs, testes ou evidências.
