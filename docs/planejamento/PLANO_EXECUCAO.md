# Plano de Execução — Vibe Check

Este arquivo é a **memória operacional** do projeto e a **linha oficial de execução por Sprint**.
O `BACKLOG_PRODUTO.md` define o escopo e os critérios de aceitação; o `README.md` descreve o
produto e a arquitetura; o `PLANO_TESTES.md` define como cada PB e cada Sprint são validados.
Aqui ficam a ordem de execução por Sprint, o trabalho atual e o ponto exato de retomada.

> **A execução é conduzida por Sprint.** Os marcos técnicos (M0–M5) foram preservados apenas
> como referência de entregas e riscos (ver seção 12) e **não** controlam mais a ordem principal
> de implementação. A ordem oficial segue as Sprints do backlog.

## 1. Objetivo do MVP

Entregar um fluxo no qual um grupo de até cinco pessoas:

1. autentica-se pelo Spotify;
2. cria ou acessa uma sala por código;
3. informa o contexto e o modo de consenso;
4. tem seus gostos musicais coletados;
5. recebe uma seleção que considera afinidade, rejeição e justiça;
6. gera uma playlist privada real na conta Spotify do host;
7. visualiza o resultado e uma explicação de representatividade.

## 2. Fontes de verdade

- **Escopo e aceitação:** `BACKLOG_PRODUTO.md`.
- **Visão e arquitetura:** `README.md`.
- **Plano de validação (testes por PB e por Sprint):** `PLANO_TESTES.md`.
- **Trabalho em andamento e retomada:** este arquivo.
- **Comportamento real:** código e testes automatizados.

Em caso de contradição, registrar a decisão neste arquivo e corrigir os documentos afetados na
mesma história, preservando os critérios de aceitação do backlog.

## 3. Fluxo obrigatório de execução

O agente de implementação deve seguir estritamente o fluxo abaixo, sem antecipar PBs futuros.

```text
Sprint atual
    ↓
PB da Sprint
    ↓
Planejamento do PB
    ↓
Implementação do PB
    ↓
Testes individuais do PB
    ↓
Correção das falhas
    ↓
Validação dos critérios de aceitação
    ↓
Próximo PB
    ↓
Testes integrados da Sprint
    ↓
Correções e regressão
    ↓
Encerramento da Sprint
```

## 4. Protocolo obrigatório do agente de implementação

1. Trabalhar somente na Sprint ativa.
2. Manter apenas um PB principal em andamento.
3. Ler completamente o PB antes de alterar o código.
4. Verificar dependências antes de iniciar.
5. Planejar o PB antes da implementação.
6. Implementar somente o escopo do PB atual.
7. Criar ou atualizar os testes junto com a implementação.
8. Executar os testes individuais do PB antes de avançar.
9. Corrigir todas as falhas relacionadas ao PB.
10. Validar cada critério de aceitação.
11. Atualizar a documentação e o status do PB.
12. Registrar comandos, resultados e evidências.
13. Não iniciar o próximo PB com testes obrigatórios falhando.
14. Ao terminar todos os PBs, executar os testes integrados da Sprint.
15. Executar testes de regressão das Sprints anteriores.
16. Não encerrar a Sprint enquanto houver falhas obrigatórias.
17. Atualizar o diário de retomada ao final de cada sessão.
18. Registrar a próxima ação de maneira objetiva e executável.
19. Não antecipar funcionalidades de PBs futuros.
20. Não alterar critérios de aceitação sem registrar e justificar a decisão.

### 4.1 Regras de trabalho complementares (preservadas)

- Implementar primeiro o menor fluxo verificável.
- Não iniciar extras antes de concluir o caminho principal do MVP.
- Toda história precisa cumprir seus critérios de aceitação e a Definition of Done do backlog.
- Criar testes junto com a funcionalidade, não apenas no final.
- Nunca versionar ou registrar tokens, chaves e segredos.
- Manter o motor em `engine/` puro, determinístico e sem banco ou rede.
- Registrar ideias novas no backlog sem interromper a história atual.
- Usar commits pequenos identificados pela história, por exemplo: `feat(PB-04): criar sala efêmera`.

### 4.2 Regra de parada entre PBs

Ao concluir a implementação de cada PB, o agente deve anunciar:

```text
PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO
```

Após executar e corrigir os testes individuais do PB:

```text
PB-XX VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM
```

Caso existam falhas:

```text
PB-XX REPROVADO NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS
```

O agente **não** deve iniciar outro PB enquanto o PB atual estiver reprovado, salvo quando existir
um bloqueio externo documentado e o próximo PB **não** depender do item bloqueado.

### 4.3 Regra de parada da Sprint

Ao finalizar todos os PBs da Sprint, o agente executa os testes integrados e informa:

```text
SPRINT N EM VALIDAÇÃO — EXECUTANDO TESTES INTEGRADOS E DE REGRESSÃO
```

Apenas quando todos os testes obrigatórios passarem:

```text
SPRINT N CONCLUÍDA — INCREMENTO VALIDADO
```

Caso contrário:

```text
SPRINT N REPROVADA NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS
```

## 5. Visão geral das Sprints

| Sprint | Objetivo | PBs | Pontos | Status |
|---|---|---|---:|---|
| Sprint 1 | Fundação técnica + autenticação + sala utilizável | PB-01, PB-02, PB-04, PB-05, PB-06, PB-08 | 25 | Validação integrada pendente |
| Sprint 2 | Núcleo do motor de negociação (PNE) | PB-09, PB-10, PB-11, PB-12, PB-13 | 24 | Validação integrada pendente |
| Sprint 3 | Fluxo principal ponta a ponta (playlist real + resultado) | PB-07, PB-14, PB-15, PB-16, PB-17 | 23 | **Encerrada operacionalmente por exceção do usuário — e2e real pendente, não VALIDADA** |
| Sprint 4 | Complementos da experiência | PB-03, PB-18, PB-19, PB-20 | 14 | **EM VALIDAÇÃO — integrada automatizável OK; e2e real (`CT-S4-INT-02`) diferida** |
| Sprint 5 | Expansão pós-MVP (fora do MVP) | PB-21, PB-22, PB-23, PB-24 | 18 | **PB-21..24 VALIDADOS; integrada automatizável OK (CT-S5-INT-01..03); e2e real diferida** |
| Sprint 6 | Estabilização e evolução contextual | PB-25, PB-26, PB-27, PB-28, PB-29 | 24 | Em validação paralela — implementação técnica concluída; aguardando QA |
| Sprint 7 | Biblioteca musical ampliada e eficiente | PB-30, PB-31, PB-32, PB-33, PB-34 | 24 | Em andamento — promovida pelo Product Owner em 2026-07-31 |

- **MVP (núcleo):** PB-01, PB-02, PB-04, PB-05, PB-06, PB-08, PB-09, PB-10, PB-11, PB-12, PB-13, PB-14, PB-15, PB-16, com as práticas de qualidade aplicadas continuamente pela **Definition of Done** (antigo PB-20 de "Qualidade" — ver `../produto/BACKLOG_PRODUTO.md` §15).
- **Sprint ativa:** Sprint 7, promovida por decisão explícita do Product Owner em 2026-07-31 e
  executada conforme [`SPRINT_07_IMPLEMENTACAO.md`](SPRINT_07_IMPLEMENTACAO.md). A Sprint 6 segue em
  validação paralela, sem dependência bloqueante para PB-30..34. **Próximo PB acionável:** definido
  automaticamente pelo campo `Status`
  de cada PB, na ordem de implementação da Sprint ativa (ver `AGENTS.md` e `scripts/orquestrar.sh`).
- **Exceção processual explícita:** em 2026-07-18, o usuário autorizou avançar para a Sprint 4 sem a
  demonstração e2e real da Sprint 3 e sem as assinaturas integradas das Sprints 1–2. A exceção libera
  implementação, mas **não** transforma evidência pendente em aprovação de QA nem autoriza emitir as
  assinaturas `SPRINT N CONCLUÍDA`. As dívidas de validação permanecem registradas.
- **Promoção do pós-MVP:** em 2026-07-18, após o QA validar individualmente todos os PBs da Sprint 4,
  o usuário determinou seguir para a Sprint 5. A decisão promove PB-21..24 e libera sua implementação
  ordenada, mas não equivale à assinatura integrada `SPRINT 4 CONCLUÍDA`; `CT-S4-INT-*` e as dívidas
  integradas anteriores continuam pendentes.

> **Convenção de Status (legível por máquina).** A **primeira palavra** do campo `- **Status:**` de
> cada PB é um *token* de um vocabulário fechado; o texto após ` — ` é detalhe humano livre. O
> orquestrador percorre a ordem da Sprint ativa e trata o **primeiro PB cujo token não é `VALIDADO`**.
>
> | Token | Significado | O orquestrador roda |
> |---|---|---|
> | `A-FAZER` | ninguém começou | Implementação → QA |
> | `EM-IMPLEMENTACAO` | em andamento | Implementação → QA |
> | `AGUARDANDO-QA` | implementado (por Dev/colega/Codex), falta validar | **só QA** |
> | `REPROVADO` | QA achou defeito | Implementação (correção) → QA |
> | `BLOQUEADO` | bloqueio externo/dependência | pula (verificar dependências) |
> | `VALIDADO` | fechado pelo QA | segue para o próximo PB |
>
> Ao **implementar** um PB, marque-o `AGUARDANDO-QA` e faça commit. O QA marca `VALIDADO`/`REPROVADO`.

---

## Sprint 1 — Fundação técnica, autenticação e sala utilizável

### Objetivo da Sprint

Ao final da Sprint 1 o grupo deve conseguir: autenticar-se pelo Spotify, criar uma sala por código
curto, entrar nela sem duplicidade, informar contexto e modo de consenso, e ter os dados musicais
(top tracks/artists) coletados e armazenados em snapshot — deixando a base pronta para o motor.

### PBs incluídos

- PB-01 — Fundação técnica do produto
- PB-02 — Autenticação com Spotify
- PB-04 — Criação de sala efêmera
- PB-05 — Entrada e acompanhamento da sala
- PB-06 — Contexto e modo de consenso
- PB-08 — Coleta e cache de dados musicais

### Dependências da Sprint

- **Externas (M0):** aplicativo criado no Spotify Developer Dashboard, `redirect_uri` local
  configurada, contas Premium autorizadas na demonstração (limite de 5 no Development Mode).
- **Técnicas:** Node.js ≥ 18 instalado no host (bloqueio atual do PB-01), Python 3.11.9 e Docker
  (já confirmados).
- **Entre PBs:** PB-02 depende de PB-01; PB-04 de PB-01 e PB-02; PB-05 de PB-02 e PB-04; PB-06 de
  PB-04; PB-08 de PB-02.
- **Spike técnico Spotify** (após PB-01, antes de aprofundar PB-02/PB-08): validar top tracks,
  top artists, Search, criação de playlist privada e o limite de 5 usuários. Registrar resultados
  no `README.md`.

### Ordem de implementação

1. PB-01
2. PB-02  *(spike técnico Spotify em conjunto)*
3. PB-04
4. PB-05
5. PB-06
6. PB-08

A ordem respeita as dependências declaradas no backlog.

### Execução dos PBs

#### PB-01 — Fundação técnica do produto

- **Status:** VALIDADO (QA revalidação 2026-07-14) — bloqueio de ambiente (Node) removido; CT-PB01-06 reexecutado e aprovado; todos os obrigatórios passam.
- **Objetivo:** base local integrada e reproduzível de frontend (React/Vite), backend (FastAPI) e
  banco (PostgreSQL) com SQLAlchemy/Alembic.
- **Dependências:** Nenhuma.
- **Critérios de aceitação:**
  1. [x] Frontend e backend iniciam conforme instruções documentadas. — Backend verificado; frontend
     nativo verificado com Node 24 (`vite` pronto em 59 ms e HTTP 200 em `127.0.0.1:5173`).
  2. [x] Backend conecta ao PostgreSQL.
  3. [x] Migração inicial do Alembic executa e reverte sem erro.
  4. [x] Configurações sensíveis vêm de variáveis de ambiente não versionadas.
- **Plano de implementação:** *(concluído)* scaffolds `backend/` e `frontend/`, `docker-compose.yml`
  (Postgres 16), SQLAlchemy 2.0 + Alembic (migração `0001_initial` → tabela `users`), endpoints de
  saúde, config via `pydantic-settings`, `.env.example` sem segredos e instruções no `README.md`.
- **Arquivos ou módulos previstos:** `backend/app/main.py`, `backend/app/config.py`,
  `backend/app/db/{base,session,models}.py`, `backend/app/api/health.py`,
  `backend/alembic/versions/0001_initial.py`, `frontend/src/{App.jsx,apiClient.js,main.jsx}`,
  `docker-compose.yml`, `.env.example`. *(todos existentes)*
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-01) — health/liveness, health/db OK,
  health/db indisponível (503 sem vazar detalhe), ciclo de migração ida/volta, ausência de segredos
  versionados, execução do frontend.
- **Evidências necessárias:** saída de `pytest`, saída do ciclo Alembic upgrade/downgrade/upgrade,
  respostas 200 de `/health` e `/health/db`, e (pendente) captura da tela de status do frontend em
  `http://localhost:5173`.
- **Riscos:** a assinatura final `PB-01 VALIDADO` ainda precisa ser reemitida pelo QA.
- **Bloqueios:** nenhum bloqueio técnico de implementação; Node.js/npm já estão instalados.
- **Resultado da implementação:** backend + banco + migração + frontend (scaffold que compila) prontos.
- **Resultado dos testes (2026-07-13):** `pytest` **4 passed**; Alembic `upgrade head` → `downgrade base`
  → `upgrade head` sem erros; `/health` e `/health/db` → 200; `.env` não rastreado e vazio;
  frontend `npm install` + `vite build` OK em container Node 20 (28 módulos, `dist/` gerado).
- **Validação QA (2026-07-13):** CT-PB01-01..05 **Aprovados** com evidência reforçada (servidor
  uvicorn real + Postgres 16 do Docker: `/`, `/health`, `/health/db` → 200; ciclo Alembic inspecionado
  no catálogo do Postgres — `users`/`ix_users_spotify_id` criados/removidos/recriados; `.env` git-ignored).
  **CT-PB01-06 Bloqueado** (Node/npm ausentes no host → frontend nativo não executável; critério 1 sem
  evidência). Defeitos: **DEF-PB01-01** (Média, bloqueio de ambiente) e **DEF-PB01-02** (Baixa, nomes de
  variáveis do `.env` divergem do `.env.example`). Relatório completo: `docs/relatorios-testes/PB-01.md`.
  **Veredito QA: PB-01 BLOQUEADO NA VALIDAÇÃO — EVIDÊNCIA INSUFICIENTE** (não há defeito de código;
  falta apenas comprovar o critério 1).
- **Evidência adicional do Dev (2026-07-13):** Node `v24.18.0`, npm `11.16.0`, `npm run build` OK
  (42 módulos), `npm run dev` OK e frontend nativo respondeu HTTP 200. O bloqueio ambiental foi removido.
- **Próxima ação exata:** nenhuma para o PB-01 (encerrado). Dev (Codex) pode puxar PB-04 e PB-08.

#### PB-02 — Autenticação com Spotify

- **Status:** VALIDADO (QA revalidação 2026-07-13) — reprovado na 1ª rodada, **aprovado na 2ª** após correções.
- **Revalidação QA (2026-07-13, 2ª rodada):** suíte completa **19 passed / 0 failed** (Postgres) e
  suíte QA **11/11 em SQLite** (tz corrigido). Defeitos Alta/Média **todos corrigidos**: DEF-PB02-01
  (refresh/reauth — CT-PB02-06a..d validam comportamento), DEF-PB02-02 (Fernet obrigatória no startup),
  DEF-PB02-03 (naive/aware normalizado), DEF-PB02-04 (`.env` corrigido → `SPOTIFY_CLIENT_SECRET`),
  DEF-PB02-05 (testes entregues), DEF-PB02-06 (302 + cookies via config + trata `error`). Remanescente:
  **DEF-PB02-07 (Baixa, aberto)** — scope creep `Home.jsx`, não bloqueia.
  **Veredito QA: PB-02 VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM.**
  Próxima ação: Dev liberado para o próximo PB da Sprint 1 (PB-04); e2e real (M0) e frontend nativo a
  demonstrar no fechamento da Sprint.
- **[Histórico] Validação QA (2026-07-13, 1ª rodada):** suíte `backend/tests/test_pb02_auth_qa.py` (criada pelo QA, mockada)
  → **11 passed / 1 failed** contra Postgres. Aprovados: CT-PB02-01 (redirect+state; obs.: 307≠302),
  CT-PB02-02 (CSRF→400), CT-PB02-03 (user idempotente + `/auth/me`), CT-PB02-04 (sem token em resposta),
  CT-PB02-05 (cifrado em repouso, com ressalva), CT-PB02-07 (regressão PB-01 verde; migração reversível).
  **Reprovado: CT-PB02-06** (refresh/reauth ausente). Defeitos: **DEF-PB02-01** (Alta — refresh/reauth
  não implementado), **DEF-PB02-02** (Alta — chave Fernet efêmera sem `FERNET_KEY` → tokens
  irrecuperáveis após restart), DEF-PB02-03 (Média — naive/aware quebra sessão em SQLite),
  DEF-PB02-04 (Média — `.env` com `CLIENT_SECRET` errado quebra OAuth real), DEF-PB02-05 (Média —
  entrega sem testes), DEF-PB02-06/07 (Baixa — 307≠302, valores hardcoded, sem tratar `error`;
  scope creep `Home.jsx`). Relatório: `docs/relatorios-testes/PB-02.md`.
  **Veredito QA: PB-02 REPROVADO NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS.**
- **Correções do Dev (2026-07-13):** implementados refresh central e persistência do novo access token;
  falha de refresh marca `reauth_required_at`; removida chave Fernet temporária; datas SQLite
  normalizadas para UTC; redirect/cookies parametrizados; consentimento negado tratado; nomes do
  `.env` local alinhados sem expor valores; testes técnicos adicionados em `test_pb02_auth.py`.
- **Resultado técnico:** `backend/.venv/bin/pytest backend/tests -q` → **16 passed**; frontend
  `npm run build` → sucesso (42 módulos); Vite nativo → HTTP 200. Nenhuma chamada real ao Spotify.
- **Próxima ação exata:** QA reexecuta CT-PB02-01..07, com atenção ao refresh bem-sucedido e falho,
  persistência Fernet após reinício e ausência de exposição de tokens.
- **[Status original do plano — mantido para referência]:** A fazer
- **Objetivo:** fluxo Spotify OAuth com proteção por `state`, sessão por cookie httpOnly e
  persistência criptografada de tokens somente no backend.
- **Dependências:** PB-01. Externas: app Spotify + `redirect_uri` (M0).
- **Critérios de aceitação:**
  1. Redirecionar o usuário para a autorização oficial do Spotify.
  2. O callback rejeita resposta com `state` ausente ou inválido.
  3. Autorização válida cria/atualiza o usuário e inicia sessão da aplicação.
  4. Access/refresh token não vão ao frontend nem a logs.
  5. Tokens armazenados criptografados em repouso.
