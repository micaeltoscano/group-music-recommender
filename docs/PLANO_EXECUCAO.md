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
| Sprint 1 | Fundação técnica + autenticação + sala utilizável | PB-01, PB-02, PB-04, PB-05, PB-06, PB-08 | 25 | **Em andamento** |
| Sprint 2 | Núcleo do motor de negociação (PNE) | PB-09, PB-10, PB-11, PB-12, PB-13 | 24 | A fazer |
| Sprint 3 | Fluxo principal ponta a ponta (playlist real + resultado) | PB-14, PB-15, PB-16, PB-07 | 23 | A fazer |
| Sprint 4 | Complementos e consolidação de qualidade | PB-03, PB-17, PB-18, PB-19, PB-20 | 22 | A fazer |
| Futuro | Evolução do produto (fora do MVP) | PB-21, PB-22 | 18 | A fazer |

- **MVP (núcleo):** PB-01, PB-02, PB-04, PB-05, PB-06, PB-08, PB-09, PB-10, PB-11, PB-12, PB-13, PB-14, PB-15, com apoio contínuo de PB-20.
- **Sprint ativa:** Sprint 1. **PB ativo:** PB-01 (em teste — ver seção 6).

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

- **Status:** Em teste *(implementação concluída no backend/banco/migração; falta uma evidência do frontend)*
- **Objetivo:** base local integrada e reproduzível de frontend (React/Vite), backend (FastAPI) e
  banco (PostgreSQL) com SQLAlchemy/Alembic.
- **Dependências:** Nenhuma.
- **Critérios de aceitação:**
  1. [~] Frontend e backend iniciam conforme instruções documentadas. — **Backend: verificado.**
     **Frontend: build verificado** em container Node 20; **falta o `npm run dev` nativo** (Node ausente no host).
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
- **Riscos:** ambiente sem Node local impede a última verificação nativa do frontend.
- **Bloqueios:** Node.js/npm ausentes no host (o build em container supre parcialmente).
- **Resultado da implementação:** backend + banco + migração + frontend (scaffold que compila) prontos.
- **Resultado dos testes (2026-07-13):** `pytest` **4 passed**; Alembic `upgrade head` → `downgrade base`
  → `upgrade head` sem erros; `/health` e `/health/db` → 200; `.env` não rastreado e vazio;
  frontend `npm install` + `vite build` OK em container Node 20 (28 módulos, `dist/` gerado).
- **Próxima ação exata:** instalar Node.js ≥ 18 no host e rodar `cd frontend && npm install && npm run dev`,
  confirmando a tela de status em `http://localhost:5173`; então marcar o critério 1 como concluído e
  fechar o PB-01 (`PB-01 VALIDADO`).

#### PB-02 — Autenticação com Spotify

- **Status:** A fazer
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
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** concluir M0 (app Spotify + redirect) e implementar `GET /auth/login`.

#### PB-04 — Criação de sala efêmera

- **Status:** A fazer
- **Objetivo:** criar sala temporária com código curto único, host como primeiro integrante e
  expiração de 24h.
- **Dependências:** PB-01 e PB-02.
- **Critérios de aceitação:**
  1. Apenas usuário autenticado cria sala.
  2. Cada sala recebe código curto único.
  3. Criador registrado como host e primeiro integrante.
  4. Expiração de 24h a partir da criação.
  5. Retornar código e dados iniciais da sala.
- **Plano de implementação:** `POST /rooms` cria `music_sessions` (code único, `host_user_id`,
  `status=open`, `expires_at = now + 24h`) e `music_session_members` (host). Geração de código
  colisão-resistente. Migração para `music_sessions` e `music_session_members`.
- **Arquivos ou módulos previstos:** `backend/app/api/rooms.py`, `backend/app/services/room_service.py`,
  `backend/app/db/models.py`, `frontend/` (Home), nova migração Alembic.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-04) — só autenticado cria, unicidade do
  código, host como membro, `expires_at` = 24h, payload de retorno.
