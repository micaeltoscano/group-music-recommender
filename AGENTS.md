# AGENTS.md — Como trabalhar neste repositório (Vibe Check)

> Este arquivo é lido automaticamente por agentes de código (Codex, Cursor e afins) na raiz do
> repositório. Se você é um modelo/assistente ajudando a **implementar**, leia isto **antes** de
> tocar no código. O contrato completo entre os papéis está em
> [`docs/agentes/PROTOCOLO.md`](docs/agentes/PROTOCOLO.md).

## 1. Como o trabalho é orquestrado

Dois papéis, que se comunicam **através do repositório** (git + documentos), nunca direto:

- **Implementação (Dev)** — você, o colega humano, ou o Codex. Implementa **um PB por vez**.
  Prompt completo do papel: [`docs/agentes/AGENTE_IMPLEMENTACAO.md`](docs/agentes/AGENTE_IMPLEMENTACAO.md).
- **Teste (QA)** — o Claude. Valida o PB, é a **única autoridade** para aprovar.
  Prompt completo: [`docs/agentes/AGENTE_TESTE.md`](docs/agentes/AGENTE_TESTE.md).

O script [`scripts/orquestrar.sh`](scripts/orquestrar.sh) automatiza o ciclo: ele **descobre sozinho
qual é o próximo PB** lendo o campo `Status` de cada PB no
[`docs/planejamento/PLANO_EXECUCAO.md`](docs/planejamento/PLANO_EXECUCAO.md), roda a fase certa
(implementação e/ou QA) e avança na ordem da Sprint ativa.

**Portão obrigatório:** o Dev **não inicia o próximo PB** sem um `VALIDADO` do QA daquele PB.

## 2. A regra que faz a detecção automática funcionar

O orquestrador não sabe *quem* fez o trabalho — ele lê o **campo `Status`** de cada PB. Por isso,
ao terminar de implementar um PB você **precisa deixar rastro no estado compartilhado**:

1. **Commit** do código do PB (mensagem no formato `feat(PB-XX): ...`).
2. No `PLANO_EXECUCAO.md`, no bloco `#### PB-XX`, marque a **primeira palavra** do campo Status:
   ```markdown
   - **Status:** AGUARDANDO-QA — <o que foi feito, em texto livre>
   ```
3. Emita literalmente: `PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO` e **pare**.

Se você não marcar o Status, o orquestrador trata o PB como `A-FAZER` e pode reimplementar por cima.

### Vocabulário de Status (a primeira palavra do campo)

| Token | Quando usar |
|---|---|
| `A-FAZER` | ninguém começou |
| `EM-IMPLEMENTACAO` | em andamento (opcional, para trabalho longo) |
| `AGUARDANDO-QA` | **você acabou de implementar**; falta a validação do QA |
| `REPROVADO` | o QA reprovou; corrija e volte para `AGUARDANDO-QA` |
| `BLOQUEADO` | bloqueio externo/dependência não satisfeita |
| `VALIDADO` | **só o QA escreve isto** |

O texto após ` — ` é livre (evidências, decisões). Só a **primeira palavra** é lida pela máquina.

## 3. Regras inegociáveis de implementação

Resumo do que mais importa (detalhe em `AGENTE_IMPLEMENTACAO.md`):

- **Um PB por vez.** Não antecipe PBs futuros; respeite dependências (campo `Dependências` do PB).
- **Só a Sprint ativa** (a linha `Em andamento` na tabela de Sprints do `PLANO_EXECUCAO.md`).
- **Testes junto com o código** — comportamento e regras de negócio, não só "o endpoint existe".
- **Nunca** versione/logue tokens, chaves ou segredos. Use mocks para Spotify/LLM/Last.fm nos testes.
- O motor em `backend/app/engine/` é **puro**: sem rede, sem banco, determinístico.
- **Não** faça push/merge na branch principal sem autorização explícita.
- **Não** altere critérios de aceitação para "passar" um teste. Não marque nada como `VALIDADO`.
- **Toda tela do frontend é construída a partir do design** em [`docs/design/`](docs/design/): siga o
  screenshot da tela do PB e use os **tokens já no** `frontend/src/index.css` (`var(--accent)`, etc.).
  Recrie em React — **não** embuta o HTML do protótipo. Mapa tela↔PB: [`docs/design/development_guide.md`](docs/design/development_guide.md).

## 4. Fluxo em uma frase

> Leia o PB no `PLANO_EXECUCAO.md` → implemente só ele + testes → marque `AGUARDANDO-QA` + commit →
> emita `PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO` → **pare** e aguarde o QA.