- **Plano de implementação:** `GET /auth/login` (gera `state`), `GET /auth/callback` (valida `state`,
  troca code por tokens, cria/atualiza `users`, grava `spotify_tokens` cifrados com Fernet, cria
  `app_sessions` e cookie httpOnly), `GET /auth/me`. Refresh central no `SpotifyClient` e marcação de
  `reauth_required_at`. Migração para `spotify_tokens` e `app_sessions`.
- **Arquivos ou módulos previstos:** `backend/app/api/auth.py`, `backend/app/clients/spotify_client.py`,
  `backend/app/clients/crypto.py`, `backend/app/services/` (sessão), `backend/app/db/models.py`
  (novas tabelas), `frontend/` (tela de Login), nova migração Alembic.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-02) — CSRF por `state`, criptografia em
  repouso, token nunca no frontend/logs, criação/atualização de usuário, refresh e reauth.
- **Evidências necessárias:** logs sanitizados, inspeção do registro cifrado, resposta de `/auth/me`,
  teste de callback com `state` inválido.
- **Riscos:** R-01 (limite de 5 usuários), R-03 (refresh), R-08 (vazamento de tokens).
- **Bloqueios:** credenciais Spotify e `redirect_uri` (M0) precisam existir.
- **Resultado da implementação:** OAuth, sessão, criptografia persistente e refresh/reauth implementados.
- **Resultado dos testes:** 16 testes backend aprovados; build e servidor Vite nativo aprovados.
- **Próxima ação exata:** concluir M0 (app Spotify + redirect) e implementar `GET /auth/login`.

#### PB-04 — Criação de sala efêmera

- **Status:** VALIDADO (QA 2026-07-14) — CT-PB04-01..06 reexecutados pelo QA contra Postgres real
  (401 não-autenticado, 201 autenticado, 20 criações concorrentes com códigos únicos, host consistente,
  expiração de 24h, payload sanitizado); migração `0003` ida/volta/ida OK; regressão 27/27. Sem defeito
  de código. Commit concluído em `f87b220` (`feat(PB04): Criação de sala efêmera`). Relatório:
  `docs/relatorios-testes/PB-04.md`.
- **Objetivo:** criar sala temporária com código curto único, host como primeiro integrante e
  expiração de 24h.
- **Dependências:** PB-01 e PB-02.
- **Critérios de aceitação:**
  1. [x] Apenas usuário autenticado cria sala — sessão ausente/inválida retorna 401 e não persiste.
  2. [x] Cada sala recebe código curto único — formato `XXXX-XXXX`, `UNIQUE` no banco e retry após
     colisão; 12 criações concorrentes produziram 12 códigos distintos.
  3. [x] Criador registrado como host e primeiro integrante — sala e vínculo gravados no mesmo commit.
  4. [x] Expiração de 24h a partir da criação — diferença exata validada na resposta e persistência.
  5. [x] Retornar código e dados iniciais da sala — resposta 201 sanitizada com sala e host.
- **Plano de implementação:** `POST /rooms` cria `music_sessions` (code único, `host_user_id`,
  `status=open`, `expires_at = now + 24h`) e `music_session_members` (host). Geração de código
  colisão-resistente. Migração para `music_sessions` e `music_session_members`. Home cria a sala e
  exibe o código retornado sem antecipar lobby, join ou polling (PB-05).
- **Arquivos criados:** `backend/app/api/rooms.py`, `backend/app/services/{__init__,room_service}.py`,
  `backend/app/schemas/{__init__,rooms}.py`, `backend/alembic/versions/0003_pb04_rooms.py`,
  `backend/tests/test_pb04_rooms.py`.
- **Arquivos alterados:** `backend/app/db/models.py`, `backend/app/main.py`, `frontend/src/Home.jsx`,
  `frontend/src/apiClient.js`, `frontend/src/index.css`, este plano.
- **Migração:** `0003_pb04_rooms` (down revision `23f017f2fbb2`) cria `music_sessions` e
  `music_session_members`; downgrade remove primeiro os vínculos e depois as salas.
- **Decisões:** código usa alfabeto sem caracteres ambíguos e 8 símbolos em dois blocos; restrição
  única é a garantia final contra concorrência; sala+membro são atômicos; payload expõe apenas dados
  públicos da sala/host; entrada na sala e lobby permanecem fora deste PB.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-04) — só autenticado cria, unicidade do
  código, host como membro, `expires_at` = 24h, payload de retorno.
- **Comandos executados:** `pytest tests/test_pb04_rooms.py -q`; regressão PB-01/PB-02;
  `pytest tests -q`; `python -m compileall -q app tests`; `pip check`; `npm run build`; Alembic na revisão
  anterior: `upgrade head` → `downgrade 23f017f2fbb2` → `upgrade head`; `git add ...` (bloqueado
  pelo sandbox naquela sessão; commit concluído posteriormente em `f87b220`).
- **Resultado da implementação:** endpoint `POST /rooms`, persistência, autenticação, retry de código,
  resposta tipada/sanitizada e Home responsiva concluídos.
- **Resultado dos testes técnicos (2026-07-14):** PB-04 **8 passed / 0 failed**; regressão PB-01/PB-02
  **19 passed / 0 failed**; suíte completa **27 passed / 0 failed**; build Vite **42 módulos**;
  `compileall` e `pip check` sem falhas; migração PB-04 ida/volta/ida aprovada em SQLite isolado.
- **Resultados observados:** `POST /rooms` autenticado → 201; ausente/inválido → 401 sem escrita;
  12 criações concorrentes → 12 códigos únicos; colisão forçada recuperada sem registro parcial;
  resposta sem token/hash/dados de terceiro.
- **Critérios pendentes:** nenhum; validação independente concluída pelo QA.
- **Riscos e limitações:** limitações do sandbox da implementação foram encerradas pelo QA, que
  repetiu a concorrência e o ciclo Alembic no PostgreSQL alvo.
- **Bloqueios:** nenhum; validação QA e commit concluídos.
- **Próxima ação exata:** nenhuma para o PB-04 (encerrado).
- **Ponto de retomada:** PB-04 encerrado; PB-05 liberado pelas dependências.

#### PB-05 — Entrada e acompanhamento da sala

- **Status:** VALIDADO (QA 2026-07-15, commit `4061eb4`) — CT-PB05-01..07 executados e aprovados contra
  PostgreSQL isolado; sem defeitos, sem regressões. Relatório: `docs/relatorios-testes/PB-05.md`.
- **Objetivo:** entrar por código sem duplicidade, respeitar o limite de 5 integrantes, proteger o
  acesso (403 para não-membros) e atualizar a sala por polling.
- **Dependências:** PB-02 e PB-04.
- **Critérios de aceitação:**
  1. [x] Rejeitar código inexistente (404) ou sala expirada (410), sem criar vínculo.
  2. [x] Máximo de cinco integrantes; sexto ingresso recebe 409 inclusive sob concorrência real.
  3. [x] Mesmo usuário não é associado duas vezes; join repetido retorna o estado atual (200).
  4. [x] Só membros consultam a sala; não-membro recebe 403 sem payload da sala.
  5. [x] Interface atualiza por polling a cada 4s, dentro da faixa de 3–5s.
- **Plano de implementação:** *(concluído)* `POST /rooms/{code}/join` normaliza o código, trava a linha
  da sala no PostgreSQL, valida expiração/limite e trata duplicidade de forma idempotente;
  `GET /rooms/{code}` aplica guarda de membro e devolve somente dados públicos em ordem estável. Home
  cria/entra e navega ao lobby; Room mostra código, expiração, capacidade e membros com polling de 4s.
- **Arquivos criados:** `backend/tests/test_pb05_rooms.py`, `frontend/src/Room.jsx`.
- **Arquivos alterados:** `backend/app/api/rooms.py`, `backend/app/services/room_service.py`,
  `frontend/src/{App,Home,apiClient,index.css}`, este plano.
- **Migrações:** nenhuma; PB-05 reutiliza `music_sessions` e `music_session_members` da revisão
  `0003_pb04_rooms`, incluindo a PK composta `(session_id, user_id)`.
- **Decisões:** join duplicado é idempotente mesmo com a sala cheia; códigos digitados são normalizados
  para `XXXX-XXXX`; o limite concorrente usa `SELECT ... FOR UPDATE` por sala no PostgreSQL; a resposta
  lista apenas `user_id`, nome, imagem, papel e horário de entrada; contexto/modo permanecem no PB-06.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-05) — código inválido/expirado, 6º membro
  bloqueado, join duplicado idempotente, 403 para não-membro, atualização por polling.
- **Comandos executados:** `pytest tests/test_pb05_rooms.py -q` em SQLite e PostgreSQL isolado;
  `pytest tests -q`; `python -m compileall -q app tests`; `pip check`; `npm run build`; `npm run dev`
  + HTTP 200; Alembic no PostgreSQL isolado: `upgrade head` → `downgrade 23f017f2fbb2` → `upgrade head`.
- **Resultado da implementação:** rotas de join/leitura, autorização, concorrência, Home de entrada e
  lobby responsivo com polling concluídos, sem antecipar contexto, modo, Vibe Check ou geração.
- **Resultado dos testes técnicos (2026-07-15):** PB-05 **10 passed / 0 failed** (9 testes de
  API/regra em SQLite + 1 teste opt-in de concorrência no PostgreSQL, com 4 vagas preenchidas, 1
  rejeição e total final = 5); suíte local completa **36 passed / 0 failed / 1 skipped** (o teste
  PostgreSQL opt-in); build Vite **43 módulos**; servidor Vite respondeu HTTP 200; `compileall`,
  `pip check` e ciclo Alembic sem falhas.
- **Resultados observados:** join válido → 200 e membro persistido; inexistente → 404; expirada → 410;
  sexto → 409; repetido → 200 com um vínculo; não-membro no GET → 403 sem dados; leitura posterior
  reflete novo membro e leituras repetidas mantêm o mesmo estado.