- **Evidências necessárias:** registro persistido, código único sob concorrência, resposta da API.
- **Riscos:** colisão de código; criação sem autenticação.
- **Bloqueios:** depende de PB-02.
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** modelar `music_sessions`/`music_session_members` e `POST /rooms`.

#### PB-05 — Entrada e acompanhamento da sala

- **Status:** A fazer
- **Objetivo:** entrar por código sem duplicidade, respeitar o limite de 5 integrantes, proteger o
  acesso (403 para não-membros) e atualizar a sala por polling.
- **Dependências:** PB-02 e PB-04.
- **Critérios de aceitação:**
  1. Rejeitar código inexistente ou sala expirada.
  2. Máximo de cinco integrantes.
  3. Mesmo usuário não é associado duas vezes.
  4. Só membros consultam a sala; demais recebem 403.
  5. Interface atualiza por polling a cada 3–5s.
- **Plano de implementação:** `POST /rooms/{code}/join` (valida existência/expiração/limite/duplicidade,
  PK composta em `music_session_members` evita duplicidade) e `GET /rooms/{code}` (guarda de membro,
  lista integrantes e estado). Polling no frontend a cada 3–5s.
- **Arquivos ou módulos previstos:** `backend/app/api/rooms.py`, `backend/app/services/room_service.py`,
  `frontend/` (Room + polling em `apiClient`).
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-05) — código inválido/expirado, 6º membro
  bloqueado, join duplicado idempotente, 403 para não-membro, atualização por polling.
- **Evidências necessárias:** respostas 403/409/limite, estado atualizado no polling.
- **Riscos:** condição de corrida no limite de 5; vazamento de dados de sala alheia.
- **Bloqueios:** depende de PB-04.
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar `join` com verificação de limite/duplicidade e guarda de membro.

#### PB-06 — Contexto e modo de consenso

- **Status:** A fazer
- **Objetivo:** permitir que **somente o host** defina ocasião/descrição e o modo (Democrático ou
  Festa Segura), disponibilizando as alterações na próxima atualização da sala.
- **Dependências:** PB-04.
- **Critérios de aceitação:**
  1. Somente o host altera contexto e modo.
  2. Aceitar ocasião, descrição livre ou ambos.
  3. Modo é Democrático ou Festa Segura.
  4. Alterações visíveis na próxima atualização da sala.
- **Plano de implementação:** `PUT /rooms/{code}/context` e `PUT /rooms/{code}/mode` com guarda de host;
  persistir `occasion`, `description`, `mode` em `music_sessions`; validar enum de modo.
- **Arquivos ou módulos previstos:** `backend/app/api/rooms.py`, `backend/app/schemas/`,
  `frontend/` (Room — formulário de contexto/modo).
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-06) — membro comum recebe erro apropriado,
  host altera, modo inválido rejeitado, propagação via polling.
- **Evidências necessárias:** resposta 403 para membro comum, persistência do contexto/modo.
- **Riscos:** autorização insuficiente (membro alterando contexto).
- **Bloqueios:** depende de PB-04.
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar as rotas de contexto/modo com guarda de host.

#### PB-08 — Coleta e cache de dados musicais

- **Status:** A fazer
- **Objetivo:** obter top tracks/artists via Spotify e armazenar snapshots com validade (default 7
  dias), reutilizando snapshots válidos e sinalizando reautenticação em falha de token.
- **Dependências:** PB-02.
- **Critérios de aceitação:**
  1. Consultar apenas endpoints Spotify autorizados no MVP.
  2. Faixas e artistas associados ao usuário em um snapshot.
  3. Snapshot com menos de 7 dias reutilizado por padrão.
  4. Snapshot vencido atualizado antes da geração.
  5. Falha de renovação de token marca necessidade de nova autenticação.
- **Plano de implementação:** `GET /me/top` e `POST /me/refresh-music-snapshot`; persistir
  `user_music_snapshots` (`top_tracks_json`, `top_artists_json`, `fetched_at`, `time_range`);
  política de expiração configurável; integração com refresh central do `SpotifyClient`.
