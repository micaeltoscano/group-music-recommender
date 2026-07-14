# GEMINI.md — Guia para o agente Gemini (Vibe Check)

> Lido automaticamente pelo Gemini CLI na raiz do repositório. Aqui trabalha **um colaborador que
> usa só Gemini**, então o mesmo modelo faz **implementação** e depois **QA**, mas em **fases
> separadas e explícitas** — nunca aprove na mesma passada em que implementou.

## 1. Contexto do projeto

Vibe Check: grupo entra numa sala → define contexto → um motor de negociação gera uma playlist real
no Spotify. Execução **por Sprint**, **um PB por vez**. Fontes de verdade:

- Escopo/critérios: [`docs/produto/BACKLOG_PRODUTO.md`](docs/produto/BACKLOG_PRODUTO.md)
- Sprint ativa, ordem e status: [`docs/planejamento/PLANO_EXECUCAO.md`](docs/planejamento/PLANO_EXECUCAO.md)
- Testes por PB: [`docs/planejamento/PLANO_TESTES.md`](docs/planejamento/PLANO_TESTES.md)
- Divisão do trabalho: [`docs/planejamento/MAPA_TRABALHO.md`](docs/planejamento/MAPA_TRABALHO.md)
- Protocolo entre papéis: [`docs/agentes/PROTOCOLO.md`](docs/agentes/PROTOCOLO.md)
- Design (recriar, não copiar): [`docs/design/README.md`](docs/design/README.md)

## 2. Como pegar trabalho (divisão dinâmica, sem trilha fixa)

Não há trilha fixa. Você e o colega **seguem o plano da Sprint ativa** e cada um pega **~2 PBs
livres** de cada vez. Veja o que está livre e reivindique:

```bash
git checkout main && git pull
./scripts/orquestrar.sh --list --profile gemini            # o que está 🟢 LIVRE / feito / esperando
./scripts/orquestrar.sh --pb PByy --profile gemini          # faz o ciclo do PB (marca você como dono)
```

Regras para não colidir:
- Pegue PBs **🟢 LIVRE** que o colega ainda não pegou; **avise no chat** quais pegou.
- **Evite pegar dois PBs que mexem no mesmo arquivo** ao mesmo tempo — veja a tabela em
  [`docs/planejamento/MAPA_TRABALHO.md`](docs/planejamento/MAPA_TRABALHO.md) §2.
- **Migração Alembic:** avise antes de criar e encadeie na revisão mais recente (`down_revision`).
- Motor em `backend/app/engine/` é **puro** (sem rede/banco) — se pegar um PB do motor, mantenha assim.

## 3. Fluxo de um PB (você faz o PB inteiro)

Siga [`docs/agentes/AGENTE_IMPLEMENTACAO.md`](docs/agentes/AGENTE_IMPLEMENTACAO.md) na fase de código e
[`docs/agentes/AGENTE_TESTE.md`](docs/agentes/AGENTE_TESTE.md) na fase de QA.

```
1. git checkout main && git pull && git checkout -b feat/SPRINT-0X/PByy
2. Implemente SOMENTE o PB (código + testes). Motor puro, sem rede/banco.
3. Marque o Status do PB em PLANO_EXECUCAO.md como AGUARDANDO-QA e faça commit.
4. FASE DE QA (passe adversarial, como se não fosse você): rode os testes do PLANO_TESTES.md,
   tente quebrar (entradas inválidas, listas vazias, determinismo, ausência de I/O).
5. Escreva docs/relatorios-testes/PB-yy.md e marque o Status como VALIDADO ou REPROVADO.
6. Abra PR para main.
```

### Vocabulário de Status (primeira palavra do campo `- **Status:**`)
`A-FAZER` · `EM-IMPLEMENTACAO` · `AGUARDANDO-QA` (implementado, falta validar) · `REPROVADO` ·
`BLOQUEADO` · `VALIDADO` (só após o passe de QA). O texto após ` — ` é detalhe livre.

## 4. Orquestrador (perfil gemini — usa Gemini nas duas fases)

```bash
./scripts/orquestrar.sh --list --profile gemini            # painel: o que está livre/feito/esperando
./scripts/orquestrar.sh --pb PB-09 --profile gemini         # faz o ciclo do PB-09 (reivindica você)
./scripts/orquestrar.sh --pb PB-09 --profile gemini --dry-run  # simula, sem chamar Gemini
```

O `--pb` reivindica o PB (marca `EM-IMPLEMENTACAO — @vocês`), respeita dependências (recusa se um
pré-requisito não estiver `VALIDADO`) e avisa se o PB já tem outro dono (`--force` assume mesmo assim).

## 5. Regras inegociáveis

- Um PB por vez; só a Sprint ativa; respeite as dependências do campo `Dependências`.
- Testes exercitam comportamento/regra de negócio — não só "o endpoint existe".
- Motor em `engine/` **puro** (sem rede/banco); serviços externos **mockados** nos testes.
- **Nunca** versione/logue tokens ou segredos. **Não** faça push/merge em `main` sem revisão (PR).
- Não altere critérios de aceitação para "passar" um teste.
- **Frontend a partir do design:** toda tela vem de [`docs/design/`](docs/design/) — siga o screenshot
  do PB e use os **tokens já no** `frontend/src/index.css` (`var(--accent)`, etc.). Recrie em React,
  **não** embuta o HTML. Mapa tela↔PB: [`docs/design/development_guide.md`](docs/design/development_guide.md).