- **Critérios pendentes:** nenhum — os cinco critérios foram comprovados pelo QA.
- **Validação QA (2026-07-15):** CT-PB05-01..07 **todos Aprovados** contra PostgreSQL isolado
  (`vibe_qa_pb05`) com servidor uvicorn real: join → 200 e convidado visível no GET; inexistente → 404;
  expirada → 410 (inclusive no limite exato); 6º → 409 com contagem final 5; join repetido → 200 com um
  único vínculo, mesmo com a sala cheia; não-membro → 403 sem qualquer dado da sala; 3 leituras
  byte-a-byte idênticas. **Concorrência real:** teste do Dev (5 disputantes) → 4/1/total 5 e teste QA de
  contenção pesada (20 disputantes) → 4/16/**total 5**. **Experimento de mutação:** removendo o
  `SELECT ... FOR UPDATE` só em memória, o total chega a **6** — provando que o lock é indispensável e
  que o teste detectaria a regressão. **Polling medido em navegador real (Chromium):** intervalos de
  **4002/4000 ms** (média 4001), dentro de 3–5s; reload mantém o estado; `clearInterval` no unmount sem
  vazamento. **Visual:** lobby fiel a `03-sala-lobby.png` no escopo do PB-05 (OCASIÃO/MODO são PB-06 e
  estão corretamente ausentes). Suíte completa **42 passed / 0 failed** (37 Dev + 5 QA) — sem regressão
  em PB-01/02/04; build Vite 43 módulos. Testes de QA em `backend/tests/test_pb05_rooms_qa.py`.
  **Defeitos: nenhum.** **Veredito QA: PB-05 VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM.**
- **Riscos e limitações:** polling medido apenas em Chromium headless (não em Safari/Firefox nem em aba
  em segundo plano); comparação com o design foi estrutural, não pixel a pixel; sessões semeadas no banco
  (OAuth real do Spotify fica para o fechamento da Sprint). O teste de concorrência depende de
  `TEST_DATABASE_URL` — sem ela é **pulado**; garantir essa variável na CI.
- **Bloqueios:** nenhum.
- **Próxima ação exata:** Dev liberado para o próximo PB da Sprint 1 — **PB-06** (dep. PB-04 ✔) e
  **PB-08** (dep. PB-02 ✔) estão livres. Após PB-06 e PB-08, executar os testes integrados da Sprint 1.
- **Ponto de retomada:** PB-05 encerrado pelo QA no commit `4061eb4`; Sprint 1 com PB-01, PB-02, PB-04 e
  PB-05 validados; faltam PB-06 e PB-08.

#### PB-06 — Contexto e modo de consenso

- **Status:** VALIDADO (QA 2026-07-16, commit `432a23c`) — CT-PB06-01..05 executados e aprovados;
  22 testes adicionais de QA em `backend/tests/test_pb06_rooms_qa.py`; suíte contra PostgreSQL real
  **74 passed / 0 skipped**; migração comprovada reversível no ciclo `0004 → 0003 → 0004`; testes do
  implementador validados por mutação (guarda de host e commit). Nenhum defeito bloqueante/alto/médio.
  Relatório: [`docs/relatorios-testes/PB-06.md`](../relatorios-testes/PB-06.md).
- **Objetivo:** permitir que **somente o host** defina ocasião/descrição e o modo (Democrático ou
  Festa Segura), disponibilizando as alterações na próxima atualização da sala.
- **Dependências:** PB-04.
- **Critérios de aceitação:**
  1. Somente o host altera contexto e modo. — cobertura técnica: host 200; membro 403 e estado intacto.
  2. Aceitar ocasião, descrição livre ou ambos. — as três combinações foram persistidas nos testes.
  3. Modo é Democrático ou Festa Segura. — ambos aceitos; valor fora do enum retorna 422 sem alteração.
  4. Alterações visíveis na próxima atualização da sala. — `GET` do membro devolve o novo estado e o
     frontend continua consultando a cada 4s.
- **Plano de implementação:** *(concluído)* `PUT /rooms/{code}/context` e
  `PUT /rooms/{code}/mode` com guarda de host; persistência de `occasion`, `description` e `mode`;
  enum fechado aos dois modos do MVP; exposição no `RoomResponse`; lobby React editável pelo host e
  somente leitura para membros.
- **Arquivos criados:** `backend/alembic/versions/0004_pb06_context_mode.py`,
  `backend/tests/test_pb06_rooms.py`.
- **Arquivos alterados:** `backend/app/db/models.py`, `backend/app/schemas/rooms.py`,
  `backend/app/services/room_service.py`, `backend/app/api/rooms.py`,
  `backend/tests/test_pb04_rooms.py`, `frontend/src/{Room.jsx,apiClient.js,index.css}`, este plano.
- **Migração:** `0004_pb06_context_mode` (down revision `0003_pb04_rooms`) adiciona as colunas
  nullable `occasion varchar(100)`, `description text` e `mode varchar(32)`; downgrade remove somente
  essas três colunas. A inspeção inicial confirmou que, apesar do texto anterior do plano, PB-04 não
  havia criado essas colunas no modelo nem no banco.
- **Decisões:** `PUT /context` substitui o par ocasião/descrição e exige ao menos um valor não vazio;
  textos são aparados e limitados a 100/1000 caracteres; o modo é armazenado pelos nomes públicos
  `Democrático`/`Festa Segura`; `Descoberta` não foi incluído por ser pós-MVP; o frontend preserva o
  rascunho do host durante o polling.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-06) — membro comum recebe erro apropriado,
  host altera, modo inválido rejeitado, propagação via polling.
- **Evidências necessárias:** resposta 403 para membro comum, persistência do contexto/modo.
- **Comandos executados:** `pytest tests/test_pb06_rooms.py -q`; `pytest tests -q` em SQLite e com
  `TEST_DATABASE_URL` no PostgreSQL local; `python -m compileall -q app tests`; `pip check`;
  `npm run build`; Alembic/PostgreSQL `current` → `upgrade head` → `downgrade 0003_pb04_rooms` →
  inspeção das colunas → `upgrade head` → inspeção final; `git diff --check`.
- **Resultado da implementação:** API, banco e lobby entregam edição host-only e leitura sincronizada
  de contexto/modo, sem incluir Vibe Check ou geração de playlist.
- **Resultado dos testes técnicos (2026-07-16):** PB-06 **10 passed / 0 failed**; suíte local
  **46 passed / 0 failed / 6 skipped** (casos PostgreSQL opt-in); suíte completa contra PostgreSQL
  **52 passed / 0 failed**; build Vite **43 módulos**; `compileall`, `pip check` e `git diff --check`
  sem falhas; Vite dev pronto em 60 ms e rota do lobby respondeu HTTP 200. Migração real comprovada
  em ciclo `0003 → 0004 → 0003 → 0004`, terminando em
  `0004_pb06_context_mode` com as nove colunas esperadas.
- **Resultados observados:** host altera contexto/modo com 200; membro recebe 403 nas duas rotas;
  modo inválido recebe 422; leituras do membro e após recarga mantêm os valores persistidos.
- **Critérios pendentes:** nenhum. CT-PB06-01..05 executados pelo QA em 2026-07-16 — todos aprovados;
  os quatro critérios de aceitação estão comprovados por evidência independente.
- **Resultado da validação (QA 2026-07-16):** VALIDADO. Autorização confirmada também contra
  não-membro, requisição anônima (401), sala inexistente (404) e host de outra sala; enum de modo
  resistiu a 8 variantes inválidas; limites 100/1000 verificados nas fronteiras. Observação
  OBS-PB06-01 (host consegue editar sala expirada, comportamento herdado do GET do PB-05, sem
  regressão introduzida aqui) encaminhada como decisão de produto, fora do escopo deste PB.
  Pendência não bloqueante: inspeção visual do lobby em navegador real contra `03-sala-lobby.png`.
- **Riscos e limitações:** frontend compilado e comparado estruturalmente com `03-sala-lobby.png`, mas
  ainda sem inspeção visual em navegador real nesta rodada; limites textuais adicionais não alteram os
  critérios. Spotify não é utilizado neste PB.
- **Bloqueios:** nenhum.
- **Próxima ação exata:** QA executa CT-PB06-01..05, incluindo autorização, persistência, polling e
  inspeção visual do lobby, e registra o veredito sem iniciar PB-08 antes disso.
- **Ponto de retomada:** código, testes, documentação, migração aplicada no PostgreSQL local e commit
  do PB-06 prontos; aguarda validação independente.

#### PB-08 — Coleta e cache de dados musicais

- **Status:** VALIDADO (QA 2026-07-16, commit `b662e52`) — CT-PB08-01..06 executados e aprovados;
  21 testes adicionais de QA em `backend/tests/test_pb08_music_snapshots_qa.py`; suíte contra
  PostgreSQL real **111 passed / 0 skipped**; migração comprovada reversível no ciclo
  `0004 → 0005 → 0004 → 0005`. Permanece aberto o **DEF-PB08-01 (Média)**: coleta concorrente do mesmo
  usuário devolve HTTP 500 por `IntegrityError` não tratado — sem corrupção de dados e sem defeito
  bloqueante/alto. Integração real com o Spotify **não** validada (tudo mockado).
  Relatório: [`docs/relatorios-testes/PB-08.md`](../relatorios-testes/PB-08.md).
- **Objetivo:** obter top tracks/artists via Spotify e armazenar snapshots com validade (default 7
  dias), reutilizando snapshots válidos e sinalizando reautenticação em falha de token.
- **Dependências:** PB-02.
- **Critérios de aceitação:**
  1. Consultar apenas endpoints Spotify autorizados no MVP. — cobertura técnica confirma somente
     `GET /me/top/tracks` e `/me/top/artists`, com escopo `user-top-read` já solicitado no OAuth.
  2. Faixas e artistas associados ao usuário em um snapshot. — JSON persistido com FK do usuário.
  3. Snapshot com menos de 7 dias reutilizado por padrão. — `GET /me/top` não chama o cliente externo.
  4. Snapshot vencido atualizado antes da geração. — registro existente é atualizado sem duplicação;
     `POST /me/refresh-music-snapshot` força coleta mesmo quando o cache está fresco.
  5. Falha de renovação de token marca necessidade de nova autenticação. — refresh central do PB-02
     grava `reauth_required_at` e a API responde 401 com instrução de novo login.
- **Plano de implementação:** *(concluído)* `GET /me/top` e
  `POST /me/refresh-music-snapshot`; persistência de `user_music_snapshots`; TTL configurável;
  integração com refresh central; coleta restrita a top tracks/artists; fallback para o último
  snapshot em 429 e resposta controlada quando não existe cache.
- **Arquivos criados:** `backend/app/api/music.py`, `backend/app/schemas/music.py`,
  `backend/app/services/music_service.py`,
  `backend/alembic/versions/0005_pb08_music_snapshots.py`,
  `backend/tests/test_pb08_music_snapshots.py`.
- **Arquivos alterados:** `backend/app/clients/spotify_client.py`, `backend/app/config.py`,
  `backend/app/db/models.py`, `backend/app/main.py`, `.env.example`, `README.md`, este plano.
- **Migração:** `0005_pb08_music_snapshots` (down revision `0004_pb06_context_mode`) cria tabela com
  UUID, FK `user_id`, `time_range`, `top_tracks_json`, `top_artists_json`, `fetched_at`, índice por
  usuário e unicidade `(user_id, time_range)`; downgrade remove índice e tabela.
- **Decisões:** manter um snapshot atual por usuário/faixa temporal e atualizá-lo em vez de acumular
  duplicatas; suportar `short_term`, `medium_term` e `long_term`; limite default 50; cache é fresco
  somente com idade estritamente menor que sete dias; 429 reutiliza snapshot existente (mesmo vencido)
  com aviso e preserva `Retry-After` quando não há cache; listas vazias formam snapshot válido com aviso.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-08) — reuso de snapshot fresco, refetch de
  vencido, falha de token → reauth, escopo de endpoints, resposta 429 mockada.
- **Evidências necessárias:** snapshot persistido, reuso vs refetch conforme idade, marcação de reauth.
- **Comandos executados:** `pytest tests/test_pb08_music_snapshots.py -q`; `pytest tests -q` em
  SQLite e com `TEST_DATABASE_URL` no PostgreSQL local; `python -m compileall -q app tests`;
  `pip check`; `npm run build`; Alembic/PostgreSQL `current` → `upgrade head` → inspeção da tabela e
  índices → `downgrade 0004_pb06_context_mode` → confirmação da remoção → `upgrade head`;
  `git diff --check`.
- **Resultado da implementação:** coleta e cache de tops integrados à autenticação, com payload
  sanitizado (sem tokens), persistência por usuário, atualização configurável e fallbacks controlados.
- **Resultado dos testes técnicos (2026-07-16):** PB-08 **16 passed / 0 failed**; suíte local
  **84 passed / 0 failed / 6 skipped**; suíte completa contra PostgreSQL **90 passed / 0 failed**;
  build Vite **43 módulos**; `compileall`, `pip check` e `git diff --check` sem falhas. Migração real
  comprovada em ciclo `0004 → 0005 → 0004 → 0005`, terminando em
  `0005_pb08_music_snapshots` com tabela, FK, PK, índice e unicidade esperados.
- **Resultados observados:** snapshot fresco não acessa Spotify; vencido é atualizado no mesmo ID;
  refresh falho grava reauth e responde 401; 429 usa cache ou responde 429 com `Retry-After`; tops
  vazios persistem sem crash; rotas sem sessão retornam 401.
- **Critérios pendentes:** nenhum. CT-PB08-01..06 executados pelo QA em 2026-07-16 — todos aprovados;
  os cinco critérios de aceitação estão comprovados por evidência independente.
- **Resultado da validação (QA 2026-07-16):** VALIDADO com um defeito Média em aberto. Verificados
  além do plano: isolamento entre usuários (snapshot de A não vaza nem serve de cache para B),
  fronteira exata do TTL (6d23h59 reusa; 7d01min recoleta), TTL vindo de configuração e não fixo no
  código, ausência de token na resposta e no snapshot persistido, aderência da marcação de reauth,
  `time_range` inválido → 422, e 429 no meio da coleta não gravando snapshot parcial. Escopo de
  endpoints confirmado por varredura: só `/v1/me` (PB-02) e `/v1/me/top/{tracks,artists}` (PB-08).
- **DEF-PB08-01 (Média, Aberto):** `get_or_refresh_snapshot` não trata `IntegrityError` no commit;
  duas coletas simultâneas do mesmo usuário/faixa fazem a perdedora retornar **HTTP 500**. Banco não
  corrompido (unicidade segura; 1 snapshot) e retry funciona. Corrigir com o padrão já usado em
  `join_room`. Recomendado corrigir **antes da validação integrada da Sprint 1**.
- **Limitação relevante:** integração real com o Spotify **não** foi validada — todos os caminhos
  externos são mockados. Necessária execução real com evidência sanitizada antes da demonstração.
- **Riscos e limitações:** integração real com contas Spotify/spike externo não foi executada nesta
  rodada; todos os caminhos externos usam mocks, conforme o plano. A documentação oficial consultada
  em 2026-07-16 confirma os endpoints, escopo, parâmetros e semântica de rate limit usados.
- **Bloqueios:** nenhum para validação mockada; credenciais/contas autorizadas são necessárias apenas
  para o teste real de demonstração/fechamento da Sprint.
- **Próxima ação exata:** QA executa CT-PB08-01..06, com atenção a cache, reauth, 429, payload vazio e
  migração PostgreSQL. Após `VALIDADO`, iniciar a validação integrada da Sprint 1, não outro PB.
- **Ponto de retomada:** código, testes, documentação e migração do PB-08 prontos; aguarda QA.

### Testes integrados da Sprint 1

Ver `PLANO_TESTES.md` → "Testes integrados da Sprint 1". Cobrem, no mínimo:

- Fluxo principal: login Spotify → criar sala → entrar por código → definir contexto/modo → snapshot pronto.
- Integração entre PBs: usuário autenticado (PB-02) vira host (PB-04) e coleta dados (PB-08).
- Autorização e controle de acesso: 403 para não-membro; só host altera contexto; só host cria sala.
- Persistência e consistência: sala, membros, contexto e snapshot sobrevivem a recarregamento/polling.
- Tratamento de erros: código inválido, sala expirada, 6º integrante, token expirado.
- Segurança: token nunca chega ao frontend; sem segredos versionados.
- Regressão: —  (primeira Sprint; sem Sprints anteriores).

### Critérios de encerramento da Sprint 1

A Sprint 1 só é concluída quando:

- [ ] todos os PBs obrigatórios (PB-01, PB-02, PB-04, PB-05, PB-06, PB-08) estiverem concluídos;
- [ ] todos os critérios de aceitação estiverem validados;
- [ ] todos os testes individuais dos PBs estiverem passando;
- [ ] os testes integrados da Sprint estiverem passando;
- [ ] os testes de regressão estiverem passando (n/a nesta Sprint);
- [ ] os bloqueios restantes estiverem documentados;
- [ ] o incremento (autenticar → sala → contexto → snapshot) puder ser demonstrado;
- [ ] este plano estiver atualizado com evidências e ponto de retomada.

### Evidências da Sprint 1

- Comandos executados: `pytest`, ciclo Alembic, `curl /health*`, `vite build` *(parciais — PB-01)*.
- Quantidade de testes / aprovados / reprovados: **4 / 4 / 0** (backend, PB-01).
- Endpoints verificados: `/`, `/health`, `/health/db` (200). *(Auth/rooms/music: pendentes.)*
- Telas verificadas: status do frontend (build em container). *(Login/Home/Room: pendentes.)*
- Migrações verificadas: `0001_initial` (users) — ida/volta.
- Integrações verificadas: Postgres (conexão). *(Spotify: pendente — spike.)*
- Limitações conhecidas: frontend nativo não executado (Node ausente); Spotify não integrado.
- Data da validação: 2026-07-13 (parcial — apenas PB-01).

### Status da Sprint 1

**Validação integrada pendente** — PB-01, PB-02, PB-04, PB-05, PB-06 e PB-08 VALIDADOS: todos os PBs da Sprint 1
passaram na validação independente (QA 2026-07-16). O próximo passo é a **validação integrada da
Sprint 1** (`CT-S1-INT-*` + regressão), ainda **não** executada — é um ciclo próprio e anunciado, que
o QA não iniciou junto com o PB-08.

Pendências que **não** bloqueiam os PBs individuais, mas devem ser tratadas antes de fechar a Sprint:

- **DEF-PB08-01 (Média, aberto):** coleta concorrente do mesmo usuário devolve HTTP 500; corrigir com
  o padrão de `join_room`. Ver [`docs/relatorios-testes/PB-08.md`](../relatorios-testes/PB-08.md).
- **Integração real com o Spotify nunca foi exercitada** — toda a validação do PB-02 e do PB-08 é
  mockada. Necessária execução real com credenciais autorizadas e evidência sanitizada antes da
  demonstração do incremento.
- **OBS-PB06-01:** host consegue editar sala expirada; decisão de produto pendente.

---

## Sprint 2 — Núcleo do motor de negociação (PNE)

### Objetivo da Sprint

Ao final da Sprint 2, para entradas fixas, o motor determinístico produz uma **seleção reproduzível**
com scores individuais e de grupo, tratamento de rejeição, métricas de justiça e os modos Democrático
e Festa Segura — **sem chamadas de rede** — e a geração é controlada por execução (Generation Lock).

### PBs incluídos

- PB-09 — Modelagem de gosto e compatibilidade
- PB-10 — Geração do conjunto de candidatas
- PB-11 — Pontuação individual e coletiva
- PB-12 — Rejeição, justiça e modos de consenso
- PB-13 — Controle e histórico da geração

### Dependências da Sprint

- **De Sprints anteriores:** PB-05 e PB-08 (snapshots/membros) para PB-09; PB-06 (contexto) para PB-10 e PB-13.
- **Entre PBs:** PB-10 depende de PB-09; PB-11 de PB-09 e PB-10; PB-12 de PB-11; PB-13 de PB-11.
- **Opcional:** PB-12 consome respostas do PB-07 quando disponível (não bloqueante).
- **Regra técnica:** o motor (`engine/`) permanece puro, determinístico e sem I/O.

### Ordem de implementação

1. PB-09
2. PB-10
3. PB-11
4. PB-12
5. PB-13

### Execução dos PBs

#### PB-09 — Modelagem de gosto e compatibilidade

- **Status:** VALIDADO — motor puro implementado com similaridade de Jaccard e ponderação de componentes; 6 testes passados.
- **Objetivo:** perfis individuais (faixas, artistas, gêneros) e compatibilidade normalizada e
  reprodutível, tratando listas vazias e grupo de 1.
- **Dependências:** PB-05 e PB-08.
- **Critérios de aceitação:**
  1. Modelo individual considera faixas, artistas e gêneros do snapshot.
  2. Trata listas vazias e grupo de um integrante.
  3. Compatibilidade normalizada e reprodutível para a mesma entrada.
  4. Sem chamadas de rede durante o cálculo.
- **Plano de implementação:** `engine/taste.py` (perfis + similaridade, ex.: Jaccard) recebendo dados já
  buscados; sem acesso a banco/rede.
- **Arquivos ou módulos previstos:** `backend/app/engine/taste.py`, testes em `backend/tests/`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-09) — grupo de 1, listas vazias,
  determinismo, ausência de I/O, faixa de valores [0,1].
- **Evidências necessárias:** testes unitários verdes com valores esperados.
- **Riscos:** R-13 (integrante sem dados).
- **Bloqueios:** precisa de snapshots (PB-08).
- **Resultado da implementação:** Criação de `UserTasteProfile`, `jaccard_similarity`, e cálculo de compatibilidade no `engine/taste.py`.
- **Resultado dos testes:** 6 testes criados em `test_pb09_taste.py` e validados com sucesso (`6 passed`).
- **Próxima ação exata:** Avançar para a PB-10 (Geração do conjunto de candidatas).ompatibilidade.

#### PB-10 — Geração do conjunto de candidatas

- **Status:** VALIDADO — implementação da extração e deduplicação do pool de candidatas a partir dos snapshots; 3 testes passados.
- **Objetivo:** montar pool de candidatas com contribuição de vários integrantes, deduplicado, com
  origem registrada e descarte motivado de candidatas sem identificação.
- **Dependências:** PB-06 e PB-09.
- **Critérios de aceitação:**
  1. Inclui contribuições de diferentes integrantes quando há dados.
  2. Sem duplicatas.
  3. Origem de cada candidata registrada.
  4. Candidatas sem identificação suficiente descartadas com motivo.
- **Plano de implementação:** montagem do pool a partir de top tracks/artistas fortes; deduplicação por
  identidade de faixa; registro de `source` e `discard_reason`.
- **Arquivos ou módulos previstos:** `backend/app/engine/candidates.py`, testes em `backend/tests/`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-10) — dedupe, cobertura de integrantes,
  registro de origem, descarte motivado.
- **Evidências necessárias:** pool sem duplicatas com origem e descartes registrados.
- **Riscos:** viés para a maioria na montagem (mitigado no PB-12).
- **Bloqueios:** depende de PB-09.
- **Resultado da implementação:** Criação de `generate_candidate_pool`, `CandidateTrack` e `DiscardedTrack` no `engine/candidates.py`.
- **Resultado dos testes:** 3 testes criados no `test_pb10_candidates.py` e validados com sucesso (`3 passed`).
- **Próxima ação exata:** Avançar para a PB-11 (Pontuação individual e coletiva).

#### PB-11 — Pontuação individual e coletiva

- **Status:** VALIDADO — implementação de pesos centrais e cálculo de pontuação (individual e de grupo) concluída; 4 testes passados.
- **Objetivo:** fórmulas configuráveis de score individual e de grupo, com pesos centralizados e
  resultados determinísticos e testados.
- **Dependências:** PB-09 e PB-10.
- **Critérios de aceitação:**
  1. Score individual considera afinidade de faixa/artista/gênero-ou-tag, popularidade e novidade.
  2. Score de grupo considera média, menor score, cobertura, contexto e diversidade.
  3. Pesos centralizados e configuráveis.
  4. Mesma entrada/config → mesmo resultado.
  5. Cálculos principais com testes automatizados de valores esperados.
- **Plano de implementação:** `engine/scoring.py` + `engine/weights.py` (pesos default do README §8);
  funções puras.
- **Arquivos ou módulos previstos:** `backend/app/engine/scoring.py`, `backend/app/engine/weights.py`, testes.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-11) — valores esperados, determinismo,
  sensibilidade a pesos, min/avg/coverage.
- **Evidências necessárias:** testes verdes com números esperados; pesos centralizados.
- **Riscos:** popularity bias; divergência de fórmula vs README.
- **Bloqueios:** depende de PB-09/PB-10.
- **Resultado da implementação:** Criação de `DEFAULT_INDIVIDUAL_WEIGHTS` e `DEFAULT_GROUP_WEIGHTS` no `weights.py`. Criação das fórmulas no `scoring.py`.
- **Resultado dos testes:** 4 testes criados no `test_pb11_scoring.py` cobrindo determinismo e valores esperados (`4 passed`).
- **Próxima ação exata:** Avançar para a PB-12 (Rejeição, justiça e modos de consenso).

#### PB-12 — Rejeição, justiça e modos de consenso

- **Status:** VALIDADO — implementação da penalidade de rejeição, least misery e representação mínima concluída; 6 testes passados.
- **Objetivo:** aplicar penalidade de rejeição, least misery, cobertura, representação mínima e os
  perfis de peso dos modos Democrático e Festa Segura.
- **Dependências:** PB-11. Opcional: PB-07 (respostas do Vibe Check como entrada, não bloqueante).
- **Critérios de aceitação:**
  1. Rejeição forte reduz o score mesmo agradando à maioria.
  2. Calcular satisfação média, menor satisfação, cobertura e fairness score.
  3. Democrático dá peso igual aos integrantes.
  4. Festa Segura favorece familiaridade e baixa rejeição.
  5. Seleção tenta elevar o integrante menos representado sem derrubar demais o grupo.
- **Plano de implementação:** `engine/fairness.py` (rejection_penalty, least misery, coverage, fairness,
  representação mínima) e perfis de modo em `weights.py`.
- **Arquivos ou módulos previstos:** `backend/app/engine/fairness.py`, `backend/app/engine/weights.py`, testes.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-12) — veto forte, least misery vs média
  (A=10,B=10,C=1), diferença entre modos, elevação do mínimo.
- **Evidências necessárias:** testes com grupos divergentes e vetos fortes.
- **Riscos:** R-12 (maioria domina), R-13 (dados ausentes).
- **Bloqueios:** depende de PB-11.
- **Resultado da implementação:** Criação de `fairness.py` implementando cálculo de justiça, penalidade de rejeição e o balanço do integrante menos representado. Adicionado perfis de modo no `weights.py`.
- **Resultado dos testes:** 6 testes criados no `test_pb12_fairness.py` cobrindo modos e penalidades (`6 passed`).
- **Próxima ação exata:** Avançar para a PB-13 (Controle e histórico da geração).

#### PB-13 — Controle e histórico da geração

- **Status:** VALIDADO — endpoint de controle (lock, estados transicionais, retry pós-falha) concluído; testes unitários passando.
- **Objetivo:** uma execução (`playlist_run`) por solicitação, com estados e Generation Lock que impede
  concorrência (409) na mesma sala.
- **Dependências:** PB-05, PB-06 e PB-11.
- **Critérios de aceitação:**
  1. Primeira solicitação válida cria execução `running`.
  2. Solicitação concorrente na mesma sala retorna 409.
  3. Execução concluída → `completed`; falha → `failed`.
  4. Após falha, o host inicia nova execução controlada.
  5. Cada geração concluída tem registro independente.
- **Plano de implementação:** `POST /rooms/{code}/generate` marca `session.status=generating` e cria
  `playlist_runs(status=running)` transacionalmente; 409 se já `generating`; transições de estado.
- **Arquivos ou módulos previstos:** `backend/app/api/rooms.py`, `backend/app/services/generation_service.py`,
  `backend/app/db/models.py` (`playlist_runs`), nova migração.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-13) — 409 concorrente, transições
  running/completed/failed, idempotência de clique, retry pós-falha.
- **Evidências necessárias:** resposta 409 sob concorrência; estados persistidos.
- **Riscos:** R-09 (gerações duplicadas).
- **Bloqueios:** depende de PB-11 e das rotas de sala.
- **Resultado da implementação:** Endpoint de controle em `generation_service.py` injetado no router de `/rooms/{code}/generate`. Implementado Lock pessimista para controle concorrente, criando nova migration e modelo `PlaylistRun` no db.
- **Resultado dos testes:** 4 testes unitários e de integração concluídos sem falhas para verificação de 409 e controle de Lock.
- **Próxima ação exata:** Iniciar a Sprint 3 com a PB-14 (Correspondência das músicas no Spotify).

### Testes integrados da Sprint 2

Ver `PLANO_TESTES.md` → "Testes integrados da Sprint 2". Cobrem, no mínimo:

- Fluxo do motor: snapshots (PB-08) → modelagem (PB-09) → pool (PB-10) → scores (PB-11) → justiça (PB-12)
  → execução controlada (PB-13), tudo determinístico e sem rede.
- Integração entre PBs: a saída de cada camada alimenta corretamente a próxima.
- Regressão da Sprint 1: autenticação, salas, contexto e snapshots continuam funcionando.
- Persistência: `playlist_runs` registra estado e resultados de forma consistente.
- Concorrência/idempotência: cliques repetidos em "gerar" → 409.
- Segurança/autorização: só host dispara geração; só membro consulta.

### Critérios de encerramento da Sprint 2

- [ ] PB-09, PB-10, PB-11, PB-12, PB-13 concluídos e critérios validados;
- [ ] testes individuais de cada PB passando;
- [ ] testes integrados da Sprint 2 passando;
- [ ] regressão da Sprint 1 passando;
- [ ] motor reproduzível para entradas fixas, sem chamadas externas;
- [ ] bloqueios documentados; incremento demonstrável; plano atualizado.

### Evidências da Sprint 2

- Comandos executados: — (a preencher)
- Testes / aprovados / reprovados: — (a preencher)
- Endpoints verificados: `POST /rooms/{code}/generate` (409). — (a preencher)
- Migrações verificadas: `playlist_runs`. — (a preencher)
- Limitações conhecidas: — (a preencher)
- Data da validação: — (a preencher)

### Status da Sprint 2

**Validação integrada pendente** — os PBs individuais estão `VALIDADO`, mas os casos
`CT-S2-INT-*` e a assinatura de encerramento da Sprint ainda não foram registrados.

---

## Sprint 3 — Fluxo principal ponta a ponta

### Objetivo da Sprint

Ao final da Sprint 3, o fluxo principal do MVP funciona de ponta a ponta: a seleção do motor vira uma
**playlist privada real na conta do host** (via Spotify Search com o token do host), com tela de
resultado e explicabilidade; o contexto do host é interpretado de forma estruturada (LLM com fallback)
e o Vibe Check opcional está disponível.

### PBs incluídos

- PB-07 — Vibe Check opcional
- PB-14 — Correspondência das músicas no Spotify
- PB-15 — Criação da playlist no Spotify
- PB-16 — Resultado e explicabilidade
- PB-17 — Interpretação estruturada do contexto

### Dependências da Sprint

- **De Sprints anteriores:** PB-05 e PB-06 para PB-07; PB-02, PB-11, PB-12, PB-13 para PB-14;
  PB-06 e PB-10 para PB-17.
- **Entre PBs:** PB-15 depende de PB-14; PB-16 depende de PB-13, PB-14 e PB-15. PB-07 e PB-17 são
  independentes do caminho da playlist dentro da Sprint.
- **Externas:** nenhuma chave paga — PB-17 usa Ollama local (`llama3.1:8b`); requer o Ollama
  instalado e o modelo baixado na máquina de desenvolvimento/demo, com fallback determinístico
  obrigatório caso o serviço local não esteja disponível.

### Ordem de implementação

1. PB-14  *(correspondência das candidatas no Spotify — abre o caminho da playlist)*
2. PB-15  *(criação da playlist real; depende de PB-14)*
3. PB-16  *(resultado e explicabilidade; depende de PB-14 e PB-15)*
4. PB-17  *(interpretação de contexto; tem fallback)*
5. PB-07  *(Vibe Check opcional; não bloqueia a geração)*

### Execução dos PBs

#### PB-07 — Vibe Check opcional

- **Status:** VALIDADO (QA revalidação integrada 2026-07-18) — correção de `DEF-S3-INT-03-01`
  confirmada independentemente. As respostas do Vibe Check são agregadas e consumidas pelo motor
  (`engine/vibe_scoring.py`) com influência limitada a 20%; `CT-S3-INT-03` passa (reprodutor QA
  intocado) e a sondagem adversarial `tests/test_s3_vibe_scoring_qa.py` (6 casos) confirma que o
  sinal não inverte consenso forte, preserva o "pular" e é monotônico em `valence`. Suíte completa
  217 passed / 6 skipped / 0 failed. Sem defeitos abertos.
- **Objetivo:** questionário curto (3–5 perguntas), pulável, cujas respostas viram preferências
  normalizadas (0–1) por usuário/sala, atualizáveis a cada nova resposta.
- **Dependências:** PB-05 e PB-06.
- **Critérios de aceitação:**
  1. Entre 3 e 5 perguntas.
  2. Usuário pode pular sem bloquear a geração.
  3. Respostas armazenadas por usuário e sala.
  4. Preferências derivadas entre 0 e 1.
  5. Nova resposta do mesmo usuário atualiza a participação seguinte.
- **Plano de implementação:** `GET/POST /rooms/{code}/vibe-check`; persistir `vibe_check_answers`.
- **Arquivos ou módulos previstos:** `backend/app/api/vibe_check.py`, `backend/app/db/models.py`,
  `frontend/` (Room — Vibe Check), migração.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-07).
- **Bloqueios:** nenhum.
- **Resultado da implementação:** Backend via FastAPI/SQLAlchemy (upsert no `VibeCheckAnswer`) e
  frontend React permitem responder ou pular. Correção integrada: novo motor puro
  `engine/vibe_scoring.py` agrega respostas por média, considera quem pulou como neutro, calcula
  adequação de energia, tolerância a melancolia e popularidade, e combina o sinal em 20% do score;
  afinidade, consenso, justiça e contexto preservam 80%. Sem respostas, o ranking anterior é mantido.
- **Decisão semântica da correção:** o campo legado `valence` é consumido como tolerância a conteúdo
  melancólico, conforme `CT-S3-INT-03`; o texto da pergunta foi alinhado a essa regra sem alterar API
  ou banco.
- **Arquivos da correção:** `backend/app/engine/vibe_scoring.py`,
  `backend/app/{engine/weights.py,services/generation_service.py,api/vibe_check.py}` e
  `backend/tests/test_s3_vibe_scoring.py`.
- **Migrações:** nenhuma.
- **Testes técnicos da correção:** testes focados PB-07/PB-12/PB-17 + ciclo integrado **40 passed**;
  ciclo integrado isolado + novos unitários **10 passed**; suíte completa **211 passed / 6 skipped /
  0 failed**; frontend Vite **45 módulos**; `compileall`, `pip check` e `git diff --check` aprovados.
- **Próxima ação exata:** QA reexecuta `CT-S3-INT-03`, `CT-PB12-07` e a regressão; se verde, mantém
  pendente somente a demonstração e2e real `CT-S3-INT-01` antes de encerrar a Sprint 3.

#### PB-14 — Correspondência das músicas no Spotify

- **Status:** VALIDADO — correspondência e match_confidence criados. Relatório de testes salvo.
- **Objetivo:** resolver candidatas via Spotify Search com o token do host, normalizar título/artista,
  validar disponibilidade e descartar ambíguos/indisponíveis; cada válida com identificador Spotify.
- **Dependências:** PB-02, PB-11, PB-12 e PB-13.
- **Critérios de aceitação:**
  1. Busca usa o mercado do token do host quando disponível.
  2. Título/artista normalizados (live, remastered, acoustic…).
  3. Abaixo da confiança mínima → descartado com motivo registrado.
  4. Indisponível no mercado do host → não selecionado.
  5. Cada música válida possui o identificador Spotify associado.
- **Plano de implementação:** track matching (normalização/variantes/confiança) em `SpotifyClient`;
  checagem de mercado; persistir candidatas resolvidas (`match_confidence`, `discard_reason`, `source`).
- **Arquivos ou módulos previstos:** `backend/app/clients/spotify_client.py`,
  `backend/app/services/generation_service.py`, `backend/app/db/models.py` (`playlist_run_tracks`), migração.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-14) — normalização de variantes, confiança
  mínima, indisponível no mercado, identificador associado.
- **Riscos:** R-02, R-04, R-05.
- **Bloqueios:** contas Spotify da demo; motor (PB-11/PB-12) e execução (PB-13).
- **Resultado da implementação:** — (não iniciado)
- **Próxima ação exata:** implementar track matching de candidatas com o token do host.

#### PB-15 — Criação da playlist no Spotify

- **Status:** VALIDADO — sincronizado com o veredito de QA já registrado em
  `../relatorios-testes/PB-15.md`: `PB-15 VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM`.
- **Objetivo:** criar playlist privada (20–30 faixas, máx. 2/artista) na conta do host a partir das
  músicas correspondidas, guardar id/URL na execução e devolver o link ao host.
- **Dependências:** PB-14.
- **Critérios de aceitação:**
  1. A playlist deve conter entre 20 e 30 músicas.
  2. No máximo duas músicas por artista.
  3. Playlist privada por padrão.
  4. `spotify_playlist_id` e URL armazenados na execução.
  5. O host recebe o link da playlist criada.
- **Plano de implementação:** criação de playlist + add items via `SpotifyClient`; aplicar cap de
  2/artista e faixa 20–30; persistir id/URL em `playlist_runs`.
- **Arquivos ou módulos previstos:** `backend/app/clients/spotify_client.py`,
  `backend/app/services/generation_service.py`, `backend/app/api/rooms.py`, `backend/app/schemas/rooms.py`,
  `frontend/src/Room.jsx`, `frontend/src/index.css`, migração.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-15) — cap de 2/artista, faixa 20–30,
  privada por padrão, id/URL persistidos, link retornado.
- **Evidências necessárias:** playlist criada de fato no Spotify do host; id/URL persistidos.
- **Riscos:** R-02, R-05.
- **Bloqueios:** integração real exige uma conta Spotify autorizada da demo; validação automatizada usa
  respostas mockadas, sem tokens reais.
- **Correção Dev (2026-07-17):** ligado o fluxo `POST /rooms/{code}/generate` a snapshots → pool →
  scoring/fairness → matching → criação privada → persistência → `completed`; sala com somente o host
  é válida; falha fica `failed` e libera retry; resposta traz ID/URL; frontend recebeu botão e estado
  `05-gerando.png`. O mínimo de 20, máximo de 30 e cap de 2/artista são aplicados antes do envio.
- **Migração corrigida:** o revision id original tinha 33 caracteres e não cabia em
  `alembic_version.version_num varchar(32)`; alterado para `0009_pb15_playlist`. Upgrade real no banco
  principal confirmado e ciclo `upgrade → downgrade 0008 → upgrade` validado em base temporária.
- **Arquivos alterados na correção:** `backend/alembic/versions/0009_pb15_playlist_run_spotify_id.py`,
  `backend/app/{api/rooms.py,schemas/rooms.py,services/generation_service.py}`,
  `backend/tests/{test_pb13_generation.py,test_pb15_playlist_creation_qa.py,test_pb15_generation_flow.py}`,
  `frontend/src/{Room.jsx,index.css}`, este plano, `PLANO_TESTES.md` e `README.md`.
- **Testes técnicos da correção:** PB-13/PB-15 **10 passed**; suíte completa **164 passed / 6 skipped**
  (os seis opt-in PostgreSQL); build Vite **45 módulos**; `compileall`, `pip check`, Compose e schema
  PostgreSQL verificados. Teste integrado mockado comprova host sozinho, 25 faixas, playlist privada,
  ID/URL persistidos e sala liberada.
- **Limitação:** CT-PB15-03 com Spotify real continua pendente de QA; mocks não provam a criação na
  conta real.
- **Próxima ação exata:** nenhuma no PB-15; a evidência real ponta a ponta integra a validação da
  Sprint 3, sem alterar o veredito histórico do PB.

#### PB-16 — Resultado e explicabilidade

- **Status:** VALIDADO — QA independente 2026-07-17, rodada 3 (ver `../relatorios-testes/PB-16.md`). Os 5 critérios de aceitação e os 6 casos obrigatórios `CT-PB16-01..06` estão atendidos com evidência real. Defeitos DEF-PB16-01/02/03/04 encontrados nas rodadas anteriores foram todos confirmados corrigidos, sem novos defeitos nesta rodada.
- **Objetivo:** tela de resultado com link da playlist, compatibilidade, fairness, representação por
  integrante e justificativas legíveis, sem expor dados sensíveis de terceiros.
- **Dependências:** PB-13, PB-14 e PB-15.
- **Critérios de aceitação:**
  1. Apresentar o link da playlist criada.
  2. Apresentar compatibilidade e fairness score da execução.
  3. Representação dos integrantes em formato compreensível.
  4. Cada música com justificativa resumida.
  5. Explicações não identificam rejeições/dados sensíveis de outro integrante.
- **Plano de implementação:** `GET /rooms/{code}/result`; montagem de `explanation_json`;
  tela Result no frontend com representação agregada e motivos por faixa.
- **Arquivos ou módulos previstos:** `backend/app/api/rooms.py`, `backend/app/services/`, `frontend/` (Result).
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-16) — presença do link/métricas,
  representação, privacidade das explicações, acesso restrito a membros.
- **Evidências necessárias:** payload de resultado; verificação de que nenhuma rejeição individual é exposta.
- **Riscos:** R-08 (privacidade nas explicações).
- **Bloqueios:** depende de PB-14 e PB-15.
- **Resultado da implementação:** endpoint `GET /rooms/{code}/result` + tela Result implementados.
  Correções desta sessão:
  - DEF-PB16-01: `compatibility_score`/`fairness_score`/`explanation_json` agora são calculados na
    conclusão do run (`complete_generation` → `result_service.finalize_run_metrics`) e persistidos em
    `playlist_runs` (colunas novas, migração `0010_pb16_run_metrics`); o endpoint só lê o que a execução
    calculou. Compatibilidade = % de faixas com 2+ contribuintes; fairness = índice de Jain sobre as
    contribuições por integrante — semânticas documentadas em `backend/app/services/result_service.py`.
  - DEF-PB16-02: `why_items` deixou de ser estático; é derivado das métricas reais da execução.
  - DEF-PB16-03: `reason` por faixa não nomeia mais integrantes individuais (texto agregado);
    `contributed_by` mantém o crédito positivo por integrante, por decisão de produto.
  Migração validada com upgrade/downgrade/upgrade em Postgres real (docker-compose). Suíte backend:
  172 passed, 6 skipped (11 específicos de PB-16, incluindo novo teste de persistência das métricas).
  Build do frontend OK.
- **Resultado da revalidação de QA (2026-07-17, rodada 2):** DEF-PB16-01/02/03 confirmados
  corrigidos de forma independente. Novo defeito: DEF-PB16-04 (Média) — `build_room_result` usa o
  snapshot de representação persistido na conclusão do run sem reconciliar com os membros atuais da
  sala; um integrante que entra depois do run concluído não aparece na própria representação.
  Evidência: `backend/tests/test_pb16_qa_revalidacao.py` (1 failed na suíte completa: 172 passed,
  6 skipped, 1 failed).
- **Correção de DEF-PB16-04 (2026-07-17):** `build_room_result` agora complementa a representação
  persistida com membros atuais da sala ausentes do snapshot (percentage 0), quando a leitura vem
  dos dados persistidos pela execução. Teste do QA que reproduzia o defeito
  (`test_pb16_qa_revalidacao.py`) passa. Suíte backend: 173 passed, 6 skipped (nenhuma regressão).
  Build do frontend OK.
- **Resultado da revalidação de QA (2026-07-17, rodada 3 — final):** DEF-PB16-04
  confirmado corrigido; testes adicionais do QA (`test_pb16_qa_revalidacao_r3.py`)
  provam ausência de duplicidade na representação e integridade do caminho legado
  (runs concluídos sem métricas persistidas). Nenhum novo defeito encontrado.
  Suíte completa: 175 passed, 6 skipped, 0 failed. Migração confirmada no head
  (`0010_pb16_run_metrics`) em Postgres real. Build do frontend OK.
- **Próxima ação exata:** nenhuma pendente para este PB; liberado para prosseguir com os
  próximos PBs da Sprint 3 (PB-07, PB-17) conforme `PROTOCOLO.md`.

**PB-16 VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM**

#### PB-17 — Interpretação estruturada do contexto

- **Status:** VALIDADO (QA revalidação independente 2026-07-18, rodada 3) — reabertura
  `INC-PB17-CTX-01` fechada. `CT-PB17-05` e `CT-S3-INT-02` reproduzidos pelo QA em pool misto realista
  e prova por mutação (contexto neutro → rankings idênticos), nos dois modos; `CT-PB17-06` confirma
  que o contexto (peso 0.15) não inverte consenso forte; `CT-PB17-01..04` verdes na regressão; suíte
  completa **201 passed / 6 skipped / 0 failed** (8 testes novos de QA em
  `backend/tests/test_pb17_qa_validador.py`). Sem defeitos abertos. Limitações registradas: Ollama
  real e reversibilidade da migração em Postgres não reexecutados nesta rodada; demonstração e2e real
  fica para o fechamento integrado da Sprint 3. Relatório:
  [`docs/relatorios-testes/PB-17.md`](../relatorios-testes/PB-17.md).
- **Objetivo:** LLM interpreta a descrição livre do host em um schema JSON validado, com fallback
  determinístico e sem enviar dados brutos de tops ao LLM.
- **Dependências:** PB-06 e PB-10.
- **Critérios de aceitação:**
  1. Saída segue schema JSON (ocasião, humor, energia, tags +/-, itens a evitar).
  2. Resposta inválida rejeitada sem interromper a geração.
  3. Sem LLM, segue com consenso/afinidade/popularidade.
  4. Dados brutos de tops não vão ao LLM.
  5. LLM não decide diretamente as músicas.
- **Plano de implementação:** `LLMClient` (Ollama local, modelo `llama3.1:8b`, via API HTTP
  `POST /api/generate` com `format=json` em `OLLAMA_BASE_URL`, padrão `http://localhost:11434`) +
  validação de schema + fallback; cache de contexto em `playlist_runs.llm_context_json`.
- **Arquivos ou módulos previstos:** `backend/app/clients/llm_client.py`, `backend/app/schemas/` (context),
  `backend/app/services/generation_service.py`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-17) — JSON inválido → fallback,
  LLM ausente → fallback, privacidade (sem dados brutos), schema válido e, obrigatoriamente,
  `CT-PB17-05` comprovando que contextos distintos alteram coerentemente scores/seleção.
- **Evidências necessárias:** logs sem dados brutos; fallback exercido; schema validado.
- **Riscos:** R-06 (LLM inválido/indisponível — inclui Ollama não instalado/rodando localmente ou
  modelo não baixado; fallback determinístico cobre todos esses casos).
- **Bloqueios:** nenhum bloqueio externo — requer apenas Ollama instalado localmente e o modelo
  `llama3.1:8b` baixado (`ollama pull llama3.1:8b`); sem Ollama disponível, o fallback determinístico
  assume automaticamente (não bloqueia o desenvolvimento nem a geração da playlist).
- **Resultado da implementação:** `LLMClient` implementado em
  [backend/app/clients/llm_client.py](../../backend/app/clients/llm_client.py) — chama
  `POST /api/generate` do Ollama local (`OLLAMA_BASE_URL`, `OLLAMA_MODEL=llama3.1:8b`) com
  `format=json`, valida a resposta contra o schema `LLMContext`
  ([backend/app/schemas/context.py](../../backend/app/schemas/context.py): ocasião, humor, energia,
  tags +/-, avoid) e cai no fallback determinístico (`fallback_context`, heurística por palavras-chave
  na ocasião/descrição) em qualquer falha — Ollama indisponível, timeout, HTTP de erro, JSON malformado
  ou fora do schema. Integrado em `execute_generation`
  ([backend/app/services/generation_service.py](../../backend/app/services/generation_service.py)):
  interpreta o contexto logo após confirmar os membros da sala (só `room.occasion`/`room.description`
  vão ao LLM — nunca snapshots/tops) e persiste em `playlist_runs.llm_context_json` (migração
  `0011_pb17_llm_context`, aplicada e revertida com sucesso em Postgres real). O motor de scoring já
  aceitava `context_score` desde o PB-11 (peso 0.05, neutro por padrão) — o LLM não decide músicas,
  só produz os critérios (critério 5).
- **Resultado dos testes:** `backend/tests/test_pb17_llm_context.py` (8 testes: schema válido, JSON
  malformado, JSON fora do schema, timeout, erro de conexão, erro HTTP, privacidade do payload
  enviado ao Ollama, e confirmação de que o peso de contexto no motor é baixo/neutro) +
  `backend/tests/test_pb17_generation_integration.py` (1 teste: pipeline completo persiste
  `llm_context_json` mesmo sem Ollama real disponível no ambiente). Ollama real não estava instalado
  neste ambiente — todos os testes usam `httpx.AsyncClient.post` mockado; o teste de integração roda
  contra o fallback real (sem mock do LLMClient), confirmando que a ausência do Ollama não trava nem
  atrasa a geração. Suíte completa: 184 passed, 6 skipped, 0 failed. Build do frontend OK (sem
  mudanças de frontend neste PB).
- **Resultado da revalidação de QA (2026-07-17, rodada 1):** critérios 1, 3, 4 e 5 confirmados
  atendidos de forma independente (incluindo inspeção direta do payload enviado ao Ollama para
  privacidade — CT-PB17-04). Defeito novo: DEF-PB17-01 (Alta) — em `_call_ollama()`
  ([backend/app/clients/llm_client.py:64-71](../../backend/app/clients/llm_client.py#L64-L71)),
  `body.get("response")` assume que o envelope JSON decodificado é um `dict`, sem checar. Se o Ollama
  responder HTTP 200 com um corpo JSON válido mas de outro tipo (lista, string, número), `.get(...)`
  levanta `AttributeError`, não capturada por `interpret_context` (só trata
  `LLMUnavailableError`/`LLMInvalidResponseError`), e propaga até `execute_generation`, que retorna
  **502 Bad Gateway** — quebrando a geração real da playlist. Confirmado de ponta a ponta via API
  (não só no `llm_client` isolado). Evidência: `backend/tests/test_pb17_qa_revalidacao.py` (4 failed
  na suíte completa: 184 passed, 6 skipped, 4 failed).
- **Correção de DEF-PB17-01 (2026-07-17):** aplicadas as duas correções sugeridas pelo QA, em camadas:
  (1) `_call_ollama` agora valida `isinstance(body, dict)` antes de `.get("response")`, levantando
  `LLMUnavailableError` (não `AttributeError`) para qualquer envelope de tipo inesperado; (2)
  `interpret_context` ganhou um `except Exception` de último recurso, logando e caindo no fallback
  determinístico para qualquer falha não prevista relacionada ao LLM — reforço estrutural para que o
  critério 2 ("sem interromper a geração") seja garantido mesmo que uma classe de erro futura e não
  antecipada apareça. Os 4 testes do QA que reproduziam o defeito
  (`test_pb17_qa_revalidacao.py`, incluindo o teste fim a fim via API) agora passam. Suíte backend:
  188 passed, 6 skipped, 0 failed (nenhuma regressão). Build do frontend OK.
- **Resultado da revalidação de QA (2026-07-17, rodada 2 — final):** DEF-PB17-01
  confirmado corrigido; sondagem adicional em variações do conteúdo de `response`
  (vazio, nulo, não-string, JSON de lista) e em chamadas concorrentes não
  encontrou novos defeitos. Verificado que `fallback_context` roda fora do
  `try/except` de `interpret_context`, mas o único ponto de chamada real
  (`execute_generation`) sempre passa `str | None` (colunas SQLAlchemy) — não é
  um risco acionável em produção. Suíte completa: 188 passed, 6 skipped, 0
  failed. Migração confirmada no head (`0011_pb17_llm_context`) em Postgres
  real. Build do frontend OK. Os 5 critérios de aceitação atendidos.

##### Reabertura por lacuna de integração — INC-PB17-CTX-01

- **Evidência funcional:** em teste real com mais de um usuário, alterar ocasião/descrição não
  alterou materialmente a playlist; o conjunto final continuou derivado dos mesmos top tracks.
- **Causa confirmada por inspeção:** `execute_generation` persiste `llm_context_json`, porém
  `_rank_candidates` não recebe o contexto interpretado; `calculate_group_score` usa
  `context_score=1.0` neutro por padrão e os dois modos ativos configuram peso de contexto `0.0`.
- **Contradição que motivou a reabertura:** `CT-PB17-05` e `CT-S3-INT-02` exigem que o contexto
  influencie candidatas/scores, mas a rodada histórica tratou `CT-PB17-05` como “não aplicável”.
- **Escopo da correção:** conectar critérios estruturados ao motor determinístico, sem permitir que
  o LLM escolha músicas diretamente; oferecer fallback contextual determinístico sem Last.fm.
- **Fora do escopo:** PB-18 permanece na Sprint 4 para enriquecer tags/confiança via Last.fm;
  PB-11 e PB-12 permanecem `VALIDADO` e entram apenas na regressão da correção.
- **Portão:** a Sprint 3 não pode ser encerrada até `CT-PB17-05` e `CT-S3-INT-02` passarem, além da
  regressão dos casos anteriormente aprovados do PB-17.
- **Próxima ação exata:** Dev implementa somente a correção do PB-17 com testes; ao concluir, marca
  `AGUARDANDO-QA` e emite o handoff oficial para uma nova validação independente.

##### Implementação da correção — handoff do Dev em 2026-07-17

- `engine/context_scoring.py` transforma o schema validado em um `context_score` puro e
  determinístico por candidata. Ocasião/humor/tags definem afinidade temática, energia é comparada
  com sinais conservadores de gênero e `tags_negative`/`avoid` aplicam penalidades.
- Os gêneros dos top artistas já existentes nos snapshots enriquecem cópias das candidatas; nenhum
  dado adicional é enviado ao LLM e não há rede/banco dentro do motor.
- `_rank_candidates` recebe os critérios e entrega o score ao cálculo coletivo. “Democrático” e
  “Festa Segura” reservam 15% ao contexto, mantendo 85% para afinidade, consenso e cobertura.
- A migração `0012_pb17_context_rank` adiciona `selection_rank` às faixas da execução. Isso preserva
  a ordem contextual ao reler as correspondências no PostgreSQL, onde `created_at` empata para
  inserções feitas na mesma transação.
- `backend/tests/test_pb17_context_scoring.py` cobre score, `avoid`, enriquecimento sem mutação e
  mudança material das 30 primeiras faixas entre “festa” e “estudo” nos dois modos.
- Evidências do Dev: 30 testes focados passaram; suíte backend completa com `APP_ENV=test` passou
  com 193 testes e 6 skips; build Vite passou; `git diff --check` passou. O backend em execução
  recarregou os módulos e permaneceu saudável.
- **Portão atual:** `AGUARDANDO-QA`. O QA deve reexecutar `CT-PB17-05`, `CT-S3-INT-02` e a regressão,
  emitindo o novo `VALIDADO` ou `REPROVADO`; o Dev não encerra a Sprint antecipadamente.

> Assinatura histórica da rodada 2, preservada para rastreabilidade:
> `PB-17 VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM`.

### Testes integrados da Sprint 3

Ver `PLANO_TESTES.md` → "Testes integrados da Sprint 3". Cobrem, no mínimo:

- Fluxo e2e: login → sala → contexto/modo → snapshot → motor → **playlist real** → resultado explicável.
- Contexto: "festa alegre" vs "estudo relaxante" muda tags/candidatas; LLM inválido → fallback sem quebrar.
- Vibe Check: pular → geração segue; responder → influencia o ranking.
- Regressão das Sprints 1 e 2: auth/salas/motor/execução continuam funcionando.
- Segurança/privacidade: token do host nunca no frontend; explicações sem dados sensíveis de terceiros.
- Falha de serviço externo: Search não acha/indisponível → descarta com motivo, sem crashar.

### Critérios de encerramento da Sprint 3

- [x] PB-07, PB-14, PB-15, PB-16, PB-17 concluídos e critérios validados;
- [x] testes individuais de cada PB passando;
- [x] testes integrados da Sprint 3 passando (parte automatizável — Spotify mockado);
- [x] regressão das Sprints 1 e 2 passando (217 passed / 6 skipped / 0 failed);
- [ ] **playlist real demonstrável de ponta a ponta — VALIDAÇÃO PENDENTE, será feita futuramente
  devido a limitações de API** (`CT-S3-INT-01`, requer conta Spotify Premium / Development Mode);
- [x] bloqueios documentados; plano atualizado.

### Evidências da Sprint 3

- Comandos/testes: `APP_ENV=test .venv/bin/pytest tests/test_s3_integration_qa.py` → **4 passed /
  1 failed** (CT-S3-INT-03 falha); regressão `--ignore=tests/test_s3_integration_qa.py` → **201
  passed / 6 skipped / 0 failed** (CT-S3-INT-04).
- Casos integrados: CT-S3-INT-01 (parcial ✔), CT-S3-INT-02 ✔, CT-S3-INT-03 ✖ (`DEF-S3-INT-03-01`),
  CT-S3-INT-04 ✔, CT-S3-INT-05 ✔.
- Revalidação QA (rodada 2, após correção `088597b`): reprodutor QA intocado
  `tests/test_s3_integration_qa.py` → **5 passed** (CT-S3-INT-03 agora verde); sondagem adversarial
  nova `tests/test_s3_vibe_scoring_qa.py` → **6 passed**; suíte completa → **217 passed / 6 skipped /
  0 failed**.
- Playlist criada no Spotify (id/URL): — pendente (demonstração e2e real; Spotify mockado nos testes).
- Data da validação: 2026-07-18 (rodadas 1 e 2).

### Status da Sprint 3

**Ciclo integrado Aprovado na parte automatizável (QA rodada 2, 2026-07-18); falta a demo e2e real.**
A rodada 1 reprovou por `DEF-S3-INT-03-01` (Alta) — Vibe Check persistido mas não consumido pelo
motor. O Dev corrigiu no commit `088597b`: `execute_generation` agora lê `vibe_check_answers`, agrega
as respostas (quem pula conta como neutro) e o motor puro `engine/vibe_scoring.py` aplica um
`vibe_score` (energia, tolerância a melancolia via `valence`, popularidade) misturado ao `group_score`
com influência limitada a 20%. Revalidação independente do QA: o reprodutor antes vermelho passa e a
sondagem adversarial confirma que o sinal **não inverte consenso forte**, preserva o "pular" e é
monotônico em `valence`. **`DEF-S3-INT-03-01` fechado; nenhum defeito Alta/bloqueante aberto.**
CT-S3-INT-01 (parcial), INT-02, INT-03, INT-04 (regressão 217 passed) e INT-05 aprovados.

**Encerramento (QA 2026-07-18):** todos os PBs e a parte automatizável do ciclo integrado estão
`VALIDADO`, sem defeito Alta/bloqueante aberto. **A demonstração e2e real da playlist (`CT-S3-INT-01`)
fica com VALIDAÇÃO PENDENTE — será feita futuramente devido a limitações de API** (conta Spotify
Premium / Development Mode). Por isso a assinatura oficial da Sprint **não** é `SPRINT 3 CONCLUÍDA`;
permanece:

> `SPRINT 3 EM VALIDAÇÃO — EVIDÊNCIA E2E REAL PENDENTE (DIFERIDA POR LIMITAÇÃO DE API)`

Ao retomar, executar `CT-S3-INT-01` real e só então emitir `SPRINT 3 CONCLUÍDA — INCREMENTO VALIDADO`.
Nenhum trabalho de código está pendente; a pendência é puramente de evidência/ambiente.

**Exceção de avanço (usuário, 2026-07-18):** o usuário autorizou explicitamente passar por cima do
portão de validação e iniciar a Sprint 4. A Sprint 3 fica encerrada apenas para fins operacionais, com
`CT-S3-INT-01` real ainda pendente e sem assinatura de conclusão do QA.

---

## Sprint 4 — Complementos da experiência

### Objetivo da Sprint

Ao final da Sprint 4, a experiência está complementada: logout/remoção de dados, enriquecimento de
contexto por Last.fm, sequenciamento da playlist e coleta de feedback. A consolidação de qualidade
(testes, fallbacks, proteção de dados, documentação, roteiro de demonstração) é a **Definition of
Done** aplicada a todos os PBs desde a Sprint 1 — não é mais um PB à parte.

### PBs incluídos

- PB-03 — Logout e remoção de dados
- PB-18 — Enriquecimento de contexto com Last.fm
- PB-19 — Sequenciamento da experiência musical
- PB-20 — Feedback pós-playlist

### Dependências da Sprint

- **De Sprints anteriores:** PB-02 (PB-03); PB-10 e PB-17 (PB-18); PB-12, PB-14 e PB-15 (PB-19); PB-16 (PB-20).
- **Externas:** `LASTFM_API_KEY` (PB-18) — com cascata de fallback obrigatória.

### Ordem de implementação

1. PB-03
2. PB-18
3. PB-19
4. PB-20

### Execução dos PBs

#### PB-03 — Logout e remoção de dados

- **Status:** VALIDADO (QA 2026-07-18) — CT-PB03-01..04 verificados independentemente. Logout
  invalida só a sessão atual (outra sessão do mesmo usuário sobrevive); `DELETE /auth/me` exige
  autenticação (401 sem sessão), apaga tokens/todas as sessões/snapshots/respostas de Vibe Check e
  anonimiza a identidade; apagar o **host** preserva a sala e os dados do convidado (sem colateral de
  `ON DELETE CASCADE`); respostas 204 sem token. Sondagem QA `backend/tests/test_pb03_privacy_qa.py`
  (6 casos) + Dev (6) verdes; suíte completa 229 passed / 6 skipped / 0 failed. Sem defeitos.
  Relatório: [`docs/relatorios-testes/PB-03.md`](../relatorios-testes/PB-03.md).
- **Objetivo:** encerrar sessão (invalidando-a no backend) e excluir/anonimizar dados pessoais sem
  expor tokens ou dados de terceiros.
- **Dependências:** PB-02.
- **Critérios de aceitação:**
  1. Logout invalida a sessão da aplicação no backend.
  2. Após logout, rotas autenticadas respondem como não autorizadas.
  3. Remoção exclui/anonimiza os dados pessoais previstos.
  4. Operação não expõe tokens nem dados de outros integrantes.
- **Plano de implementação:** `POST /auth/logout` invalida somente a sessão atual e remove o cookie;
  `DELETE /auth/me` exige autenticação, apaga tokens Spotify, todas as sessões do usuário, snapshots
  musicais e respostas do Vibe Check, e anonimiza a identidade.
- **Arquivos criados:** `backend/app/services/privacy_service.py`,
  `backend/tests/test_pb03_privacy.py`.
- **Arquivos alterados:** `backend/app/api/auth.py`, `README.md`, este plano.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-03) — sessão invalidada, 401 pós-logout,
  remoção efetiva, não exposição de terceiros.
- **Evidências necessárias:** rota autenticada retornando não autorizada após logout; dados removidos.
- **Riscos:** R-08. Excluir fisicamente `users` acionaria `ON DELETE CASCADE` nas salas hospedadas e
  apagaria artefatos de terceiros; por isso a linha é preservada como sujeito anônimo.
- **Decisões:** `spotify_id` recebe identificador aleatório irreversível, `display_name` vira
  `Usuário removido` e `image_url` é apagada. Salas, memberships e runs compartilhados permanecem
  referenciando apenas a identidade anônima; um login futuro com o mesmo Spotify cria usuário novo.
- **Migrações:** nenhuma; o modelo atual suporta a política.
- **Bloqueios:** nenhum técnico; PB-02 validado. A Sprint 4 foi aberta pela exceção processual
  autorizada pelo usuário, preservada na visão geral.
- **Resultado da implementação:** logout idempotente; sessão atual invalidada no banco; cookie
  removido; deleção autenticada e atômica dos dados pessoais; identidade anonimizada sem afetar o
  outro integrante nem apagar a sala hospedada; respostas 204 vazias não expõem tokens.
- **Resultado dos testes técnicos:** `test_pb03_privacy.py` + regressão PB-02 **21 passed / 0 failed**;
  suíte backend completa **223 passed / 6 skipped / 0 failed**; build Vite **45 módulos**;
  `compileall`, `pip check` e `git diff --check` aprovados. Migração não aplicável.
- **Próxima ação exata:** QA executa `CT-PB03-01..04`, com atenção à preservação de salas/dados de
  terceiros e à remoção de todas as sessões, tokens, snapshots e respostas pessoais.

#### PB-18 — Enriquecimento de contexto com Last.fm

- **Status:** VALIDADO (QA 2026-07-18) — CT-PB18-01..05 verificados independentemente. Ordem real da
  cascata confirmada por espião (faixa antes de artista; artista só sem tags de faixa); cache válido
  **não** chama a rede (stub que lança se invocado) e cache expirado re-consulta; confiança exata por
  fonte (0.95/0.75/0.50/0.20); exceção inesperada do cliente não propaga; a `LASTFM_API_KEY` não vaza
  no cache nem na candidata. Sondagem QA `backend/tests/test_pb18_lastfm_context_qa.py` (8 casos) +
  Dev (9) verdes; suíte completa 246 passed / 6 skipped / 0 failed. Migração `0013` reversível
  (estrutura verificada). Sem defeitos. Relatório:
  [`docs/relatorios-testes/PB-18.md`](../relatorios-testes/PB-18.md).
- **Objetivo:** tags do Last.fm (faixa → artista) combinadas com gêneros Spotify, em cache com
  confiança, sem interromper a geração em erro/ausência.
- **Dependências:** PB-10 e PB-17.
- **Critérios de aceitação:**
  1. Tenta tags da faixa antes das do artista.
  2. Sem Last.fm, usa gêneros Spotify e demais sinais.
  3. Cada resultado registra fonte e confiança.
  4. Consultas repetidas reutilizam cache válido.
  5. Resposta vazia/erro não interrompe a geração.
- **Plano de implementação:** `LastFmClient` + serviço de cascata; cache em `track_context_cache` com
  `confidence`/`source`; tags selecionadas anexadas à candidata antes do ranking contextual.
- **Arquivos criados:** `backend/app/clients/lastfm_client.py`,
  `backend/app/services/context_enrichment_service.py`,
  `backend/alembic/versions/0013_pb18_track_context_cache.py`,
  `backend/tests/test_pb18_lastfm_context.py`.
- **Arquivos alterados:** `backend/app/config.py`, `backend/app/db/models.py`,
  `backend/app/engine/context_scoring.py`, `backend/app/services/generation_service.py`,
  `.env.example`, `README.md`, este plano.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-18) — cascata, cache válido reutilizado,
  erro/vazio não quebra, confiança por fonte.
- **Evidências necessárias:** `track_context_cache` com fonte/confiança; cascata exercida.
- **Riscos:** R-07 (sem tags).
- **Migração:** `0013_pb18_context_cache`, reversível; cria cache único por `spotify_track_id` com
  tags da faixa/artista, gêneros Spotify, `context_scores_json`, `source`, `confidence` e
  `fetched_at`. Ciclo `upgrade → downgrade 0012 → upgrade` aprovado em PostgreSQL real; banco deixado
  em `0013_pb18_context_cache (head)`; `alembic check` sem drift.
- **Decisões:** confiança por fonte: faixa 0,95; artista 0,75; gêneros Spotify 0,50; consenso 0,20.
  Cache válido por 30 dias (configurável); timeout padrão de 5s. Sem chave, nome/artista, tags ou em
  qualquer falha externa, a cascata continua sem lançar erro. O cliente não inclui chave em mensagens
  de erro. Tags Last.fm entram como sinal do score contextual, sem decidir diretamente a playlist.
- **Bloqueios:** nenhum técnico. `LASTFM_API_KEY` real não estava disponível; o caminho externo foi
  validado com cliente mockado e parser do envelope oficial, e a ausência da chave/fallback foi
  exercitada sem rede.
- **Resultado da implementação:** `track.getTopTags` é tentado primeiro; somente quando vazio/erro o
  cliente tenta `artist.getTopTags`; depois usa gêneros Spotify ou consenso. Cada candidata recebe
  `context_source`, `context_confidence` e `context_tags`; o cache válido evita nova chamada externa.
- **Resultado dos testes técnicos:** `test_pb18_lastfm_context.py` **9 passed / 0 failed** cobrindo
  `CT-PB18-01..05`; regressão direta PB-17/PB-18 **15 passed**; suíte backend completa
  **238 passed / 6 skipped / 0 failed**. `compileall`, `pip check`, build Vite (**45 módulos**),
  `git diff --check`, migração reversível e `alembic check` aprovados.
- **Riscos/limitações:** integração real com Last.fm não exercitada por ausência de chave; timeout,
  HTTP/payload inválido, resposta vazia e erro inesperado estão cobertos por fallback/mocks. O cache
  de fallback expira normalmente para permitir nova tentativa futura.
- **Próxima ação exata:** QA executa `CT-PB18-01..05`, com atenção à ordem real das chamadas, ao reuso
  do cache sem rede e à continuidade do pipeline diante de falhas inesperadas do cliente.

#### PB-19 — Sequenciamento da experiência musical

- **Status:** VALIDADO (QA 2026-07-18) — CT-PB19-01..05 verificados independentemente, com
  **propriedade exaustiva**: para toda combinação de artistas de tamanho 2–6, quando existe arranjo
  sem adjacência (oráculo de permutações), o sequenciador produz um; o cap de 2/artista nunca é
  violado; abertura de alta aceitação (cede se forçaria adjacência); risco no meio; determinismo
  estável mesmo permutando a entrada. Integração verificada: a ordem persistida em `selection_rank`
  coincide com as URIs enviadas ao Spotify. Sondagem QA `backend/tests/test_pb19_sequencer_qa.py`
  (7 casos) + Dev (10) verdes; suíte completa 263 passed / 6 skipped / 0 failed. Sem defeitos.
  Relatório: [`docs/relatorios-testes/PB-19.md`](../relatorios-testes/PB-19.md).
- **Objetivo:** ordenar a seleção final com abertura de alta aceitação, faixas arriscadas no meio,
  sem 2 do mesmo artista consecutivas e respeitando o cap de 2/artista.
- **Dependências:** PB-12, PB-14 e PB-15.
- **Critérios de aceitação:**
  1. Sem duas do mesmo artista consecutivas.
  2. Começar por música de alta aceitação.
  3. Faixas de maior risco preferencialmente no meio.
  4. Respeitar o cap de 2 músicas por artista.
- **Plano de implementação:** `engine/sequencer.py` puro sobre a seleção final; posição do ranking
  como aceitação e seu inverso como risco; ordem final persistida em `selection_rank`.
- **Arquivos criados:** `backend/app/engine/sequencer.py`,
  `backend/tests/test_pb19_sequencer.py`.
- **Arquivos alterados:** `backend/app/services/generation_service.py`,
  `backend/app/services/result_service.py`, `backend/app/db/models.py`,
  `backend/tests/test_pb17_generation_integration.py`, `README.md`, este plano.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-19) — sem repetição consecutiva,
  abertura forte, risco no meio, cap respeitado.
- **Evidências necessárias:** ordem final validada por testes.
- **Riscos:** conflito entre abertura, adjacência e risco; empates; entrada dominada por um artista.
- **Decisões:** não adjacência tem prioridade; a abertura usa a maior aceitação entre as escolhas que
  ainda permitem terminar sem repetição. Risco é aproximado da centralidade da playlist; faixas do
  mesmo artista usam antecipação para não empurrar o maior risco à borda. Cap escolhe as duas faixas
  de maior aceitação por artista. Todos os empates usam posição original/id, sem aleatoriedade.
- **Migrações:** nenhuma; `selection_rank` já suporta a posição final. Para faixas selecionadas, o
  valor deixa de ser apenas ranking e passa a ser a ordem efetivamente enviada ao Spotify.
- **Bloqueios:** nenhum; PB-12, PB-14 e PB-15 validados.
- **Resultado da implementação:** `sequence_tracks` seleciona/capa/ordena sem I/O; a criação da
  playlist converte ranking em aceitação/risco, marca descartes `artist_cap`/`playlist_limit`, envia
  as URIs sequenciadas, persiste a posição final e o endpoint de resultado lê a mesma ordem. Entrada
  vazia, pequena ou impossível degrada por melhor esforço sem erro.
- **Resultado dos testes técnicos:** `test_pb19_sequencer.py` **10 passed / 0 failed** cobrindo
  `CT-PB19-01..05` e integração Spotify/persistência; sondagem combinatória adicional percorreu
  **1.056 casos viáveis** (2–8 faixas, até 2/artista) sem adjacência indevida. Suíte backend completa
  **256 passed / 6 skipped / 0 failed**. `compileall`, `pip check`, build Vite (**45 módulos**) e
  `git diff --check` aprovados.
- **Riscos/limitações:** risco usa o inverso da posição de ranking por não haver audio features nem
  score de risco persistido no MVP. Quando não existe solução sem adjacência, o resultado mantém cap
  e tamanho por melhor esforço.
- **Próxima ação exata:** QA executa `CT-PB19-01..05`, incluindo contraexemplos de abertura
  (`A,A,B`), empates, lista de artista único e confirmação de que a ordem persistida coincide com as
  URIs enviadas ao Spotify.

#### PB-20 — Feedback pós-playlist

- **Status:** VALIDADO (QA 2026-07-18) — CT-PB20-01..05 verificados independentemente. Feedback por
  faixa e geral persistidos; **isolamento de execução** confirmado (faixa de outro run → 404; membro
  de outra sala → 403; não autenticado → 401, nada persiste); limites 0–5 e comentário validados
  (422); upsert idempotente sem duplicar; `future_use_notice` na API. Interação com PB-03 verificada:
  a remoção de conta também apaga os feedbacks pessoais sem afetar terceiros. Sondagem QA
  `backend/tests/test_pb20_feedback_qa.py` (10 casos) + Dev (9) verdes; suíte completa 282 passed /
  6 skipped / 0 failed. Migração `0014` reversível. Sem defeitos. Relatório:
  [`docs/relatorios-testes/PB-20.md`](../relatorios-testes/PB-20.md).
- **Objetivo:** coletar feedback por faixa (like/dislike/more_like_this/never_again) e geral
  (representação/satisfação), associado à execução correta, sem uso no ranking do MVP.
- **Dependências:** PB-16.
- **Critérios de aceitação:**
  1. Marcar like/dislike/more_like_this/never_again por faixa.
  2. Informar satisfação e representação da playlist.
  3. Feedback associado ao usuário e à execução correta.
  4. Usuário não registra feedback em sala da qual não participa.
  5. Deixar explícito que o feedback é para evoluções futuras.
- **Plano de implementação:** `POST /playlist-runs/{id}/tracks/{track_id}/feedback` e
  `POST /playlist-runs/{id}/feedback`; persistir `member_track_feedback` e `playlist_feedback`.
- **Arquivos ou módulos previstos:** `backend/app/api/feedback.py`, `backend/app/db/models.py`, migração, `frontend/`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-20) — associação correta, bloqueio de
  não-membro, aviso de uso futuro, persistência.
- **Evidências necessárias:** feedback persistido e vinculado; não-membro bloqueado.
- **Riscos:** vinculação incorreta de execução.
- **Bloqueios:** nenhum técnico; PB-16 validado.
- **Resultado da implementação:** criadas as duas rotas autenticadas com autorização por membership
  e exigência de run concluído. Os registros usam upsert único por usuário/run/faixa e por
  usuário/run; faixa descartada ou pertencente a outra execução não é aceita. O resultado expõe
  `run_id`/`track_id`; a ação da tela de resultado abre o novo formulário responsivo, com os quatro
  sinais por faixa, duas escalas 0–5, comentário opcional e estado de confirmação. A interface e as
  respostas da API deixam explícito que o uso será futuro e não afeta o ranking do MVP. A remoção de
  conta também exclui os novos feedbacks pessoais sem afetar os de terceiros.
- **Arquivos criados:** `backend/app/api/feedback.py`, `backend/app/schemas/feedback.py`,
  `backend/app/services/feedback_service.py`, `backend/alembic/versions/0014_pb20_feedback.py`,
  `backend/tests/test_pb20_feedback.py`, `frontend/src/Feedback.jsx`.
- **Arquivos alterados:** modelos/registro da API, schemas e serviço do resultado, serviço de
  privacidade, rota/app/cliente/CSS do frontend, README e este plano.
- **Migração:** `0014_pb20_feedback`, validada em PostgreSQL isolado com cadeia completa
  `upgrade head`, `downgrade 0013_pb18_context_cache` e novo `upgrade head`; banco temporário removido.
  Aplicada também ao banco local da aplicação, que permaneceu saudável; as duas rotas constam no OpenAPI.
- **Resultado dos testes técnicos:** `test_pb20_feedback.py` cobre `CT-PB20-01..05`, atualização
  idempotente, autenticação, limites 0–5, run incompleto, faixa descartada, integração do payload de
  resultado e privacidade: **9 passed / 0 failed**. Suíte backend completa **272 passed / 6 skipped /
  0 failed**; `compileall`, `pip check`, build Vite (**46 módulos**) e `git diff --check` aprovados.
- **Riscos/limitações:** os dois endpoints são independentes; em falha de rede durante o envio da
  tela, uma parte pode chegar antes da outra, mas o reenvio é seguro por upsert. Feedback continua
  deliberadamente fora do motor/ranking do MVP.
- **Próxima ação exata:** PB validado individualmente; preservar como pendência separada apenas a
  inspeção visual e `CT-S4-INT-*`, sem reabrir PB-20.

> **Nota — Qualidade/robustez/documentação (antigo PB-20):** deixou de ser um PB e virou a
> **Definition of Done**, aplicada a **todos** os PBs desde a Sprint 1 (ver `../produto/BACKLOG_PRODUTO.md`
> §15): testes de motor/API, clientes externos mockados (token expirado, 429, JSON inválido, busca vazia),
> nenhum segredo em logs/testes, README atualizado e roteiro de demonstração. Verificada a cada entrega.

### Testes integrados da Sprint 4

Ver `PLANO_TESTES.md` → "Testes integrados da Sprint 4". Cobrem, no mínimo:

- Logout/remoção: sessão invalidada e dados removidos sem afetar terceiros.
- Last.fm: cascata e cache exercidos; erro externo não quebra a geração.
- Sequenciamento: ordem final coerente sobre a playlist real.
- Feedback: coleta associada corretamente à execução; não-membro bloqueado.
- Regressão completa das Sprints 1–3.
- Qualidade: suíte completa verde; nenhum segredo exposto; documentação atualizada.

### Critérios de encerramento da Sprint 4

- [ ] PB-03, PB-18, PB-19, PB-20 concluídos e critérios validados;
- [ ] testes individuais de cada PB passando;
- [ ] testes integrados da Sprint 4 passando;
- [ ] regressão das Sprints 1–3 passando;
- [ ] documentação e roteiro de demo prontos;
- [ ] bloqueios documentados; plano atualizado.

### Evidências da Sprint 4

- Comandos/telas/integrações: — (a preencher)
- Data da validação: — (a preencher)

### Status da Sprint 4

**PBs individuais validados; validação integrada pendente.** A Sprint 5 foi aberta operacionalmente
por decisão explícita do usuário, sem emitir `SPRINT 4 CONCLUÍDA`.

---

## Sprint 5 — Expansão pós-MVP (fora do MVP)

Aberta por decisão explícita do usuário em 2026-07-18. A exceção preserva, sem promover a aprovação,
as validações integradas pendentes das Sprints 1–4.

### Ordem de implementação

1. PB-21
2. PB-22
3. PB-23
4. PB-24

### Execução dos PBs

#### PB-21 — Modo Descoberta

- **Status:** VALIDADO (QA 2026-07-18) — CT-PB21-01..06 verificados independentemente. Portão da flag
  é **server-side** (flag off → 422 e `room.mode` intacto; on → persiste; não-host → 403); novidade
  0.30 > 0.05 e diversidade 0.15 fazem a candidata nova/diversa pontuar mais e subir no ranking; veto
  forte ainda derruba a 25% (penalidade 0.75); **mutação confirma** que a diversidade sempre calculada
  não altera os modos do MVP (peso 0.0); explicação só no modo Descoberta. Sondagem QA
  `backend/tests/test_pb21_discovery_mode_qa.py` (10 casos) + Dev (6) verdes; suíte completa 302 passed
  / 6 skipped / 0 failed. Sem defeitos. Relatório:
  [`docs/relatorios-testes/PB-21.md`](../relatorios-testes/PB-21.md).
- **Objetivo:** oferecer, por feature flag, um perfil de pesos que favoreça novidade/diversidade sem
  abandonar consenso, rejeição e representação mínima.
- **Dependências:** PB-11, PB-12 e PB-16 — todas `VALIDADO`.
- **Critérios de aceitação:**
  1. Modo selecionável somente quando habilitado na configuração.
  2. Peso de novidade superior ao modo Democrático.
  3. Rejeições fortes e representação mínima continuam consideradas.
  4. Resultado explica que o modo favoreceu descoberta musical.
- **Plano de implementação:** feature flag `DISCOVERY_MODE_ENABLED`; lista de modos disponível vinda
  da API; perfil `discovery` no motor; mapeamento explícito no pipeline e explicação persistida.
- **Testes obrigatórios:** `CT-PB21-01..06` no `PLANO_TESTES.md`.
- **Bloqueios:** nenhum.
- **Resultado da implementação:** `DISCOVERY_MODE_ENABLED` é `false` por padrão. O endpoint autenticado
  `GET /rooms/consensus-modes` anuncia apenas os modos habilitados; a tentativa direta de selecionar
  “Descoberta” com a flag desligada recebe 422 sem alterar a sala. Com a flag ligada, o host pode
  selecionar e persistir o modo. O frontend consome essa lista, sem alterar o payload histórico do
  lobby. O perfil `discovery` aumenta novidade para 0,30 e diversidade para 0,15; diversidade é um
  sinal puro calculado contra artistas/gêneros conhecidos. Veto de 0,75 e elevação do integrante
  menos representado continuam no mesmo pipeline. A explicação do modo é persistida no run e exibida
  no resultado.
- **Arquivos criados:** `backend/tests/test_pb21_discovery_mode.py`.
- **Arquivos alterados:** configuração/env/Compose; schemas/API/serviço de salas; scoring, pesos,
  geração e resultado; seletor/cliente frontend; README; planos de execução e testes.
- **Migração:** não aplicável; `music_sessions.mode` já é texto e suporta o novo valor.
- **Resultado dos testes técnicos:** `test_pb21_discovery_mode.py` **6 passed / 0 failed** cobrindo
  `CT-PB21-01..06`. Suíte backend completa **288 passed / 6 skipped / 0 failed**; `compileall`,
  `pip check`, build Vite (**46 módulos**), `docker compose config` e `git diff --check` aprovados.
- **Riscos/limitações:** o sinal de novidade preserva a heurística existente do PB-11 (datas iniciadas
  em `202` são novas); não estima idade relativa em anos. Diversidade sem gêneros usa o artista como
  fallback. O recurso permanece opt-in para permitir calibração antes de habilitação geral.
- **Próxima ação exata:** encerrado pelo QA; o portão para PB-22 foi liberado.

#### PB-22 — Agrupamento de perfis musicais

- **Status:** VALIDADO (QA 2026-07-18) — CT-PB22-01..06 verificados independentemente. Motor puro
  consome só sinais autorizados e não replica dados brutos (privacidade); `insufficient_evidence` em
  <3 perfis/perfil esparso/sem par acima do limiar; **determinismo confirmado nas 24 permutações**;
  homogêneo → `single_group`; candidatas recebem os cluster IDs dos membros e **mutação confirma que
  os clusters não alteram o ranking** (critério 4); limiar fora de [0,1] e user_id duplicado →
  ValueError. Sondagem QA `backend/tests/test_pb22_taste_clustering_qa.py` (13 casos) + Dev (10)
  verdes; suíte completa 325 passed / 6 skipped / 0 failed. Sem defeitos. Relatório:
  [`docs/relatorios-testes/PB-22.md`](../relatorios-testes/PB-22.md).
- **Objetivo:** identificar subgrupos de afinidade a partir de dados autorizados, deterministicamente.
- **Dependências:** PB-09 `VALIDADO`; portão anterior PB-21 `VALIDADO` pelo relatório de QA.
- **Critérios de aceitação:**
  1. O agrupamento consome somente `tracks`, `artists` e `genres` de `UserTasteProfile`, derivados dos
     snapshots temporários já autorizados; o resultado não replica dados musicais brutos.
  2. Menos de três perfis, perfil com menos de dois sinais ou nenhum par acima do limiar produz
     `insufficient_evidence`; grupo homogêneo produz `single_group` sem divisão artificial.
  3. Perfis são ordenados por `user_id`, pares e componentes têm ordem estável e os IDs
     `cluster-XX` são reproduzíveis para a mesma coleção de entrada.
  4. O resultado completo entra em `_rank_candidates` e cada candidata recebe os IDs transitórios
     dos clusters de seus membros de origem, disponíveis ao motor sem mudar o score no PB-22.
- **Plano implementado:** reutilizar a compatibilidade ponderada do PB-09; formar componentes conexos
  com limiar 0,35; modelar resultados imutáveis com status/reason; integrar após a criação dos perfis
  e antes do ranqueamento; não persistir clusters nem antecipar faixas-ponte.
- **Arquivos criados:** `backend/app/engine/clustering.py` e
  `backend/tests/test_pb22_taste_clustering.py`.
- **Arquivos alterados:** `backend/app/engine/candidates.py`,
  `backend/app/services/generation_service.py`, `README.md`, `PLANO_TESTES.md` e este plano.
- **Migração/configuração:** não aplicável; resultado existe somente em memória durante a geração.
- **Testes obrigatórios detalhados:** `CT-PB22-01..06` no `PLANO_TESTES.md`, deixados como
  `Não executado` até a validação independente.
- **Resultado dos testes técnicos:** foco PB-22 **10 passed / 0 failed**; regressão relacionada
  PB-09/PB-10/PB-11/PB-12/PB-21/PB-22 **52 passed / 0 failed**; suíte backend completa
  **312 passed / 6 skipped / 0 failed**; `compileall`, `pip check`, build Vite (**46 módulos**) e
  `git diff --check` aprovados. `ruff` está configurado, mas o executável não está instalado no
  ambiente virtual, portanto essa checagem não foi executada.
- **Riscos/limitações:** o limiar 0,35 é uma heurística inicial; componentes conexos podem conter um
  integrante isolado quando outro subgrupo válido existe. Clusters não alteram ranking, não são
  persistidos e não são expostos ao frontend; marcação de faixas-ponte pertence exclusivamente ao
  PB-23.
- **Bloqueios:** nenhum técnico.
- **Próxima ação exata:** encerrado pelo QA; o portão para PB-23 foi liberado.

#### PB-23 — Identificação de músicas-ponte

- **Status:** VALIDADO (QA 2026-07-18) — CT-PB23-01..06 verificados independentemente. Ponte exige
  ≥2 clusters com aceitação ≥0,25 (afinidade do PB-11, popularidade/novidade zeradas — confirmado que
  candidata só popular/nova não vira ponte); `bridge_score` = 2º maior score de cluster; **mutação
  confirma que a marcação não reordena o ranking em nenhum dos 3 modos** (critério 3, não promove) e
  que a flag off não marca nada; None/single/insufficient → sem ponte; limiar fora de [0,1] →
  ValueError; determinismo nas 24 permutações; resultado expõe só booleano + explicação agregada.
  Sondagem QA `backend/tests/test_pb23_bridge_tracks_qa.py` (15 casos) + Dev (11) verdes; suíte
  completa 351 passed / 6 skipped / 0 failed. Migração `0015` reversível. Sem defeitos. Relatório:
  [`docs/relatorios-testes/PB-23.md`](../relatorios-testes/PB-23.md).
- **Objetivo:** marcar faixas com boa aceitação entre subgrupos durante o ranqueamento.
- **Dependências:** PB-11 e PB-22 `VALIDADO`; relatório PB-22 sem defeitos abertos.
- **Critérios de aceitação:**
  1. O motor calcula os componentes de afinidade do score individual do PB-11 por membro e usa a
     média por cluster; popularidade/novidade são zeradas por não diferenciarem subgrupos, e a
     candidata é ponte quando pelo menos dois clusters atingem aceitação 0,25.
  2. Durante `_rank_candidates`, candidatas recebem `is_bridge`, `bridge_score` conservador (segundo
     maior score de cluster) e os IDs dos clusters aceitos.
  3. `BRIDGE_TRACKS_ENABLED=false` por padrão impede a avaliação e limpa marcações; Democrático,
     Festa Segura e Descoberta preservam ordem e scores. Mesmo ligada, a identificação não promove
     candidatas — balanceamento é escopo do PB-24.
  4. O matching persiste `playlist_run_tracks.is_bridge`; a API retorna o booleano e justificativa
     agregada, e a tela de resultado apresenta o selo `FAIXA-PONTE` sem expor afinidades individuais.
- **Plano implementado:** módulo puro `bridge.py`; aceitação média por cluster; flag server-side;
  anotação transitória durante o ranking; persistência no matching; explicação agregada e badge no
  resultado.
- **Arquivos criados:** `backend/app/engine/bridge.py`,
  `backend/tests/test_pb23_bridge_tracks.py` e
  `backend/alembic/versions/0015_pb23_bridge_tracks.py`.
- **Arquivos alterados:** configuração/env/Compose; candidata e pipeline; modelo/schema/resultado;
  tela/tokens frontend; README; planos de execução e testes.
- **Migração:** `0015_pb23_bridge_tracks` adiciona `playlist_run_tracks.is_bridge BOOLEAN NOT NULL
  DEFAULT false`; downgrade remove a coluna. Upgrade/downgrade/upgrade aprovados em schema temporário
  isolado carimbado em `0014`; SQL offline PostgreSQL também aprovado.
- **Testes obrigatórios detalhados:** `CT-PB23-01..06` no `PLANO_TESTES.md`, deixados como
  `Não executado` até a validação independente.
- **Resultado dos testes técnicos:** foco PB-23 **11 passed / 0 failed**; regressão relacionada
  PB-11/PB-12/PB-14/PB-16/PB-19/PB-21/PB-22/PB-23 **103 passed / 0 failed**; suíte backend completa
  **336 passed / 6 skipped / 0 failed**; `compileall`, `pip check`, build Vite (**46 módulos**),
  migração reversível e SQL PostgreSQL aprovados. A cadeia histórica completa não roda em SQLite por
  uma revisão antiga usar `DEFAULT now()`; a revisão do PB-23 foi validada isoladamente. `ruff`
  continua indisponível no ambiente virtual.
- **Riscos/limitações:** aceitação 0,25 é uma heurística inicial. A marcação depende de agrupamento
  `clustered`; estados insuficiente/único não produzem pontes. O resultado expõe somente o booleano e
  uma explicação agregada, sem IDs/scores dos clusters. Nenhuma candidata recebe bônus nesta história.
- **Bloqueios:** nenhum técnico.
- **Próxima ação exata:** encerrado pelo QA; o portão para PB-24 foi liberado.

#### PB-24 — Balanceamento entre subgrupos

- **Status:** VALIDADO (QA 2026-07-18) — CT-PB24-01..06 verificados independentemente. Teto por
  cluster respeitado com alternativas; **saída é permutação exata da entrada** (não perde/duplica);
  **veto fora do prefixo não é puxado para dentro** (verificação reforçada da fronteira do
  best-effort); flag off preserva a ordem nos 3 modos; None/single/insufficient → ordem preservada;
  share fora de [0,5;1] e size negativo → ValueError; determinismo. Sondagem QA
  `backend/tests/test_pb24_subgroup_balance_qa.py` (14 casos) + Dev (14) verdes; suíte completa 379
  passed / 6 skipped / 0 failed. Migração `0016` reversível. Sem defeitos; uma observação de clareza
  registrada (best-effort conta veto pré-existente como representante, sem impacto funcional).
  Relatório: [`docs/relatorios-testes/PB-24.md`](../relatorios-testes/PB-24.md).
- **Objetivo:** alternar representantes dos subgrupos preservando consenso e justiça.
- **Dependências:** PB-12, PB-16, PB-22 e PB-23 — todas `VALIDADO`.
- **Critérios de aceitação:**
  1. O prefixo final de até 30 faixas limita cada cluster a `SUBGROUP_MAX_SHARE=0.60` quando há
     alternativas seguras e intercala primeiro o cluster menos representado.
  2. A etapa roda depois da penalização de rejeição e da elevação por justiça, não recalcula scores,
     não remove candidatas do conjunto ranqueado e não promove ao prefixo faixas com score individual
     de veto (≤ 0,05).
  3. `SUBGROUP_BALANCING_ENABLED=false` por padrão preserva exatamente a ordem dos modos Democrático,
     Festa Segura e Descoberta; o teto é configurável no intervalo de 0,5 a 1.
  4. Quando a ordem realmente muda, o run persiste `subgroup_balancing_applied=true` e o resultado
     inclui uma explicação agregada, sem expor IDs ou afinidades dos clusters.
- **Plano implementado:** módulo puro `subgroup_balance.py` seleciona deterministicamente o cluster
  menos representado e mantém desempate pela ordem original. Candidatas de múltiplos clusters são
  atribuídas ao cluster menos representado; candidatas neutras não pressionam o teto. Sem opções
  suficientes, o prefixo é completado na ordem original para preservar tamanho e qualidade.
- **Arquivos criados:** `backend/app/engine/subgroup_balance.py`,
  `backend/tests/test_pb24_subgroup_balance.py` e
  `backend/alembic/versions/0016_pb24_subgroup_balance.py`.
- **Arquivos alterados:** configuração/env/Compose; candidata e pipeline de geração; modelo e serviço
  de resultado; README; planos de execução e testes. Nenhuma mudança visual foi necessária porque a
  explicação usa a lista de justificativas existente.
- **Migração:** `0016_pb24_subgroup_balance` adiciona
  `playlist_runs.subgroup_balancing_applied BOOLEAN NOT NULL DEFAULT false`; downgrade remove a
  coluna. Upgrade/downgrade/upgrade aprovados em schema temporário isolado carimbado em `0015`; SQL
  offline PostgreSQL também aprovado.
- **Testes obrigatórios detalhados:** `CT-PB24-01..06` no `PLANO_TESTES.md`, deixados como
  `Não executado` até a validação independente.
- **Resultado dos testes técnicos:** foco PB-24 **14 passed / 0 failed**; regressão relacionada
  PB-12/PB-16/PB-19/PB-22/PB-23/PB-24 **103 passed / 0 failed**; suíte backend completa
  **365 passed / 6 skipped / 0 failed**; `compileall`, `pip check`, build Vite (**46 módulos**),
  migração reversível, SQL PostgreSQL e `git diff --check` aprovados. A cadeia histórica completa não
  roda em SQLite por uma revisão antiga usar `DEFAULT now()`; a revisão do PB-24 foi validada
  isoladamente. `ruff` continua indisponível no ambiente virtual.
- **Riscos/limitações:** o teto é aplicado por melhor esforço: pode ser excedido se faltarem
  candidatas seguras de outros clusters. O limiar de veto 0,05 e o teto 0,60 são heurísticas iniciais.
  O balanceador não busca músicas externas nem persiste composição/IDs de clusters.
- **Bloqueios:** nenhum técnico.
- **Próxima ação exata:** QA executa `CT-PB24-01..06`, com atenção à escassez de alternativas, à não
  promoção de vetos, à preservação dos três modos com flag desligada, à migração reversível e à
  explicação condicional. Não encerrar a Sprint 5 antes do veredito `VALIDADO` e da validação integrada.

Detalhes e critérios de aceitação em `../produto/BACKLOG_PRODUTO.md` (§10, PB-21 a PB-24).

---

## Sprint 6 — Estabilização e evolução contextual

### Estado e fonte detalhada

A Sprint 6 foi implementada em sequência por exceção explícita do usuário. O handoff, as decisões,
os commits, as correções e as evidências técnicas estão em
[`SPRINT_06_IMPLEMENTACAO.md`](SPRINT_06_IMPLEMENTACAO.md). A exceção retirou o portão entre PBs
durante a implementação, mas não substituiu o QA: os cinco PBs permanecem `AGUARDANDO-QA`.

### Ordem de validação

1. PB-25
2. PB-26
3. PB-27
4. PB-28
5. PB-29
6. Testes integrados da Sprint 6 e regressão completa

#### PB-25 — Resiliência e eficiência da integração Spotify

- **Status:** AGUARDANDO-QA — `DEF-PB25-01` corrigido no commit `bb1337f`; URI nativa agora só usa o
  fast path quando for exatamente `spotify:track:{id}`.
- **Objetivo:** reutilizar ID/URI de candidatas nativas e interromper o matching no primeiro rate limit.
- **Dependências:** PB-13, PB-14 e PB-15 (`VALIDADO`).
- **Critérios e evidências:** 22 testes relacionados passaram, inclusive o teste adversarial que
  reproduzia o defeito; regressão completa: 407 passaram, 6 pulados e 1 falha histórica fora do
  PB-25 (`test_qa_mode_enum_is_closed[Descoberta]`). Ver `../relatorios-testes/PB-25.md`.
- **Próxima ação:** QA revalida `DEF-PB25-01` e decide o PB-25. PB-26 permanece bloqueado até o
  veredito independente; a Sprint 7 segue pela exceção do Product Owner.

#### PB-26 — Pool contextual híbrido

- **Status:** AGUARDANDO-QA — implementado e corrigido nos commits `53c59f3`, `cfcec7f` e `1af62fe`;
  sem relatório independente das correções de aderência específica.
- **Objetivo:** combinar Tops com descoberta Last.fm por tag/similaridade, preservando proveniência,
  fallback, veto, justiça e uma parcela de âncoras pessoais.
- **Dependências:** PB-17, PB-18, PB-21 e PB-25.
- **Critérios e evidências:** ver `SPRINT_06_IMPLEMENTACAO.md` §6 e §§12–14 e `PLANO_TESTES.md` PB-26.
- **Próxima ação:** após PB-25 validado, QA repete os casos contextuais e a regressão.

#### PB-27 — Acompanhamento compartilhado da geração

- **Status:** AGUARDANDO-QA — implementado no commit `5504680`; sem relatório independente.
- **Objetivo:** compartilhar progresso, conclusão e erro por polling, preservando ações host-only.
- **Dependências:** PB-13 e PB-16 (`VALIDADO`).
- **Migração:** `0017_pb27_generation_progress`.
- **Próxima ação:** após PB-26 validado, QA executa `CT-PB27-01..05`.

#### PB-28 — Conformidade visual do Login/Landing

- **Status:** AGUARDANDO-QA — implementado no commit `c57179c`; build comprovado, inspeção visual
  independente pendente.
- **Objetivo:** alinhar a entrada ao design oficial sem quebrar OAuth, acessibilidade ou responsividade.
- **Dependências:** PB-02 (`VALIDADO`).
- **Próxima ação:** após PB-27 validado, QA executa `CT-PB28-01..04` em navegador real.

#### PB-29 — Estado compartilhado e privado do Vibe Check

- **Status:** AGUARDANDO-QA — implementado no commit `46df4a9`; sem relatório independente.
- **Objetivo:** expor somente `pending`/`answered`/`skipped` e totais, mantendo respostas privadas.
- **Dependências:** PB-07 e PB-27.
- **Migração:** `0018_pb29_vibe_status`.
- **Próxima ação:** após PB-28 validado, QA executa `CT-PB29-01..05`; depois valida a Sprint 6.

### Critérios de encerramento da Sprint 6

- [ ] PB-25..29 `VALIDADO` pelo QA;
- [ ] correções contextuais e de resultado revalidadas;
- [ ] migrações `0017`/`0018` reversíveis;
- [ ] fluxo compartilhado demonstrado sem exposição de dados privados;
- [ ] regressão completa e build frontend aprovados;
- [ ] dívidas e2e reais anteriores permanecem explicitamente rastreadas.

---

## Sprint 7 — Biblioteca musical ampliada e eficiente

> **Estado:** em andamento desde 2026-07-31 por decisão explícita do Product Owner. A validação
> pendente da Sprint 6 continua rastreada em paralelo, mas deixou de ser dependência de PB-30..34.
> Permissões reais do Spotify Development Mode e a retenção temporária continuam riscos de entrada.

### Objetivo da Sprint

Ampliar o repertório de cada integrante sem transformar o banco num espelho do Spotify: combinar
Tops e playlists elegíveis em uma biblioteca temporária, deduplicada e limitada a **500 faixas
únicas por pessoa**, sincronizada no máximo a cada sete dias e consumida pelo motor com pesos e
limites que preservam contexto e justiça.

### Contrato de produto da biblioteca

- **Limite único:** `0..500` faixas Spotify únicas por usuário, contando Tops e playlists juntas.
- **Prioridade dos Tops:** até 50 `short_term` + 50 `medium_term` + 50 `long_term`, deduplicadas;
  top artists continuam como sinal auxiliar de artistas/gêneros e não contam como faixas.
- **Preenchimento por playlists:** somente playlists próprias ou colaborativas cujo conteúdo a API
  vigente permita ler; elas preenchem as vagas restantes de modo determinístico e distribuído.
- **Sem equivalência falsa:** estar numa playlist é sinal mais fraco do que estar no Top; recorrência
  e rank podem reforçar o sinal dentro de limites configuráveis.
- **Pool ativo:** no máximo 250 candidatas por pessoa em uma geração, com alvo de até 150 Tops e 100
  faixas de playlists; capacidade ociosa pode ser preenchida sem remover a prioridade dos Tops.
- **Cache:** TTL default de sete dias, `snapshot_id` por playlist, metadados mínimos, atualização
  atômica e remoção no disconnect.
- **Compatibilidade:** sem biblioteca pronta, o pipeline continua usando o snapshot Top do PB-08.
- **Privacidade:** nenhuma playlist/faixa bruta vai ao LLM; nomes de playlists e sinais individuais
  não entram em resultado, logs ou payload coletivo.

### Dependências e riscos de entrada

- A decisão do Product Owner removeu as dependências formais da Sprint 6. O código já implementado de
  rate limit, pool contextual e observabilidade permanece como baseline, ainda sujeito ao QA próprio.
- Novo consentimento OAuth `playlist-read-private`; os três usuários da demonstração devem estar na
  allowlist. O app owner deve atender aos requisitos atuais do Development Mode.
- A API atual pode listar playlists seguidas sem permitir ler seus itens; não tentar contornar 403.
- Quotas do Spotify não são tratadas como “tokens consumíveis”: o desenho reduz chamadas, trata 429
  e mantém cache, mas não presume um limite numérico não publicado.
- Os termos do Spotify exigem necessidade, atualização e exclusão dos dados; o modelo evita payloads
  completos, retenção indefinida e uso fora da recomendação autorizada.

### Ordem de implementação

1. PB-30 — Autorização e inventário de playlists
2. PB-31 — Biblioteca musical limitada a 500 faixas
3. PB-32 — Sincronização incremental e resiliente
4. PB-33 — Perfil ponderado e seleção limitada de candidatas
5. PB-34 — Integração e observabilidade da biblioteca ampliada

### Execução dos PBs

#### PB-30 — Autorização e inventário de playlists

- **Status:** VALIDADO — todos os testes obrigatórios e adversariais passaram na revalidação de
  2026-07-31; correção no commit `be45742`.
- **Objetivo:** adicionar o menor escopo de leitura necessário, detectar reconsentimento e paginar o
  inventário de playlists elegíveis.
- **Dependências:** nenhuma.
- **Plano de implementação:** atualizar OAuth/reauth; criar cliente paginado para `/me/playlists` e
  `/playlists/{id}/items`; persistir somente ID, tipo de acesso, total, `snapshot_id` e verificação;
  filtrar itens nulos, episódios, arquivos locais e playlists sem permissão de conteúdo.
- **Arquivos previstos:** cliente Spotify, auth/scopes, serviço de biblioteca, modelos/migração e
  testes `test_pb30_playlist_inventory.py`.
- **Testes obrigatórios:** `CT-PB30-01..05` no `PLANO_TESTES.md`.
- **Migração:** inventário de playlists; revisão deve partir do head real posterior a `0018`.
- **Riscos:** consentimento antigo, paginação, payload `item`/`items`, 403 e mudanças do Dev Mode.
- **Evidências do Dev:** 9 testes focados e 72 relacionados passaram; suíte backend
  `416 passed / 6 skipped`; build Vite aprovado; `0019` upgrade/downgrade isolado e SQL PostgreSQL
  verificados; `compileall`, `pip check` e `git diff --check` aprovados.
- **Resultado do QA:** `CT-PB30-01`, `02` e `05` aprovados; `CT-PB30-03` e `04` reprovados. Suíte
  completa: `417 passed, 6 skipped, 2 failed`; build do frontend e migração `0019` aprovados.
- **Defeitos:** `DEF-PB30-01` — ausência de `playlist-read-collaborative`; `DEF-PB30-02` — inventário
  rejeita o campo vigente `items.total` e depende de `tracks.total` legado.
- **Correção do Dev:** OAuth e reauth agora exigem os dois escopos do inventário; `items.total` é o
  formato principal e `tracks.total` permanece como fallback. Testes focados: `11 passed`; regressão:
  `419 passed, 6 skipped`; build, migração, `compileall`, `pip check` e `git diff --check` aprovados.
- **Revalidação do QA:** `CT-PB30-01..05` aprovados; `DEF-PB30-01..02` revalidados; suíte focada
  `12 passed`; regressão `420 passed, 6 skipped`; migração e build aprovados.
- **Próxima ação:** PB-31 está liberado para uma nova fase de implementação.

#### PB-31 — Biblioteca musical limitada a 500 faixas

- **Status:** VALIDADO — `CT-PB31-01..06` e testes adversariais aprovados pelo QA em 2026-07-31.
- **Objetivo:** compor e persistir até 500 faixas únicas por pessoa com proveniência completa.
- **Dependências:** PB-30.
- **Plano de implementação:** tabelas normalizadas de faixa e vínculo usuário/faixa; sinais de Top
  por faixa temporal e de playlist; dedupe por Spotify ID; Tops primeiro; preenchimento round-robin
  estável entre playlists até 500; limpeza de vínculos antigos na promoção do novo snapshot.
- **Arquivos previstos:** modelos/migração, serviço de composição puro, serviço de persistência,
  privacidade e testes `test_pb31_music_library.py`.
- **Testes obrigatórios:** `CT-PB31-01..06`.
- **Migração:** reversível, com unicidade `(user_id, spotify_track_id)` e FKs em cascata apenas
  para dados pessoais da biblioteca.
- **Riscos:** cap incorreto após dedupe, uma playlist dominar o preenchimento e payload excessivo.
- **Implementação entregue:** compositor puro em `engine/music_library.py`; Tops limitados a 50 por
  faixa temporal e priorizados; playlists elegíveis preenchidas em round-robin ordenado; dedupe por
  Spotify ID preserva cada origem/rank, inclusive duplicatas encontradas depois do cap.
- **Persistência:** snapshot pessoal, faixa mínima e origem normalizada; substituição atômica do
  snapshot anterior; checks de contagem/posição e unicidade usuário/faixa. Nenhum payload bruto,
  imagem, álbum ou nome de playlist é persistido.
- **Arquivos:** `backend/app/engine/music_library.py`, `services/music_library_service.py`, modelos,
  `privacy_service.py`, migração `0020_pb31_music_library.py` e
  `tests/test_pb31_music_library.py`.
- **Evidências do Dev:** `11 passed` focados; `32 passed` relacionados; regressão completa
  `431 passed, 6 skipped`; build Vite aprovado; `compileall`, `pip check`, Alembic head, migração
  reversível isolada, SQL PostgreSQL offline e `git diff --check` aprovados.
- **Handoff do Dev:** nenhum critério técnico pendente; `CT-PB31-01..06` foram entregues ao QA com
  atenção solicitada ao cap, round-robin, atomicidade e remoção isolada.
- **Resultado do QA:** `14 passed` focados (11 Dev + 3 adversariais); regressão completa
  `434 passed, 6 skipped`; migração `0020`, rollback atômico e build Vite aprovados. Nenhum defeito
  alto, bloqueante ou regressão encontrado. Relatório: `docs/relatorios-testes/PB-31.md`.
- **Próxima ação após QA:** PB-32 liberado para uma nova fase de implementação.

#### PB-32 — Sincronização incremental e resiliente

- **Status:** VALIDADO — QA revalidou `CT-PB32-01..06` em 2026-07-31. `DEF-PB32-01` corrigido e
  revalidado com sessões independentes, locks isolados por event loop e advisory lock PostgreSQL por
  usuário. Evidência focada: `32 passed`; regressão completa Dev: `444 passed, 6 skipped`, mantendo
  somente falhas preexistentes fora da PB-32 (PB-02/PB-06). Relatório: `PB-32.md`.
- **Objetivo:** reduzir chamadas externas e preservar a última biblioteca pronta em falhas.
- **Dependências:** PB-31.
- **Plano de implementação:** TTL de sete dias; comparar `snapshot_id`; paginação de 50 itens sem
  busca individual; concorrência externa default 1; lock/upsert por usuário; staging transacional;
  distinguir rate limit transitório de `QUOTA_EXCEEDED`; nunca promover sincronização parcial.
- **Arquivos previstos:** cliente/serviço de sync, config/env de limites e testes
  `test_pb32_library_sync.py`.
- **Testes obrigatórios:** `CT-PB32-01..06`.
- **Migração:** campos de estado/tempo/erro sanitizado somente se PB-31 não os introduzir.
- **Riscos:** 429 no meio da paginação, quota compartilhada, corrida e latência de primeiro sync.

#### PB-33 — Perfil ponderado e seleção limitada de candidatas

- **Status:** VALIDADO — QA revalidou `CT-PB33-01..06` em 2026-07-31. `DEF-PB33-01` corrigido: cada
  perfil soma orçamento de voz 1 mesmo em 500×50, preservando pesos absolutos separadamente.
  Evidência focada: `26 passed`; regressão completa Dev: `457 passed, 6 skipped`, mantendo apenas
  falhas preexistentes fora da PB-33 (PB-02/PB-06). Relatório: `PB-33.md`.
- **Objetivo:** diferenciar preferência forte de repertório ocasional antes do ranking coletivo.
- **Dependências:** PB-32.
- **Plano de implementação:** modelo puro de sinal ponderado; pesos default `1.00/0.85/0.65/0.45/0.35`;
  bônus de recorrência limitado; similaridade/afinidade ponderadas; amostragem estável contextual de
  no máximo 250 faixas por pessoa; dedupe global mantendo contribuidores e proveniência agregada.
- **Arquivos previstos:** novos módulos ou evolução de `engine/taste.py`, `candidates.py`,
  `scoring.py`, `weights.py` e testes `test_pb33_weighted_library.py`.
- **Testes obrigatórios:** `CT-PB33-01..06`.
- **Migração:** nenhuma; motor recebe DTOs preparados pelo serviço.
- **Riscos:** regressão de métricas, viés por tamanho e custo de enriquecer candidatas demais.

#### PB-34 — Integração e observabilidade da biblioteca ampliada

- **Status:** A-FAZER — depende de PB-33 `VALIDADO`.
- **Objetivo:** usar a biblioteca no pipeline sem perder fallback, privacidade ou clareza operacional.
- **Dependências:** PB-31, PB-32 e PB-33.
- **Plano de implementação:** `GET/POST /me/music-library`; status na Home existente; carregamento
  da biblioteca em `generation_service`; fallback para PB-08; reuso de ID/URI; explicação agregada
  das origens no resultado.
- **Arquivos previstos:** API/schema/serviço de música, geração/resultado, Home/apiClient/CSS e testes
  `test_pb34_library_generation.py`.
- **Testes obrigatórios:** `CT-PB34-01..06`.
- **Migração:** nenhuma prevista além das definidas nos PBs 30–32.
- **Riscos:** gerar antes do primeiro sync, expor origem privada e bloquear o fluxo em cache stale.

### Testes integrados da Sprint 7

Ver `PLANO_TESTES.md` → "Testes integrados da Sprint 7". Devem comprovar: três usuários com no
máximo 500 faixas cada; sync fresco sem rede; update incremental por `snapshot_id`; rate limit/quota
com cache preservado; pool de no máximo 250 por pessoa; geração de 20–30 faixas; privacidade e
remoção; regressão completa; e uma validação real sanitizada dos novos endpoints Spotify.

### Critérios de encerramento da Sprint 7

- [ ] PB-30..34 `VALIDADO` individualmente, um por vez;
- [ ] nenhuma biblioteca possui mais de 500 faixas únicas;
- [ ] nenhuma geração recebe mais de 250 candidatas por integrante antes do dedupe global;
- [ ] sync inicial não faz N+1 por faixa e sync fresco faz zero chamada Spotify;
- [ ] 429/quota/403/reauth e concorrência mantêm estado consistente;
- [ ] `DELETE /auth/me` remove inventário, biblioteca e sinais pessoais;
- [ ] motor puro, determinístico e justo para bibliotecas de tamanhos diferentes;
- [ ] testes integrados, regressão, migrações e build frontend aprovados;
- [ ] spike/e2e real com as contas autorizadas registrado sem tokens ou dados pessoais.

---

## 12. Marcos de entrega (referência técnica — não controlam a ordem)

Mantidos como referência de entregas e riscos. A ordem oficial de implementação é por Sprint (acima).

| Marco | Descrição | Sprint(s) correspondente(s) |
|---|---|---|
| M0 | Preparação externa (app Spotify, redirect, contas, versões, `.env`) | Pré-Sprint 1 / Sprint 1 |
| M1 | Fundação + validação do Spotify (`PB-01`, spike, `PB-02`) | Sprint 1 |
| M2 | Sala utilizável (`PB-04`, `PB-05`, `PB-06`, `PB-08`) | Sprint 1 |
| M3 | Motor de negociação (`PB-09`–`PB-12`) | Sprint 2 |
| M4 | Fluxo principal completo (`PB-13`, `PB-14`, `PB-15`) | Sprint 2 → Sprint 3 |
| M5 | Complementos priorizados (`PB-07`, `PB-16`, `PB-17`, `PB-18`, `PB-03`, `PB-19`, `PB-20`) | Sprint 3 → Sprint 4 |

### M0 — Preparação externa (checklist preservado)

- [ ] Criar o aplicativo no Spotify Developer Dashboard.
- [ ] Configurar a redirect URI local.
- [ ] Definir as contas autorizadas para a demonstração.
- [x] Confirmar as versões de Python, Node.js e Docker usadas pela equipe. — Python 3.11.9 e Docker
  29.6.1/Compose v5.2.0 confirmados; **Node.js/npm ausentes** no host (pendência do PB-01).
- [x] Preparar variáveis locais sem versionar segredos. — `.env.example` sem segredos; `.env` ignorado.

## 13. Decisões registradas

| Data | Decisão | Motivo |
|---|---|---|
| 2026-07-12 | Implementar primeiro o caminho principal do MVP. | Reduzir dispersão e obter um fluxo demonstrável cedo. |
| 2026-07-12 | Tratar LLM, Last.fm, Vibe Check e feedback como complementos após o fluxo principal. | Todos possuem fallback ou não são indispensáveis à primeira validação. |
| 2026-07-12 | Executar um spike Spotify no primeiro marco/Sprint. | Antecipar o maior risco externo do projeto. |
| 2026-07-12 | Versões de referência: Python 3.11.9, Docker 29.6.1 / Compose v5.2.0. Node.js/npm ausentes. | Cumprir o M0 e explicar a única verificação pendente do PB-01. |
| 2026-07-12 | Stack do backend: FastAPI + SQLAlchemy 2.0 + Alembic + `psycopg2-binary`; config via `pydantic-settings`. | Base estável em Python 3.11; segredos só em variáveis de ambiente. |
| 2026-07-12 | Migração inicial cria somente a tabela `users`. | Validar upgrade/downgrade real sem antecipar tabelas de histórias futuras. |
| 2026-07-13 | Reorganizar a execução por Sprint (mantendo M0–M5 como referência) e criar `PLANO_TESTES.md`. | Alinhar o processo ao fluxo obrigatório Sprint → PB → testes → validação. |
| 2026-07-17 | Reabrir PB-17 dentro da Sprint 3 sem reabrir PB-11/PB-12. | Teste real em grupo mostrou que o contexto é persistido, mas não consumido pelo motor; CT-PB17-05 e CT-S3-INT-02 contradizem o “não aplicável” da validação histórica. |
| 2026-07-18 | Abrir a Sprint 4 por exceção explícita do usuário, sem promover evidências pendentes a `VALIDADO`. | A autorização libera implementação, mas a dívida de QA continua rastreada. |
| 2026-07-18 | No PB-03, anonimizar `users` em vez de excluir fisicamente a linha. | A FK do host usa `ON DELETE CASCADE`; exclusão apagaria salas e artefatos de terceiros. |
| 2026-07-31 | Planejar Sprint 7 com biblioteca única de até 500 faixas por pessoa, formada por Tops e playlists elegíveis. | Ampliar cobertura sem tratar toda playlist como gosto forte nem elevar chamadas/armazenamento sem limite. |
| 2026-07-31 | Manter no máximo 250 candidatas ativas por pessoa e pesos por origem. | Separar repertório armazenado do pool de execução e preservar justiça entre bibliotecas desiguais. |
| 2026-07-31 | Promover Sprint 7 e remover dependências formais de Sprints anteriores por decisão explícita do Product Owner. | Atender ao prazo urgente, mantendo dívidas históricas rastreadas separadamente e uma cadeia interna PB-30→34. |

## 14. Riscos e bloqueios atuais

- O Spotify Development Mode limita o aplicativo a cinco usuários autorizados (R-01).
- Os endpoints permitidos precisam ser confirmados em um aplicativo novo (spike — R-02).
- O núcleo estimado do MVP excede uma sprint e pode ultrapassar um mês (R-10).
- **PB-01:** bloqueio de Node removido; frontend nativo iniciou e respondeu HTTP 200. Falta apenas o
  QA reexecutar CT-PB01-06 e registrar seu veredito formal.
- A capacidade real da equipe (velocidade) ainda precisa ser medida na Sprint 1.
- **INC-PB17-CTX-01:** **encerrado (QA 2026-07-18).** PB-17 `VALIDADO` na revalidação independente.
- **DEF-S3-INT-03-01 (Alta):** **FECHADO (QA revalidação independente 2026-07-18).** O Vibe Check é
  consumido pelo ranqueamento com influência limitada a 20%; o reprodutor QA intocado passa e a
  sondagem adversarial confirma que o sinal não inverte consenso forte, preserva o "pular" e é
  monotônico em `valence`. Não bloqueia mais o encerramento.
- **Sprint 6:** PB-25..29 possuem evidência técnica do implementador e seguem em QA paralelo; por
  decisão do Product Owner em 2026-07-31, não bloqueiam mais a Sprint 7.
- **Sprint 7 / Spotify:** novo escopo e leitura de itens de playlist exigem spike real; 403 e
  `QUOTA_EXCEEDED` devem ser tratados sem contorno e sem apagar cache utilizável.
- **Sprint 7 / dados:** limite absoluto de 500 faixas únicas por pessoa, retenção temporária,
  metadados mínimos e remoção no disconnect são requisitos, não otimizações opcionais.

## 15. Diário de retomada

Atualizar esta seção ao encerrar cada sessão.

- **Data da última sessão:** 2026-07-31.
- **Sprint/branch de trabalho atual:** Sprint 7 na branch `feat/SPRINT06/stabilization`.
- **PB em andamento:** nenhum; PB-33 `VALIDADO` e PB-34 é o próximo acionável.
- **Último resultado concluído:** QA revalidou PB-33 com `26 passed`; `DEF-PB33-01` encerrado.
- **Onde parou:** perfil ponderado, pool limitado e justiça por orçamento de voz aprovados.
- **Próxima ação exata:** Dev pode iniciar somente PB-34 em uma nova fase.
- **Comando/teste para retomada:**
  ```bash
  ./scripts/orquestrar.sh --list --no-pull
  ```
- **Bloqueios:** nenhum para validar PB-32. O spike real permanece reservado à validação integrada e
  depende das três contas de demonstração autorizadas no app.

## 16. Checklist de encerramento de sessão

- [x] Rodei as verificações relevantes. — QA com 14 focados, regressão backend 434/6, build Vite,
  migração reversível e rollback atômico.
- [x] Comparei o plano com o backlog e os limites da integração Spotify.
- [x] Atualizei status após validação independente. — PB-31 `VALIDADO`.
- [x] Registrei decisões ou bloqueios novos. — teto 500, TTL 7 dias, pool 250 e exceção do Product Owner.
- [x] Atualizei o diário de retomada com a próxima ação exata.
- [x] Atualizei a documentação afetada. — backlog, planos de execução/testes e mapa de trabalho.
- [x] Confirmei que nenhum segredo ou token foi adicionado ao diff versionado.
- [x] Commit do PB-31 — `04ac876`.

## 17. Modelos de prompt (Implementação e Teste)

A coordenação entre os dois papéis é definida no **`AGENTS.md`** (raiz do repositório). A regra central
é o **portão de espera**: o Agente de Implementação **para e aguarda** o veredito do Agente de Teste
antes de iniciar o próximo PB ou encerrar a Sprint. Os prompts abaixo devem ser usados em fases
separadas e explícitas.

### 17.1 Prompt do Agente de Implementação (Dev)

```text
PAPEL: Agente de Implementação (Dev). Leia AGENTS.md, este plano (§4 e a Sprint ativa) e
PLANO_TESTES.md do PB antes de tocar no código.

Sprint ativa: Sprint N
PB ativo: PB-XX   (apenas UM PB por vez)
Objetivo desta sessão:
Critérios de aceitação envolvidos:
Arquivos ou componentes em escopo:
Fora do escopo:

Passos: (1) verificar dependências; (2) planejar o recorte; (3) implementar SOMENTE este PB;
(4) criar/atualizar os testes do PB; (5) rodar e corrigir localmente; (6) atualizar este plano
(Status do PB, resultado, arquivos, riscos, próxima ação).

Ao terminar, emita LITERALMENTE:  PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO
e PARE. NÃO inicie o próximo PB. AGUARDE o veredito do Agente de Teste.
Se REPROVADO, corrija SOMENTE este PB e reemita "IMPLEMENTADO".
```

### 17.2 Prompt do Agente de Teste (QA)

```text
PAPEL: Agente de Teste (QA), autoridade de validação. Não corrija código de produção; execute,
avalie e reporte. Leia AGENTS.md e PLANO_TESTES.md do PB.

Gatilho: "PB-XX IMPLEMENTADO — INICIANDO VALIDAÇÃO".

Passos: (1) selecionar os casos obrigatórios de PB-XX no PLANO_TESTES.md; (2) executar sucesso,
entrada inválida, ausência de dados, acesso não autorizado, duplicidade, limites, falha externa,
persistência, idempotência, privacidade e regressão relacionada (quando aplicável); (3) registrar
Status + evidência de cada CT (sem segredos); (4) confirmar cada critério de aceitação.

Veredito (emitir LITERALMENTE):
- tudo passa e critérios cobertos ► PB-XX VALIDADO — TODOS OS TESTES OBRIGATÓRIOS PASSARAM
- caso contrário               ► PB-XX REPROVADO NA VALIDAÇÃO — CORREÇÕES NECESSÁRIAS
                                  (listar CT, passos, obtido × esperado, evidência)

Ao fim da Sprint, repetir com os testes integrados + regressão e emitir o veredito da Sprint
(SPRINT N CONCLUÍDA / SPRINT N REPROVADA).
```

> O Dev **só** inicia o próximo PB após `PB-XX VALIDADO` emitido pelo QA. Exceção: bloqueio externo
> documentado quando o próximo PB não depende do item bloqueado (ver `AGENTS.md` §2).