- **Arquivos ou módulos previstos:** `backend/app/api/music.py`, `backend/app/clients/spotify_client.py`,
  `backend/app/db/models.py` (`user_music_snapshots`), nova migração Alembic.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-08) — reuso de snapshot fresco, refetch de
  vencido, falha de token → reauth, escopo de endpoints, resposta 429 mockada.
- **Evidências necessárias:** snapshot persistido, reuso vs refetch conforme idade, marcação de reauth.
- **Riscos:** R-02 (endpoints), R-03 (token), R-13 (integrante sem dados).
- **Bloqueios:** depende de PB-02 (tokens válidos).
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** modelar `user_music_snapshots` e implementar coleta com cache por idade.

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

**Em andamento** — PB-01 em teste; PB-02, PB-04, PB-05, PB-06 e PB-08 a fazer.

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

- **Status:** A fazer
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
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar `engine/taste.py` com testes de compatibilidade.

#### PB-10 — Geração do conjunto de candidatas

- **Status:** A fazer
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
- **Arquivos ou módulos previstos:** `backend/app/engine/` (candidate pool), `backend/app/services/generation_service.py`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-10) — dedupe, cobertura de integrantes,
  registro de origem, descarte motivado.
- **Evidências necessárias:** pool sem duplicatas com origem e descartes registrados.
- **Riscos:** viés para a maioria na montagem (mitigado no PB-12).
- **Bloqueios:** depende de PB-09.
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar montagem/deduplicação do pool com origem e descarte.

#### PB-11 — Pontuação individual e coletiva

- **Status:** A fazer
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
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar `scoring.py` e `weights.py` com testes de valores esperados.

#### PB-12 — Rejeição, justiça e modos de consenso

- **Status:** A fazer
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
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar `fairness.py` com penalidade de rejeição e representação mínima.

#### PB-13 — Controle e histórico da geração

- **Status:** A fazer
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
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar Generation Lock e o modelo `playlist_runs`.

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

**A fazer.**

---

## Sprint 3 — Fluxo principal ponta a ponta

### Objetivo da Sprint

Ao final da Sprint 3, o fluxo principal do MVP funciona de ponta a ponta: a seleção do motor vira uma
**playlist privada real na conta do host** (via Spotify Search com o token do host), com tela de
resultado e explicabilidade; o contexto do host é interpretado de forma estruturada (LLM com fallback)
e o Vibe Check opcional está disponível.

### PBs incluídos

- PB-14 — Correspondência e criação da playlist no Spotify
- PB-15 — Resultado e explicabilidade
- PB-16 — Interpretação estruturada do contexto
- PB-07 — Vibe Check opcional

### Dependências da Sprint

- **De Sprints anteriores:** PB-11, PB-12, PB-13 (motor/execução) e PB-02 (token do host) para PB-14;
  PB-13 para PB-15; PB-06 e PB-10 para PB-16; PB-05 e PB-06 para PB-07.
- **Entre PBs:** PB-15 depende de PB-14. PB-16 e PB-07 são independentes de PB-14/PB-15 dentro da Sprint.
- **Externas:** `ANTHROPIC_API_KEY` (LLM) para PB-16 — com fallback determinístico obrigatório.

### Ordem de implementação

1. PB-14  *(fecha o caminho crítico de playlist real)*
2. PB-15  *(depende de PB-14)*
3. PB-16  *(enriquecimento de contexto; tem fallback)*
4. PB-07  *(opcional; não bloqueia a geração)*

### Execução dos PBs

#### PB-14 — Correspondência e criação da playlist no Spotify

- **Status:** A fazer
- **Objetivo:** resolver candidatas via Spotify Search com o token do host, validar disponibilidade e
  criar playlist privada (20–30 faixas, máx. 2/artista), guardando id/URL na execução.
- **Dependências:** PB-02, PB-11, PB-12 e PB-13.
- **Critérios de aceitação:**
  1. Busca usa o mercado do token do host quando disponível.
  2. Título/artista normalizados (live, remastered, acoustic…).
  3. Abaixo da confiança mínima ou indisponível → descartado com motivo.
  4. Seleção final: 20–30 músicas, máx. 2 por artista.
  5. Playlist privada por padrão, na conta do host.
  6. `spotify_playlist_id` e URL armazenados na execução.
- **Plano de implementação:** track matching (normalização/variantes/confiança) em `SpotifyClient`;
  checagem de mercado; criação de playlist + add items; persistir `playlist_run_tracks`
  (`match_confidence`, `discard_reason`, `source`, `position`).
- **Arquivos ou módulos previstos:** `backend/app/clients/spotify_client.py`,
  `backend/app/services/generation_service.py`, `backend/app/db/models.py` (`playlist_run_tracks`), migração.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-14) — normalização de variantes, confiança
  mínima, desempate por popularidade, indisponível no mercado, cap de 2/artista, faixa 20–30, privada.
- **Evidências necessárias:** playlist criada de fato no Spotify do host; descartes motivados registrados.
- **Riscos:** R-02, R-04, R-05.
- **Bloqueios:** contas Spotify da demo; motor (PB-11/PB-12) e execução (PB-13).
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar track matching e criação de playlist com o token do host.

#### PB-15 — Resultado e explicabilidade

- **Status:** A fazer
- **Objetivo:** tela de resultado com link da playlist, compatibilidade, fairness, representação por
  integrante e justificativas legíveis, sem expor dados sensíveis de terceiros.
- **Dependências:** PB-13 e PB-14.
- **Critérios de aceitação:**
  1. Apresentar o link da playlist criada.
  2. Apresentar compatibilidade e fairness score da execução.
  3. Representação dos integrantes em formato compreensível.
  4. Cada música com justificativa resumida.
  5. Explicações não identificam rejeições/dados sensíveis de outro integrante.
- **Plano de implementação:** `GET /rooms/{code}/result`; montagem de `explanation_json`;
  tela Result no frontend com representação agregada e motivos por faixa.
- **Arquivos ou módulos previstos:** `backend/app/api/rooms.py`, `backend/app/services/`, `frontend/` (Result).
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-15) — presença do link/métricas,
  representação, privacidade das explicações, acesso restrito a membros.
- **Evidências necessárias:** payload de resultado; verificação de que nenhuma rejeição individual é exposta.
- **Riscos:** R-08 (privacidade nas explicações).
- **Bloqueios:** depende de PB-14.
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar `GET /rooms/{code}/result` e a tela Result.

#### PB-16 — Interpretação estruturada do contexto

- **Status:** A fazer
- **Objetivo:** LLM interpreta a descrição livre do host em um schema JSON validado, com fallback
  determinístico e sem enviar dados brutos de tops ao LLM.
- **Dependências:** PB-06 e PB-10.
- **Critérios de aceitação:**
  1. Saída segue schema JSON (ocasião, humor, energia, tags +/-, itens a evitar).
  2. Resposta inválida rejeitada sem interromper a geração.
  3. Sem LLM, segue com consenso/afinidade/popularidade.
  4. Dados brutos de tops não vão ao LLM.
  5. LLM não decide diretamente as músicas.
- **Plano de implementação:** `LLMClient` (Claude, JSON estruturado) + validação de schema + fallback;
  cache de contexto em `playlist_runs.llm_context_json`.
- **Arquivos ou módulos previstos:** `backend/app/clients/llm_client.py`, `backend/app/schemas/` (context),
  `backend/app/services/generation_service.py`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-16) — JSON inválido → fallback,
  LLM ausente → fallback, privacidade (sem dados brutos), schema válido.
- **Evidências necessárias:** logs sem dados brutos; fallback exercido; schema validado.
- **Riscos:** R-06 (LLM inválido/indisponível).
- **Bloqueios:** `ANTHROPIC_API_KEY` para o caminho com IA (fallback não depende).
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar `LLMClient` com validação de schema e fallback determinístico.

#### PB-07 — Vibe Check opcional

- **Status:** A fazer
- **Objetivo:** questionário curto (3–5 perguntas), pulável, cujas respostas viram preferências
  normalizadas (0–1) por usuário/sala, atualizáveis a cada nova resposta.
- **Dependências:** PB-05 e PB-06.
- **Critérios de aceitação:**
  1. Entre 3 e 5 perguntas.
  2. Usuário pode pular sem bloquear a geração.
  3. Respostas armazenadas por usuário e sala.
  4. Preferências derivadas entre 0 e 1.
  5. Nova resposta do mesmo usuário atualiza a participação seguinte.
- **Plano de implementação:** `GET/POST /rooms/{code}/vibe-check`; persistir `vibe_check_answers`
  (`answers_json`, `derived_preferences_json`); mapear respostas → variáveis do README §9.
- **Arquivos ou módulos previstos:** `backend/app/api/vibe_check.py`, `backend/app/schemas/`,
  `backend/app/db/models.py` (`vibe_check_answers`), `frontend/` (Room — Vibe Check), migração.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-07) — limites 3–5, pular não bloqueia,
  faixa [0,1], atualização por regravação, associação usuário/sala.
- **Evidências necessárias:** `derived_preferences_json` correto; geração segue ao pular.
- **Riscos:** R-11 (abandono por questionário).
- **Bloqueios:** depende de PB-05/PB-06.
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar rotas do Vibe Check e derivação de preferências.

### Testes integrados da Sprint 3

Ver `PLANO_TESTES.md` → "Testes integrados da Sprint 3". Cobrem, no mínimo:

- Fluxo e2e: login → sala → contexto/modo → snapshot → motor → **playlist real** → resultado explicável.
- Contexto: "festa alegre" vs "estudo relaxante" muda tags/candidatas; LLM inválido → fallback sem quebrar.
- Vibe Check: pular → geração segue; responder → influencia o ranking.
- Regressão das Sprints 1 e 2: auth/salas/motor/execução continuam funcionando.
- Segurança/privacidade: token do host nunca no frontend; explicações sem dados sensíveis de terceiros.
- Falha de serviço externo: Search não acha/indisponível → descarta com motivo, sem crashar.

### Critérios de encerramento da Sprint 3

- [ ] PB-14, PB-15, PB-16, PB-07 concluídos e critérios validados;
- [ ] testes individuais de cada PB passando;
- [ ] testes integrados da Sprint 3 passando;
- [ ] regressão das Sprints 1 e 2 passando;
- [ ] playlist real demonstrável de ponta a ponta;
- [ ] bloqueios documentados; plano atualizado.

### Evidências da Sprint 3

- Comandos/telas/integrações: — (a preencher)
- Playlist criada no Spotify (id/URL): — (a preencher)
- Data da validação: — (a preencher)

### Status da Sprint 3

**A fazer.**

---

## Sprint 4 — Complementos e consolidação de qualidade

### Objetivo da Sprint

Ao final da Sprint 4, a experiência está complementada (logout/remoção de dados, enriquecimento de
contexto por Last.fm, sequenciamento da playlist e coleta de feedback) e a qualidade consolidada
(testes, fallbacks, proteção de dados, documentação e roteiro de demonstração).

### PBs incluídos

- PB-03 — Logout e remoção de dados
- PB-17 — Enriquecimento de contexto com Last.fm
- PB-18 — Sequenciamento da experiência musical
- PB-19 — Feedback pós-playlist
- PB-20 — Qualidade, robustez e documentação

### Dependências da Sprint

- **De Sprints anteriores:** PB-02 (PB-03); PB-10 e PB-16 (PB-17); PB-12 e PB-14 (PB-18); PB-15 (PB-19).
- **PB-20:** consolida testes/qualidade de todos os PBs (execução contínua desde a Sprint 1, encerrada aqui).
- **Externas:** `LASTFM_API_KEY` (PB-17) — com cascata de fallback obrigatória.

### Ordem de implementação

1. PB-03
2. PB-17
3. PB-18
4. PB-19
5. PB-20  *(consolidação final)*

### Execução dos PBs

#### PB-03 — Logout e remoção de dados

- **Status:** A fazer
- **Objetivo:** encerrar sessão (invalidando-a no backend) e excluir/anonimizar dados pessoais sem
  expor tokens ou dados de terceiros.
- **Dependências:** PB-02.
- **Critérios de aceitação:**
  1. Logout invalida a sessão da aplicação no backend.
  2. Após logout, rotas autenticadas respondem como não autorizadas.
  3. Remoção exclui/anonimiza os dados pessoais previstos.
  4. Operação não expõe tokens nem dados de outros integrantes.
- **Plano de implementação:** `POST /auth/logout` (invalida `app_sessions`); rotina de remoção/anonimização.
- **Arquivos ou módulos previstos:** `backend/app/api/auth.py`, `backend/app/services/`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-03) — sessão invalidada, 401 pós-logout,
  remoção efetiva, não exposição de terceiros.
- **Evidências necessárias:** rota autenticada retornando não autorizada após logout; dados removidos.
- **Riscos:** R-08.
- **Bloqueios:** depende de PB-02.
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar logout com invalidação de sessão e fluxo de remoção.

#### PB-17 — Enriquecimento de contexto com Last.fm

- **Status:** A fazer
- **Objetivo:** tags do Last.fm (faixa → artista) combinadas com gêneros Spotify, em cache com
  confiança, sem interromper a geração em erro/ausência.
- **Dependências:** PB-10 e PB-16.
- **Critérios de aceitação:**
  1. Tenta tags da faixa antes das do artista.
  2. Sem Last.fm, usa gêneros Spotify e demais sinais.
  3. Cada resultado registra fonte e confiança.
  4. Consultas repetidas reutilizam cache válido.
  5. Resposta vazia/erro não interrompe a geração.
- **Plano de implementação:** `LastFmClient` + cascata; cache em `track_context_cache` com `confidence`/`source`.
- **Arquivos ou módulos previstos:** `backend/app/clients/lastfm_client.py`,
  `backend/app/db/models.py` (`track_context_cache`), migração.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-17) — cascata, cache válido reutilizado,
  erro/vazio não quebra, confiança por fonte.
- **Evidências necessárias:** `track_context_cache` com fonte/confiança; cascata exercida.
- **Riscos:** R-07 (sem tags).
- **Bloqueios:** `LASTFM_API_KEY` para o caminho principal (cascata não depende).
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar `LastFmClient` com cascata e cache.

#### PB-18 — Sequenciamento da experiência musical

- **Status:** A fazer
- **Objetivo:** ordenar a seleção final com abertura de alta aceitação, faixas arriscadas no meio,
  sem 2 do mesmo artista consecutivas e respeitando o cap de 2/artista.
- **Dependências:** PB-12 e PB-14.
- **Critérios de aceitação:**
  1. Sem duas do mesmo artista consecutivas.
  2. Começar por música de alta aceitação.
  3. Faixas de maior risco preferencialmente no meio.
  4. Respeitar o cap de 2 músicas por artista.
- **Plano de implementação:** `engine/sequencer.py` (regras determinísticas sobre a seleção final).
- **Arquivos ou módulos previstos:** `backend/app/engine/sequencer.py`, testes.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-18) — sem repetição consecutiva,
  abertura forte, risco no meio, cap respeitado.
- **Evidências necessárias:** ordem final validada por testes.
- **Riscos:** conflito entre regras e cap (empates).
- **Bloqueios:** depende de PB-14 (seleção final).
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar `engine/sequencer.py` com as regras do README §15.

#### PB-19 — Feedback pós-playlist

- **Status:** A fazer
- **Objetivo:** coletar feedback por faixa (like/dislike/more_like_this/never_again) e geral
  (representação/satisfação), associado à execução correta, sem uso no ranking do MVP.
- **Dependências:** PB-15.
- **Critérios de aceitação:**
  1. Marcar like/dislike/more_like_this/never_again por faixa.
  2. Informar satisfação e representação da playlist.
  3. Feedback associado ao usuário e à execução correta.
  4. Usuário não registra feedback em sala da qual não participa.
  5. Deixar explícito que o feedback é para evoluções futuras.
- **Plano de implementação:** `POST /playlist-runs/{id}/tracks/{track_id}/feedback` e
  `POST /playlist-runs/{id}/feedback`; persistir `member_track_feedback` e `playlist_feedback`.
- **Arquivos ou módulos previstos:** `backend/app/api/feedback.py`, `backend/app/db/models.py`, migração, `frontend/`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-19) — associação correta, bloqueio de
  não-membro, aviso de uso futuro, persistência.
- **Evidências necessárias:** feedback persistido e vinculado; não-membro bloqueado.
- **Riscos:** vinculação incorreta de execução.
- **Bloqueios:** depende de PB-15.
- **Resultado da implementação:** — (não iniciado)
- **Resultado dos testes:** — (não executado)
- **Próxima ação exata:** implementar rotas de feedback e persistência.

#### PB-20 — Qualidade, robustez e documentação

- **Status:** A fazer *(execução contínua desde a Sprint 1; consolidação na Sprint 4)*
- **Objetivo:** consolidar testes do motor e da API, mocks de clientes externos, proteção de dados,
  documentação e roteiro de demonstração do fluxo principal.
- **Dependências:** PB-02 a PB-19 (contínuo).
- **Critérios de aceitação:**
  1. Testes de motor: scoring, justiça, rejeição, duplicidade, cap por artista.
  2. Testes de API: autorização, entrada duplicada, Generation Lock.
  3. Clientes externos mockados: token expirado, 429, JSON inválido, busca sem resultado.
  4. Nenhum teste/log expõe tokens reais.
  5. README com instruções atualizadas.
  6. Roteiro de demonstração documentado.
- **Plano de implementação:** ampliar `backend/tests/`; revisar sanitização de logs; atualizar README;
  escrever roteiro de demo (pode consolidar em `PLANO_TESTES.md`/`README.md`).
- **Arquivos ou módulos previstos:** `backend/tests/**`, `README.md`, `docs/PLANO_TESTES.md`.
- **Testes obrigatórios do PB:** ver `PLANO_TESTES.md` §10 (PB-20) e todos os testes integrados.
- **Evidências necessárias:** suíte completa verde; README atualizado; roteiro de demo.
- **Riscos:** R-08 (vazamento em logs/testes).
- **Bloqueios:** depende da estabilidade dos PBs anteriores.
- **Resultado da implementação:** — (parcial: fundação de testes do PB-01 já existe)
- **Resultado dos testes:** — (4 testes de saúde já passam; suíte completa pendente)
- **Próxima ação exata:** ao longo das Sprints, manter cobertura; consolidar e documentar na Sprint 4.

### Testes integrados da Sprint 4

Ver `PLANO_TESTES.md` → "Testes integrados da Sprint 4". Cobrem, no mínimo:

- Logout/remoção: sessão invalidada e dados removidos sem afetar terceiros.
- Last.fm: cascata e cache exercidos; erro externo não quebra a geração.
- Sequenciamento: ordem final coerente sobre a playlist real.
- Feedback: coleta associada corretamente à execução; não-membro bloqueado.
- Regressão completa das Sprints 1–3.
- Qualidade: suíte completa verde; nenhum segredo exposto; documentação atualizada.

### Critérios de encerramento da Sprint 4

- [ ] PB-03, PB-17, PB-18, PB-19, PB-20 concluídos e critérios validados;
- [ ] testes individuais de cada PB passando;
- [ ] testes integrados da Sprint 4 passando;
- [ ] regressão das Sprints 1–3 passando;
- [ ] documentação e roteiro de demo prontos;
- [ ] bloqueios documentados; plano atualizado.

### Evidências da Sprint 4

- Comandos/telas/integrações: — (a preencher)
- Data da validação: — (a preencher)

### Status da Sprint 4

**A fazer.**

---

## Backlog de versões futuras (fora do MVP)

Não iniciar sem decisão explícita de escopo, e somente com o MVP estável.

- **PB-21 — Modo Descoberta** (Baixa, 5 pts; depende de PB-11, PB-12, PB-15).
- **PB-22 — Agrupamento de gostos e faixas-ponte** (Baixa, 13 pts; depende de PB-09, PB-11, PB-12, PB-15).

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

## 14. Riscos e bloqueios atuais

- O Spotify Development Mode limita o aplicativo a cinco usuários autorizados (R-01).
- Os endpoints permitidos precisam ser confirmados em um aplicativo novo (spike — R-02).
- O núcleo estimado do MVP excede uma sprint e pode ultrapassar um mês (R-10).
- **Bloqueio de ambiente (PB-01):** Node.js/npm não estão instalados no host, então o start nativo do
  frontend (`npm run dev`) não pôde ser verificado. O código Vite está pronto (build OK em container).
  Python 3.11.9 e Docker 29.6.1 já confirmados.
- A capacidade real da equipe (velocidade) ainda precisa ser medida na Sprint 1.

## 15. Diário de retomada

Atualizar esta seção ao encerrar cada sessão.

- **Data da última sessão:** 2026-07-13.
- **Sprint ativa:** Sprint 1.
- **PB em andamento:** PB-01 (fundação técnica) — **em teste** (implementação praticamente concluída).
- **Último resultado concluído:** fundação técnica criada e verificada — backend FastAPI + PostgreSQL
  (Docker) + Alembic (upgrade/downgrade da migração inicial) + `.env.example` sem segredos + `pytest`
  (**4 passed** em 2026-07-13). Frontend Vite com scaffold que compila (build OK em container Node 20).
- **Onde parou:** backend, banco e migração validados de ponta a ponta; **falta apenas executar o
  frontend nativo** — `npm run dev` não rodou porque Node.js/npm não estão instalados no host.
- **Qual teste encerra o PB-01:** executar o frontend nativo (`npm run dev`) e confirmar a tela de
  status em `http://localhost:5173` conectando a backend e banco (critério 1 do PB-01).
- **Próxima ação exata:** (1) instalar Node.js ≥ 18 e rodar `cd frontend && npm install && npm run dev`,
  confirmando `http://localhost:5173`; (2) marcar o critério "frontend inicia" como concluído e fechar
  o PB-01 (`PB-01 VALIDADO`); (3) concluir o M0 (app no Spotify Dashboard + redirect URI) e iniciar
  **PB-02 — Autenticação com Spotify**.
- **Comando/teste para retomada:**
  ```bash
  node --version            # confirmar Node ≥18 instalado
  cd frontend && npm install && npm run dev
  # em outro terminal, backend + banco:
  docker compose up -d db
  cd backend && source .venv/bin/activate && alembic upgrade head && uvicorn app.main:app --reload --port 8000
  ```
- **Bloqueios:** Node.js/npm ausentes no ambiente. Credenciais Spotify serão necessárias a partir de PB-02.

## 16. Checklist de encerramento de sessão

- [x] Rodei os testes e verificações relevantes. — `pytest` (4 passed, 2026-07-13).
- [x] Comparei o resultado com os critérios da história. — PB-01: 3/4 critérios verificados; "frontend inicia" pendente.
- [x] Atualizei checkboxes e status sem declarar trabalho incompleto como pronto.
- [x] Registrei decisões ou bloqueios novos. — reorganização por Sprint; criação do `PLANO_TESTES.md`.
- [x] Atualizei o diário de retomada com a próxima ação exata.
- [x] Atualizei a documentação afetada. — este plano e o novo `PLANO_TESTES.md`.
- [x] Confirmei que nenhum segredo ou token foi adicionado. — `.env` não rastreado e vazio.
- [ ] Preparei um commit pequeno e relacionado à história. — **pendente**: aguardando o usuário decidir sobre o commit.

## 17. Modelo de pedido para uma sessão assistida

```text
Sprint ativa: Sprint N
História ativa: PB-XX
Objetivo desta sessão:
Critérios de aceitação envolvidos:
Arquivos ou componentes em escopo:
Fora do escopo:
Como verificar (ver PLANO_TESTES.md → PB-XX):

Antes de alterar, inspecione o estado atual. Implemente somente este recorte,
execute os testes individuais do PB, corrija falhas e atualize o PLANO_EXECUCAO.md
com o ponto exato de retomada. Não inicie o próximo PB com testes obrigatórios falhando.
```
