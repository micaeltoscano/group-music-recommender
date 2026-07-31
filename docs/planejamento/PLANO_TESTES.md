# Plano de Testes — Vibe Check

Documento de validação do produto. Complementa o `BACKLOG_PRODUTO.md` (escopo e critérios de
aceitação), o `README.md` (arquitetura), o `PLANO_EXECUCAO.md` (execução por Sprint) e o `AGENTS.md`
(coordenação dos agentes). Aqui ficam os **testes individuais de cada PB** e os **testes integrados de
cada Sprint**.

> **Autoridade de validação:** este plano é executado pelo **Agente de Teste (QA)** definido no
> `AGENTS.md`. O **Agente de Implementação (Dev) para e aguarda** o veredito do QA — só avança para o
> próximo PB após `PB-XX VALIDADO`. O QA nunca declara `VALIDADO` sem executar os casos obrigatórios e
> registrar evidências, e atualiza o campo *Status* de cada `CT-*` ao final.

> Os testes não apenas confirmam que algo foi implementado: verificam se a implementação **resolve o
> problema**, cumpre os critérios de aceitação, respeita as regras de negócio e se comporta
> corretamente em situações **normais, inválidas e inesperadas**. Perspectiva adotada: QA tentando
> encontrar erros, omissões e interpretações incorretas.

## 1. Objetivo

Garantir que cada PB do MVP e cada incremento de Sprint sejam verificados com rigor, produzindo
evidências reproduzíveis, antes de qualquer PB ou Sprint ser considerado concluído. O plano serve de
guia executável para o agente de implementação e de referência de aceitação para o Product Owner.

## 2. Escopo

- **Coberto:** PBs das Sprints 1 a 5; PB-25..29 implementados tecnicamente na Sprint 6 e ainda
  aguardando validação; e PB-30..34 da Sprint 7 ativa por decisão do Product Owner.
- **MVP (núcleo):** PB-01, PB-02, PB-04, PB-05, PB-06, PB-08, PB-09, PB-10, PB-11, PB-12, PB-13,
  PB-14, PB-15, PB-16; com a qualidade aplicada continuamente pela Definition of Done.
- **Fora do escopo atual deste plano:** qualquer ampliação acima de 500 faixas por pessoa exige novo
  refinamento; a dívida de QA da Sprint 6 permanece separada e não é promovida a aprovação implícita.

## 3. Estratégia de testes

- **Pirâmide:** base ampla de testes unitários do motor (`engine/` puro), camada intermediária de
  testes de integração/API e de clientes externos mockados, e uma fina camada de testes de fluxo
  ponta a ponta (e2e) no fechamento de cada Sprint.
- **Motor determinístico:** todo cálculo do `engine/` é testado com entradas fixas e valores
  esperados, sem rede nem banco.
- **Serviços externos mockados:** Spotify, LLM e Last.fm são simulados para exercitar sucesso, erro,
  timeout, 429, JSON inválido e ausência de resultado, sem depender das APIs reais.
- **Validação real no fechamento:** o fluxo com contas Spotify reais é verificado ao final das Sprints
  3 e 4 (criação da playlist) e da Sprint 7 (consentimento, inventário, cache e geração ampliada).
- **Regressão:** ao final de cada Sprint, reexecutar os testes das Sprints anteriores.

## 4. Ambientes de teste

| Ambiente | Uso | Observações |
|---|---|---|
| Local (unit/integração) | `pytest` no backend | Banco SQLite em memória para testes de API; motor sem I/O. |
| Local (banco real) | Postgres via Docker Compose | Migrações Alembic (upgrade/downgrade). |
| Local (frontend) | Vite dev server / build | `npm run dev` (nativo) e `vite build` (container). |
| Externo mockado | Spotify/LLM/Last.fm simulados | Sem chamadas reais; respostas controladas. |
| Demonstração | Contas Spotify Premium autorizadas | Limite de 5 usuários (Development Mode). |

## 5. Tipos de teste

Selecionados por PB conforme a funcionalidade — não se força todos os tipos em todos os PBs:

unitário · integração · API · banco de dados · frontend · fluxo ponta a ponta (e2e) · segurança ·
autorização · privacidade · concorrência · idempotência · regressão · usabilidade · recuperação após
falha · serviços externos mockados · performance básica.

## 6. Critérios de entrada

Um PB entra em teste quando: a implementação do escopo está concluída; as dependências estão
concluídas ou mockadas; o ambiente e os dados de teste estão disponíveis; e os testes automatizados
pertinentes foram criados junto com a implementação.

## 7. Critérios de saída

Um PB sai da validação (aprovado) quando: todos os testes obrigatórios do PB passam; todos os seus
critérios de aceitação estão validados; nenhum defeito de severidade alta/bloqueante permanece aberto;
e as evidências estão registradas no `PLANO_EXECUCAO.md`. Uma Sprint é aprovada quando, além do acima
para todos os seus PBs, os testes integrados da Sprint e a regressão das Sprints anteriores passam.

## 8. Gestão de defeitos

- **Severidade:** Bloqueante (impede o fluxo) · Alta (critério de aceitação não atendido) · Média
  (comportamento incorreto sem bloquear) · Baixa (cosmético/menor).
- **Fluxo:** registrar defeito com CT relacionado, passos e evidência → corrigir no escopo do PB →
  reexecutar o CT → só então avançar.
- **Regra de parada:** não iniciar o próximo PB com testes obrigatórios falhando; não encerrar a
  Sprint com defeitos bloqueantes/altos abertos.

## 9. Evidências obrigatórias

Para cada execução relevante, registrar: comando executado, contagem de testes (aprovados/reprovados),
saídas de API (status e corpo sanitizado), estado persistido no banco, capturas de tela quando houver
frontend, migrações verificadas, integrações verificadas, limitações conhecidas e data da validação.
**Nunca** registrar tokens, segredos ou dados pessoais sensíveis nas evidências.

---

## 10. Testes por Sprint e por PB

Convenções:

- **ID de caso:** `CT-PBXX-NN` (teste individual) e `CT-S{N}-INT-NN` (teste integrado da Sprint N).
- **Status:** Não executado | Aprovado | Reprovado | Bloqueado.
- **Automatizável:** Sim | Não | Parcialmente.
- Salvo indicação, o **Status inicial de todos os casos é "Não executado"**, exceto onde há evidência
  real registrada (PB-01).

---

## Sprint 1 — Fundação, autenticação e sala utilizável

### PB-01 — Fundação técnica do produto

#### Objetivo da validação

Comprovar que a base local (frontend Vite, backend FastAPI, PostgreSQL, SQLAlchemy/Alembic) inicia,
conecta ao banco, aplica e reverte a migração inicial e não versiona segredos.

#### Requisitos e critérios cobertos

Critérios 1–4 do PB-01 (iniciar frontend/backend; conexão com Postgres; migração ida/volta; segredos
por variáveis de ambiente não versionadas).

#### Pré-condições

Python 3.11 + venv do backend; Docker (Postgres) para os testes de banco/migração; Node ≥ 18 para o
frontend nativo.

#### Dados de teste

Nenhum dado de domínio; usa endpoints de saúde e a tabela `users` vazia.

#### Casos de teste

##### CT-PB01-01 — Liveness do backend
- **Tipo:** API · **Prioridade:** Alta
- **Cenário:** backend no ar responde à sondagem de vida.
- **Pré-condições:** backend iniciado.
- **Dados de entrada:** `GET /health`.
- **Passos:** chamar `/health`.
- **Resultado esperado:** 200 com `{"status":"ok",...}`.
- **Evidência esperada:** resposta 200 / saída do teste.
- **Critério de aprovação:** status e corpo conforme esperado.
- **Automatizável:** Sim · **Status:** Aprovado (2026-07-13, `pytest`)

##### CT-PB01-02 — Readiness com banco alcançável
- **Tipo:** integração · **Prioridade:** Alta
- **Cenário:** `/health/db` executa `SELECT 1` com banco disponível.
- **Pré-condições:** banco de teste acessível.
- **Dados de entrada:** `GET /health/db`.
- **Passos:** chamar `/health/db`.
- **Resultado esperado:** 200 `{"status":"ok","database":"ok"}`.
- **Evidência esperada:** resposta 200.
- **Critério de aprovação:** conexão confirmada.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-13 — `curl` contra Postgres 16 real → 200)

##### CT-PB01-03 — Readiness com banco indisponível (falha controlada)
- **Tipo:** recuperação após falha / segurança · **Prioridade:** Alta
- **Cenário:** com o banco inacessível, a readiness falha sem vazar detalhes internos.
- **Pré-condições:** sessão de banco forçada a erro (override no teste).
- **Dados de entrada:** `GET /health/db`.
- **Passos:** injetar sessão que lança `OperationalError`; chamar `/health/db`.
- **Resultado esperado:** 503 com `database: "unavailable"`, **sem** stack trace/detalhe de conexão.
- **Evidência esperada:** resposta 503 sanitizada.
- **Critério de aprovação:** 503 e ausência de detalhes sensíveis.
- **Automatizável:** Sim · **Status:** Aprovado (2026-07-13)

##### CT-PB01-04 — Ciclo de migração ida/volta/ida
- **Tipo:** banco de dados · **Prioridade:** Alta
- **Cenário:** a migração `0001_initial` cria e remove `users` de forma reversível.
- **Pré-condições:** Postgres no Compose; venv ativa.
- **Dados de entrada:** `alembic upgrade head` → `downgrade base` → `upgrade head`.
- **Passos:** executar a sequência; inspecionar existência da tabela/índice em cada etapa.
- **Resultado esperado:** tabela `users` e índice `ix_users_spotify_id` criados, removidos e recriados
  sem erro.
- **Evidência esperada:** saída do Alembic sem erros.
- **Critério de aprovação:** ciclo completo sem falha.
- **Automatizável:** Parcialmente · **Status:** Aprovado (2026-07-12/13)

##### CT-PB01-05 — Ausência de segredos versionados
- **Tipo:** segurança · **Prioridade:** Alta
- **Cenário:** `.env` não é rastreado e `.env.example` não contém segredos reais.
- **Pré-condições:** repositório limpo.
- **Dados de entrada:** `git status`, conteúdo de `.env`/`.env.example`.
- **Passos:** verificar que `.env` está ignorado e vazio; conferir `.env.example` sem valores reais.
- **Resultado esperado:** nenhum segredo no controle de versão.
- **Evidência esperada:** `.env` não rastreado (0 bytes); `.env.example` com placeholders.
- **Critério de aprovação:** nada sensível versionado.
- **Automatizável:** Parcialmente · **Status:** Aprovado (2026-07-13)

##### CT-PB01-06 — Frontend nativo conecta a backend e banco *(critério pendente)*
- **Tipo:** frontend / e2e · **Prioridade:** Alta
- **Cenário:** `npm run dev` sobe o Vite e a tela de status mostra Frontend/Backend/Banco = ok.
- **Pré-condições:** Node ≥ 18 instalado (atualmente **ausente** — bloqueio); backend e banco no ar.
- **Dados de entrada:** `http://localhost:5173`.
- **Passos:** `npm install && npm run dev`; abrir a página; observar os três indicadores.
- **Resultado esperado:** três status "ok"; API base correta.
- **Evidência esperada:** captura de tela da página de status.
- **Critério de aprovação:** os três indicadores em "ok".
- **Automatizável:** Parcialmente · **Status:** Aprovado (QA revalidação 2026-07-14 — bloqueio removido: Node v24.18.0/npm 11.16.0; Vite nativo :5173 → 200, backend :8000 → 200, CORS da origem :5173 → 200; DEF-PB01-01 resolvido)

> Observação: `vite build` já foi verificado em container Node 20 (compila, `dist/` gerado). Falta a
> execução **nativa** para encerrar o critério 1 do PB-01.

---

### PB-02 — Autenticação com Spotify

#### Objetivo da validação

Comprovar que o OAuth do Spotify é seguro (proteção por `state`), cria/atualiza usuário e sessão, e que
tokens ficam **apenas** no backend, criptografados, nunca expostos ao frontend ou a logs.

#### Requisitos e critérios cobertos

Critérios 1–5 do PB-02.

#### Pré-condições

App Spotify criado, `redirect_uri` registrada, `SpotifyClient`/`crypto` disponíveis, chave Fernet em
variável de ambiente; cliente Spotify mockado para os testes automatizados.

#### Dados de teste

Usuário Spotify fictício (`spotify_id=demo_user_1`), `state` válido e inválido, code de autorização
mockado, respostas mockadas de troca de token e de `/me`.

#### Casos de teste

##### CT-PB02-01 — Redirecionamento para o consent oficial
- **Tipo:** API · **Prioridade:** Alta · **Cenário:** `GET /auth/login` redireciona ao Spotify com
  `client_id`, `scope`, `redirect_uri` e `state` gerado.
- **Passos:** chamar `/auth/login`; inspecionar o `Location`.
- **Resultado esperado:** 302 para `accounts.spotify.com` com `state` presente e escopos do MVP.
- **Evidência esperada:** header `Location`; `state` guardado no servidor/cookie.
- **Critério de aprovação:** URL de autorização correta e `state` emitido.
- **Automatizável:** Sim · **Status:** Aprovado (QA revalidação 2026-07-13 — /auth/login → 302 com state e escopos)

##### CT-PB02-02 — Callback rejeita `state` ausente/ inválido (CSRF)
- **Tipo:** segurança · **Prioridade:** Alta · **Cenário:** callback com `state` divergente do emitido
  é rejeitado.
- **Passos:** chamar `/auth/callback` com `state` inexistente e com `state` diferente do armazenado.
- **Resultado esperado:** erro (400/401), **sem** criar sessão nem trocar tokens.
- **Evidência esperada:** resposta de erro; ausência de sessão criada.
- **Critério de aprovação:** nenhum acesso concedido sem `state` válido.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-13 — state divergente/ausente → 400, sem sessão)

##### CT-PB02-03 — Autorização válida cria/atualiza usuário e sessão
- **Tipo:** integração · **Prioridade:** Alta · **Cenário:** `state` válido + code → usuário criado (1ª
  vez) ou atualizado (2ª vez) e sessão iniciada.
- **Passos:** callback com `state` válido; repetir para o mesmo `spotify_id`.
- **Resultado esperado:** 1 registro em `users` para o `spotify_id` (sem duplicar); cookie de sessão
  httpOnly definido; `GET /auth/me` retorna o usuário.
- **Evidência esperada:** registro único; `/auth/me` 200.
- **Critério de aprovação:** idempotência de usuário + sessão válida.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-13, Postgres — sem duplicar user; /auth/me OK)

##### CT-PB02-04 — Tokens nunca chegam ao frontend nem a logs
- **Tipo:** privacidade/segurança · **Prioridade:** Alta · **Cenário:** nenhuma resposta HTTP nem log
  contém access/refresh token.
- **Passos:** inspecionar corpos de `/auth/callback`, `/auth/me` e logs após o fluxo.
- **Resultado esperado:** ausência total de tokens no frontend e nos logs.
- **Evidência esperada:** respostas e logs sanitizados.
- **Critério de aprovação:** zero exposição de token.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-13, Postgres — sem tokens em resposta)

##### CT-PB02-05 — Tokens criptografados em repouso
- **Tipo:** segurança · **Prioridade:** Alta · **Cenário:** `spotify_tokens.access_token/refresh_token`
  ficam cifrados no banco.
- **Passos:** ler diretamente o registro em `spotify_tokens`.
- **Resultado esperado:** valores cifrados (não legíveis); descriptografia só via chave em env.
- **Evidência esperada:** valor persistido ≠ token em claro.
- **Critério de aprovação:** conteúdo cifrado em repouso.
- **Automatizável:** Sim · **Status:** Aprovado (QA revalidação 2026-07-13 — cifrado em repouso; DEF-PB02-02 corrigido, sem chave efêmera)

##### CT-PB02-06 — Refresh e reauth necessária
- **Tipo:** serviço externo mockado / recuperação · **Prioridade:** Alta · **Cenário:** access token
  expirado é renovado; se o refresh falhar, marca-se `reauth_required_at` e redireciona-se ao login.
- **Passos:** simular token expirado (refresh OK) e refresh com erro.
- **Resultado esperado:** renovação transparente no 1º caso; no 2º, `reauth_required_at` setado e
  redirecionamento a novo login.
- **Evidência esperada:** estado do token; resposta de reauth.
- **Critério de aprovação:** ambos os caminhos tratados sem crash.
- **Automatizável:** Sim · **Status:** Aprovado (QA revalidação 2026-07-13 — refresh/reauth com comportamento validado, CT-PB02-06a..d)

> **Reentrega Dev 2026-07-13:** refresh bem-sucedido e falho cobertos por testes técnicos; aguarda
> reexecução e atualização de Status pelo QA.

##### CT-PB02-07 — Regressão: saúde e migração continuam OK
- **Tipo:** regressão · **Prioridade:** Média · **Cenário:** após adicionar auth e migrações, PB-01
  continua válido.
- **Passos:** reexecutar CT-PB01-01..05.
- **Resultado esperado:** todos aprovados.
- **Critério de aprovação:** sem regressão.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-13 — 4 testes de saúde verdes; migração reversível)

---

### PB-04 — Criação de sala efêmera

#### Objetivo da validação

Comprovar que apenas usuários autenticados criam salas, com código único, host como primeiro membro e
expiração de 24h.

#### Requisitos e critérios cobertos

Critérios 1–5 do PB-04.

#### Pré-condições

Usuário autenticado (sessão válida); modelo `music_sessions`/`music_session_members` migrado.

#### Dados de teste

Host autenticado `demo_user_1`; relógio de referência para validar expiração.

#### Casos de teste

##### CT-PB04-01 — Criação por usuário autenticado
- **Tipo:** API · **Prioridade:** Alta · **Cenário:** host autenticado cria a sala.
- **Passos:** `POST /rooms` autenticado.
- **Resultado esperado:** 201 com `code` e dados iniciais; host registrado em `music_session_members`.
- **Evidência esperada:** payload + registro persistido.
- **Critério de aprovação:** sala e host criados.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-14, Postgres real — `POST /rooms` → 201 com código e host persistido)

##### CT-PB04-02 — Criação sem autenticação é bloqueada
- **Tipo:** autorização · **Prioridade:** Alta · **Cenário:** requisição sem sessão válida.
- **Passos:** `POST /rooms` sem cookie de sessão.
- **Resultado esperado:** 401; nenhuma sala criada.
- **Critério de aprovação:** acesso negado.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-14 — sem cookie e com cookie inválido → 401; nenhuma sala criada)

##### CT-PB04-03 — Código curto único
- **Tipo:** integração/concorrência · **Prioridade:** Alta · **Cenário:** múltiplas criações não geram
  códigos colidentes.
- **Passos:** criar N salas (inclusive em paralelo); coletar códigos.
- **Resultado esperado:** todos os códigos distintos; `code` com restrição de unicidade.
- **Evidência esperada:** conjunto de códigos sem repetição.
- **Critério de aprovação:** unicidade garantida.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-14, Postgres real — 20 criações concorrentes → 20 códigos distintos; `UNIQUE(code)` no catálogo + retry em colisão)

##### CT-PB04-04 — Host é o primeiro integrante e tem papel host
- **Tipo:** integração · **Prioridade:** Alta · **Cenário:** criador entra como `role=host`.
- **Passos:** criar sala; consultar membros.
- **Resultado esperado:** exatamente 1 membro (host) com papel host.
- **Critério de aprovação:** papel e associação corretos.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-14 — exatamente 1 membro `role=host`; 21/21 salas com vínculo consistente)

##### CT-PB04-05 — Expiração de 24h
- **Tipo:** banco/regra de negócio · **Prioridade:** Alta · **Cenário:** `expires_at ≈ created_at + 24h`.
- **Passos:** criar sala; comparar `expires_at` e `created_at`.
- **Resultado esperado:** diferença de 24h (dentro de tolerância).
- **Critério de aprovação:** janela de expiração correta.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-14 — `expires_at − created_at` = 24h exatas no payload e no banco)

##### CT-PB04-06 — Retorno da API não expõe dados sensíveis
- **Tipo:** privacidade · **Prioridade:** Média · **Cenário:** payload de criação não traz tokens nem
  dados de terceiros.
- **Passos:** inspecionar o corpo de `POST /rooms`.
- **Resultado esperado:** somente dados da sala/host.
- **Critério de aprovação:** sem vazamento.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-14 — payload só com dados públicos da sala/host; sem token, sessão ou dados de terceiros)

---

### PB-05 — Entrada e acompanhamento da sala

#### Objetivo da validação

Comprovar entrada por código sem duplicidade, limite de 5 integrantes, proteção de acesso (403 para
não-membros) e atualização por polling.

#### Requisitos e critérios cobertos

Critérios 1–5 do PB-05.

#### Pré-condições

Sala existente criada por PB-04; usuários autenticados adicionais; sala expirada disponível para teste.

#### Dados de teste

Sala aberta com host; usuários `demo_user_2..6`; um código inexistente; uma sala com `expires_at` no
passado.

#### Casos de teste

##### CT-PB05-01 — Entrada por código válido
- **Tipo:** API · **Prioridade:** Alta · **Cenário:** convidado entra e passa a constar como membro.
- **Passos:** `POST /rooms/{code}/join` autenticado.
- **Resultado esperado:** 200; usuário aparece na lista de membros no próximo `GET /rooms/{code}`.
- **Critério de aprovação:** associação criada e visível.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-15, Postgres real — `POST /rooms/{code}/join` → 200; convidado visível no `GET` seguinte; código aceito em minúsculas)

##### CT-PB05-02 — Código inexistente ou sala expirada rejeitados
- **Tipo:** entrada inválida · **Prioridade:** Alta · **Cenário:** join em código inválido/expirado.
- **Passos:** join com código inexistente; join em sala com `expires_at` passado.
- **Resultado esperado:** 404 (inexistente) e 410/403 (expirada) — sem associação criada.
- **Critério de aprovação:** ambos rejeitados com mensagem apropriada.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-15, Postgres real — inexistente → 404 "Sala não encontrada."; expirada → 410 "Esta sala expirou."; nenhum vínculo criado)

##### CT-PB05-03 — Limite de cinco integrantes
- **Tipo:** limites (máximo) · **Prioridade:** Alta · **Cenário:** o 6º ingresso é barrado.
- **Passos:** encher a sala com 5 membros; tentar o 6º.
- **Resultado esperado:** 5 aceitos; 6º recebe erro (409/403) e não é associado.
- **Evidência esperada:** contagem final = 5.
- **Critério de aprovação:** limite respeitado.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-15, Postgres real — 6º → 409, contagem final 5; concorrência pesada QA: 20 disputantes → 4 entram/16 recusados, total 5; mutante sem `FOR UPDATE` chega a 6, provando que o lock é necessário)

##### CT-PB05-04 — Join duplicado não cria segundo vínculo
- **Tipo:** duplicidade/idempotência · **Prioridade:** Alta · **Cenário:** mesmo usuário faz join 2×.
- **Passos:** join com o mesmo usuário duas vezes.
- **Resultado esperado:** sem duplicar `music_session_members` (PK composta); resposta idempotente.
- **Evidência esperada:** 1 vínculo por usuário.
- **Critério de aprovação:** anti-duplicidade garantida.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-15, Postgres real — join repetido → 200 com 1 vínculo, inclusive com a sala cheia; 10 joins simultâneos do mesmo usuário → todos 200 e 1 único vínculo)

##### CT-PB05-05 — Não-membro recebe 403 ao consultar a sala
- **Tipo:** autorização/privacidade · **Prioridade:** Alta · **Cenário:** usuário externo tenta ler a
  sala pela URL.
- **Passos:** `GET /rooms/{code}` autenticado como não-membro.
- **Resultado esperado:** 403; nenhum dado da sala/membros retornado.
- **Critério de aprovação:** acesso negado sem vazamento.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-15, Postgres real — não-membro → 403; corpo só com `detail`, sem código/id/membros/expiração da sala)

##### CT-PB05-06 — Estado atualizado no polling reflete novos membros
- **Tipo:** integração/e2e · **Prioridade:** Média · **Cenário:** entrada de um membro aparece para os
  demais na próxima leitura.
- **Passos:** membro A consulta; membro B entra; A consulta novamente (3–5s depois).
- **Resultado esperado:** B aparece na 2ª leitura de A.
- **Critério de aprovação:** propagação por polling funciona.
- **Automatizável:** Parcialmente · **Status:** Aprovado (QA 2026-07-15 — API: 1ª leitura 1 membro → B entra → 2ª leitura 2 membros; navegador real (Chromium): intervalos medidos 4002/4000 ms, média 4001 ms, todos dentro de 3–5s)

##### CT-PB05-07 — Estado consistente após recarregar
- **Tipo:** persistência · **Prioridade:** Média · **Cenário:** recarregar a página mantém a lista de
  membros e o estado.
- **Passos:** recarregar `GET /rooms/{code}`.
- **Resultado esperado:** mesma composição e estado persistidos.
- **Critério de aprovação:** consistência mantida.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-15 — 3 leituras consecutivas byte-a-byte idênticas; reload no navegador real mantém a mesma composição de membros)

---

### PB-06 — Contexto e modo de consenso

#### Objetivo da validação

Comprovar que **somente o host** altera contexto e modo, que ocasião/descrição são aceitas de forma
flexível, que o modo é restrito a Democrático/Festa Segura e que a mudança se propaga aos membros.

#### Requisitos e critérios cobertos

Critérios 1–4 do PB-06.

#### Pré-condições

Sala com host e ao menos um membro comum.

#### Dados de teste

Ocasião "festa"; descrição livre; modos válidos e um modo inválido ("qualquer").

#### Casos de teste

##### CT-PB06-01 — Somente o host altera contexto
- **Tipo:** autorização · **Prioridade:** Alta · **Cenário:** host altera; membro comum é barrado.
- **Passos:** `PUT /rooms/{code}/context` como host (OK) e como membro comum (erro).
- **Resultado esperado:** host 200; membro comum 403; contexto inalterado pelo membro.
- **Evidência esperada:** 403 para membro; contexto persistido só pelo host.
- **Critério de aprovação:** apenas host altera.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `432a23c`)

##### CT-PB06-02 — Aceita ocasião, descrição ou ambos
- **Tipo:** regra de negócio · **Prioridade:** Média · **Cenário:** combinações válidas de entrada.
- **Passos:** enviar só ocasião; só descrição; ambos.
- **Resultado esperado:** todas aceitas e persistidas corretamente.
- **Critério de aprovação:** flexibilidade respeitada.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `432a23c`)

##### CT-PB06-03 — Modo inválido é rejeitado
- **Tipo:** entrada inválida · **Prioridade:** Alta · **Cenário:** modo fora do enum permitido.
- **Passos:** `PUT /rooms/{code}/mode` com "qualquer".
- **Resultado esperado:** 422/400; modo não alterado.
- **Critério de aprovação:** só Democrático/Festa Segura aceitos.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `432a23c`)

##### CT-PB06-04 — Alteração visível para os membros no polling
- **Tipo:** integração · **Prioridade:** Média · **Cenário:** membro vê o novo contexto/modo na próxima
  leitura.
- **Passos:** host altera; membro consulta a sala depois.
- **Resultado esperado:** membro recebe contexto/modo atualizados.
- **Critério de aprovação:** propagação correta.
- **Automatizável:** Parcialmente · **Status:** Aprovado (QA 2026-07-16, commit `432a23c`)

##### CT-PB06-05 — Persistência do contexto após recarga
- **Tipo:** persistência · **Prioridade:** Média · **Cenário:** contexto/modo sobrevivem a recarregar.
- **Passos:** definir contexto; recarregar; ler novamente.
- **Resultado esperado:** valores mantidos.
- **Critério de aprovação:** estado durável.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `432a23c`)

---

### PB-08 — Coleta e cache de dados musicais

#### Objetivo da validação

Comprovar coleta de top tracks/artists nos endpoints autorizados, associação por snapshot, reuso de
snapshot fresco, refetch de vencido e sinalização de reauth em falha de token.

#### Requisitos e critérios cobertos

Critérios 1–5 do PB-08.

#### Pré-condições

Usuário autenticado com token válido (mockado); modelo `user_music_snapshots` migrado.

#### Dados de teste

Respostas mockadas de top tracks/artists; snapshot com `fetched_at` recente (<7d) e antigo (>7d);
resposta 429 e falha de refresh mockadas.

#### Casos de teste

##### CT-PB08-01 — Coleta e associação em snapshot
- **Tipo:** integração/serviço externo mockado · **Prioridade:** Alta · **Cenário:** tops coletados e
  gravados por usuário.
- **Passos:** `POST /me/refresh-music-snapshot`; inspecionar `user_music_snapshots`.
- **Resultado esperado:** snapshot com `top_tracks_json`/`top_artists_json` associado ao usuário.
- **Critério de aprovação:** dados persistidos corretamente.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `b662e52`)

##### CT-PB08-02 — Snapshot fresco (<7d) é reutilizado
- **Tipo:** cache/regra de negócio · **Prioridade:** Alta · **Cenário:** com snapshot recente, não há
  nova chamada ao Spotify.
- **Passos:** ter snapshot <7d; solicitar tops.
- **Resultado esperado:** reuso do snapshot; **sem** chamada externa.
- **Evidência esperada:** mock do Spotify não invocado.
- **Critério de aprovação:** cache respeitado.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `b662e52`)

##### CT-PB08-03 — Snapshot vencido (>7d) é refetchado
- **Tipo:** cache · **Prioridade:** Alta · **Cenário:** snapshot antigo é atualizado antes da geração.
- **Passos:** ter snapshot >7d; solicitar tops/geração.
- **Resultado esperado:** nova coleta; `fetched_at` atualizado.
- **Critério de aprovação:** refetch ocorre.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `b662e52`)

##### CT-PB08-04 — Falha de refresh marca reauth necessária
- **Tipo:** recuperação após falha · **Prioridade:** Alta · **Cenário:** refresh falha durante coleta.
- **Passos:** mockar refresh com erro; solicitar tops.
- **Resultado esperado:** operação não crasha; usuário marcado para reautenticação.
- **Critério de aprovação:** reauth sinalizada.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `b662e52`)

##### CT-PB08-05 — Resposta 429 do Spotify é tratada
- **Tipo:** serviço externo mockado · **Prioridade:** Média · **Cenário:** rate limit no Spotify.
- **Passos:** mockar 429; solicitar tops.
- **Resultado esperado:** backoff/retry ou uso de cache; sem crash.
- **Critério de aprovação:** degradação graciosa.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `b662e52`)

##### CT-PB08-06 — Integrante sem dados musicais
- **Tipo:** ausência de dados · **Prioridade:** Média · **Cenário:** tops vazios para um usuário.
- **Passos:** mockar listas vazias.
- **Resultado esperado:** snapshot vazio válido; sistema segue e registra limitação.
- **Critério de aprovação:** sem crash; limitação registrada.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-16, commit `b662e52`)

### Testes integrados da Sprint 1

#### Objetivo do incremento
Um grupo autentica-se, cria/entra em uma sala, define contexto/modo e tem os dados musicais prontos.

#### PBs cobertos
PB-01, PB-02, PB-04, PB-05, PB-06, PB-08.

#### Fluxos integrados
- Login Spotify → `GET /auth/me` → `POST /rooms` (host) → `POST /rooms/{code}/join` (convidado) →
  `PUT /rooms/{code}/context` + `/mode` (host) → `POST /me/refresh-music-snapshot` (cada membro).

#### Casos de integração
##### CT-S1-INT-01 — Fluxo feliz completo da Sprint 1
- **Tipo:** e2e · **Prioridade:** Alta · **Cenário:** dois usuários chegam a "sala pronta para o motor".
- **Resultado esperado:** ambos autenticados; sala com 2 membros; contexto/modo definidos; 2 snapshots.
- **Critério de aprovação:** estado final consistente e demonstrável.
- **Automatizável:** Parcialmente · **Status:** Não executado

##### CT-S1-INT-02 — Autenticação alimenta host e coleta
- **Tipo:** integração · **Prioridade:** Alta · **Cenário:** o mesmo usuário autenticado vira host
  (PB-04) e coleta dados (PB-08) com o token da sessão.
- **Critério de aprovação:** identidade única e consistente entre PBs.
- **Automatizável:** Sim · **Status:** Não executado

#### Casos de regressão
Nenhum (primeira Sprint). Reexecutar CT-PB01-01..05 após cada PB para garantir a fundação.

#### Casos de falha
##### CT-S1-INT-03 — Erros combinados não corrompem estado
- **Tipo:** falha · **Prioridade:** Média · **Cenário:** código inválido + 6º membro + token expirado
  em sequência.
- **Resultado esperado:** cada erro tratado isoladamente; sala permanece consistente (≤5 membros).
- **Critério de aprovação:** nenhum estado inconsistente.
- **Automatizável:** Sim · **Status:** Não executado

#### Verificações de segurança
Token nunca no frontend/logs; 403 para não-membro; só host cria/altera; sem segredos versionados.

#### Verificações de persistência
Sala, membros, contexto/modo e snapshots sobrevivem a recarga/polling e a reinício do backend.

#### Verificações de experiência do usuário
Tela de sala mostra membros entrando; contexto/modo refletidos; feedback claro em erros de entrada.

#### Critérios de aprovação da Sprint
Todos os PBs da Sprint aprovados; CT-S1-INT-01..03 aprovados; nenhum defeito alto/bloqueante aberto.

#### Evidências exigidas
`pytest` verde; respostas de API; capturas das telas Login/Home/Room; snapshots persistidos; log
sanitizado.

#### Resultado da Sprint
Pendente (Sprint em andamento — apenas PB-01 parcialmente validado até 2026-07-13).

---

## Sprint 2 — Núcleo do motor de negociação (PNE)

### PB-09 — Modelagem de gosto e compatibilidade

#### Objetivo da validação
Comprovar perfis individuais e compatibilidade normalizada, reprodutível, sem I/O, tratando listas
vazias e grupo de 1.

#### Requisitos e critérios cobertos
Critérios 1–4 do PB-09.

#### Pré-condições
`engine/taste.py` implementado; entradas fixas de snapshot.

#### Dados de teste
Perfis com interseção total, parcial e nula; um usuário; usuário com listas vazias.

#### Casos de teste
##### CT-PB09-01 — Compatibilidade com valores esperados
- **Tipo:** unitário · **Prioridade:** Alta · **Cenário:** duas listas com interseção conhecida.
- **Resultado esperado:** valor de similaridade igual ao calculado à mão (ex.: Jaccard), em [0,1].
- **Critério de aprovação:** igualdade com o valor esperado.
- **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB09-02 — Grupo de um integrante
- **Tipo:** limites · **Prioridade:** Alta · **Cenário:** só um usuário.
- **Resultado esperado:** compatibilidade definida (ex.: 1.0 ou convenção documentada), sem erro.
- **Critério de aprovação:** caso unitário tratado.
- **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB09-03 — Listas vazias / sem interseção
- **Tipo:** ausência de dados · **Prioridade:** Alta · **Cenário:** um perfil vazio ou grupos disjuntos.
- **Resultado esperado:** 0% sem crash; sem divisão por zero.
- **Critério de aprovação:** robustez a vazio.
- **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB09-04 — Determinismo e ausência de rede
- **Tipo:** unitário/segurança · **Prioridade:** Alta · **Cenário:** mesma entrada → mesma saída, sem I/O.
- **Resultado esperado:** repetições idênticas; nenhuma chamada de rede/banco.
- **Critério de aprovação:** determinístico e puro.
- **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

### PB-10 — Geração do conjunto de candidatas

#### Objetivo da validação
Comprovar pool com contribuição de vários integrantes, sem duplicatas, com origem registrada e descarte
motivado.

#### Requisitos e critérios cobertos
Critérios 1–4 do PB-10.

#### Pré-condições
Perfis do PB-09; função de montagem do pool implementada.

#### Dados de teste
Membros com faixas sobrepostas (para testar dedupe); candidata sem id suficiente; membro sem dados.

#### Casos de teste
##### CT-PB10-01 — Contribuição de diferentes integrantes
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** pool inclui faixas de mais de um
  membro quando há dados. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB10-02 — Sem duplicatas
- **Tipo:** duplicidade · **Prioridade:** Alta · **Cenário:** faixas repetidas entre membros.
- **Resultado esperado:** cada faixa aparece uma única vez. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB10-03 — Origem registrada
- **Tipo:** unitário · **Prioridade:** Média · **Resultado esperado:** cada candidata tem `source`.
- **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB10-04 — Descarte motivado de candidata sem identificação
- **Tipo:** entrada inválida · **Prioridade:** Alta · **Cenário:** faixa sem dados p/ busca posterior.
- **Resultado esperado:** descartada com `discard_reason`. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB10-05 — Membro sem dados não quebra o pool
- **Tipo:** ausência de dados · **Prioridade:** Média · **Resultado esperado:** pool montado com os
  demais; limitação registrada. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

### PB-11 — Pontuação individual e coletiva

#### Objetivo da validação
Comprovar as fórmulas de score individual e de grupo com pesos centralizados, determinísticas e com
valores esperados.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-11.

#### Pré-condições
`engine/scoring.py` e `engine/weights.py` implementados (pesos do README §8).

#### Dados de teste
Faixa com afinidades conhecidas por usuário; grupo com scores {10,10,1} para testar min/avg/coverage.

#### Casos de teste
##### CT-PB11-01 — Score individual com valor esperado
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** `user_track_score` igual ao
  cálculo manual pela fórmula ponderada. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB11-02 — Score de grupo considera média, mínimo, cobertura, contexto, diversidade
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** componentes refletidos no valor;
  `min_user_score` presente. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB11-03 — Pesos centralizados e ajustáveis
- **Tipo:** unitário/configuração · **Prioridade:** Média · **Cenário:** alterar um peso muda o score de
  forma previsível. · **Resultado esperado:** mudança proporcional; pesos vêm de `weights.py`.
- **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB11-04 — Determinismo
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** mesma entrada/config → mesmo
  resultado. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

### PB-12 — Rejeição, justiça e modos de consenso

#### Objetivo da validação
Comprovar penalidade de rejeição, least misery, cobertura, representação mínima e a diferença entre os
modos Democrático e Festa Segura.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-12.

#### Pré-condições
`engine/fairness.py` implementado; scores do PB-11.

#### Dados de teste
Faixa popular com veto forte de um membro; grupo com scores {10,10,1}; entradas com/sem Vibe Check.

#### Casos de teste
##### CT-PB12-01 — Veto forte derruba faixa popular
- **Tipo:** regra de negócio · **Prioridade:** Alta · **Cenário:** faixa agrada à maioria mas tem
  rejeição forte de um membro. · **Resultado esperado:** score final penalizado abaixo do limiar de
  seleção. · **Critério de aprovação:** rejeição prevalece sobre a média. · **Automatizável:** Sim ·
  **Status:** Aprovado (2026-07-16)

##### CT-PB12-02 — Least misery vs média simples
- **Tipo:** unitário · **Prioridade:** Alta · **Cenário:** {10,10,1} — média esconde a insatisfação de C.
- **Resultado esperado:** métrica de menor satisfação capturada; seleção evita esmagar C. ·
  **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB12-03 — Métricas de justiça calculadas
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** satisfação média, menor
  satisfação, cobertura e fairness score presentes e coerentes. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB12-04 — Modo Democrático (pesos iguais)
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** todos os integrantes com o mesmo
  peso. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB12-05 — Modo Festa Segura (familiaridade/baixa rejeição)
- **Tipo:** unitário · **Prioridade:** Alta · **Cenário:** comparar seleção nos dois modos para a mesma
  entrada. · **Resultado esperado:** Festa Segura favorece faixas conhecidas e de baixa rejeição. ·
  **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB12-06 — Elevação do integrante menos representado
- **Tipo:** regra de negócio · **Prioridade:** Alta · **Cenário:** um membro ficaria muito abaixo.
- **Resultado esperado:** troca marginal eleva o mínimo sem derrubar demais o grupo. ·
  **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB12-07 — Vibe Check como entrada opcional (não bloqueante)
- **Tipo:** integração · **Prioridade:** Média · **Cenário:** com e sem `derived_preferences_json`.
- **Resultado esperado:** funciona sem Vibe Check; com ele, ajusta pesos (ex.: baixa `sadness_tolerance`
  penaliza tags tristes). · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18) — sem
  respostas, o ranking é idêntico ao anterior (não bloqueante); com `valence` baixa, faixas `sad` são
  penalizadas; sinal limitado a 20% não inverte consenso forte. Cobertura:
  `backend/tests/test_s3_vibe_scoring_qa.py` e `test_s3_integration_qa.py::test_ct_s3_int_03_*`.

### PB-13 — Controle e histórico da geração

#### Objetivo da validação
Comprovar Generation Lock (409 concorrente), transições de estado e retry pós-falha, com registro
independente por geração.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-13.

#### Pré-condições
Rotas de sala (Sprint 1) e motor (PB-11) disponíveis; modelo `playlist_runs` migrado.

#### Dados de teste
Sala com host; duas solicitações concorrentes; execução forçada a falhar.

#### Casos de teste
##### CT-PB13-01 — Primeira geração cria execução running
- **Tipo:** API · **Prioridade:** Alta · **Resultado esperado:** `playlist_run` com `status=running` e
  `session.status=generating`. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB13-02 — Geração concorrente retorna 409
- **Tipo:** concorrência/idempotência · **Prioridade:** Alta · **Cenário:** segunda solicitação enquanto
  a primeira está em andamento. · **Resultado esperado:** 409; nenhuma segunda execução criada. ·
  **Evidência esperada:** apenas 1 run ativo. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB13-03 — Conclusão e falha atualizam estado
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** sucesso → `completed`; erro →
  `failed` com `error_message`. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-16)

##### CT-PB13-04 — Retry controlado após falha
- **Tipo:** recuperação · **Prioridade:** Alta · **Cenário:** após `failed`, host solicita nova geração.
- **Resultado esperado:** nova execução permitida; registro independente. · **Automatizável:** Sim ·
  **Status:** Aprovado (2026-07-16)

##### CT-PB13-05 — Só host dispara geração
- **Tipo:** autorização · **Prioridade:** Alta · **Resultado esperado:** membro comum recebe 403. ·
  **Automatizável:** Sim · **Status:** Não executado

##### CT-PB13-06 — Cliques repetidos não duplicam playlists
- **Tipo:** idempotência · **Prioridade:** Alta · **Cenário:** múltiplos cliques rápidos em "Gerar".
- **Resultado esperado:** uma execução por vez; sem playlists duplicadas. · **Automatizável:** Sim ·
  **Status:** Não executado

### Testes integrados da Sprint 2

#### Objetivo do incremento
O motor determinístico produz, para entradas fixas, uma seleção reproduzível com justiça e execução
controlada, sem chamadas externas.

#### PBs cobertos
PB-09, PB-10, PB-11, PB-12, PB-13.

#### Fluxos integrados
Snapshots (PB-08) → modelagem (PB-09) → pool (PB-10) → scores (PB-11) → rejeição/justiça (PB-12) →
execução controlada (PB-13).

#### Casos de integração
##### CT-S2-INT-01 — Pipeline determinístico ponta a ponta (offline)
- **Tipo:** integração · **Prioridade:** Alta · **Cenário:** entrada fixa de membros/snapshots.
- **Resultado esperado:** mesma seleção final e mesmos scores a cada execução; sem I/O. ·
  **Automatizável:** Sim · **Status:** Não executado

##### CT-S2-INT-02 — Justiça observável no resultado do motor
- **Tipo:** integração · **Prioridade:** Alta · **Cenário:** grupo divergente + veto forte.
- **Resultado esperado:** menor satisfação protegida; veto derruba faixa; métricas coerentes. ·
  **Automatizável:** Sim · **Status:** Não executado

#### Casos de regressão
##### CT-S2-INT-03 — Regressão da Sprint 1
- **Tipo:** regressão · **Prioridade:** Alta · **Resultado esperado:** auth, salas, contexto e snapshots
  continuam aprovados. · **Automatizável:** Sim · **Status:** Não executado

#### Casos de falha
##### CT-S2-INT-04 — Falha na geração deixa estado consistente
- **Tipo:** recuperação · **Prioridade:** Alta · **Cenário:** erro no meio do pipeline.
- **Resultado esperado:** run `failed`, `session` liberada para novo retry; sem dados órfãos. ·
  **Automatizável:** Sim · **Status:** Não executado

#### Verificações de segurança
Motor sem rede/banco; só host gera; só membro consulta.

#### Verificações de persistência
`playlist_runs` reflete estado real; retry cria registro independente.

#### Verificações de experiência do usuário
Feedback de "gerando…"; bloqueio de clique duplo; mensagem clara em falha.

#### Critérios de aprovação da Sprint
PBs 09–13 aprovados; CT-S2-INT-01..04 aprovados; regressão da Sprint 1 verde.

#### Evidências exigidas
`pytest` do motor com valores esperados; 409 sob concorrência; estados de `playlist_runs`.

#### Resultado da Sprint
Pendente.

---

## Sprint 3 — Fluxo principal ponta a ponta

### PB-14 — Correspondência das músicas no Spotify

#### Objetivo da validação
Comprovar track matching robusto, respeito ao mercado do host e descarte motivado, com identificador
Spotify associado a cada música válida.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-14.

#### Pré-condições
Motor (PB-11/PB-12) e execução (PB-13); token do host (PB-02); `SpotifyClient` mockado.

#### Dados de teste
Candidatas com variantes ("remastered", "live", "acoustic", "sped up"); faixa indisponível no mercado;
resultados ambíguos com popularidades distintas.

#### Casos de teste
##### CT-PB14-01 — Normalização de variantes de título/artista
- **Tipo:** unitário · **Prioridade:** Alta · **Cenário:** buscar "Song - Remastered 2011".
- **Resultado esperado:** casa com a faixa correta; variante tratada. · **Automatizável:** Sim ·
  **Status:** Não executado

##### CT-PB14-02 — Confiança mínima de match
- **Tipo:** regra de negócio · **Prioridade:** Alta · **Cenário:** melhor resultado abaixo do limiar.
- **Resultado esperado:** descartada com `discard_reason=low_match`; `match_confidence` registrado. ·
  **Automatizável:** Sim · **Status:** Não executado

##### CT-PB14-03 — Desempate por popularidade
- **Tipo:** unitário · **Prioridade:** Média · **Cenário:** dois matches plausíveis.
- **Resultado esperado:** escolhe o mais popular. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB14-04 — Faixa indisponível no mercado é descartada
- **Tipo:** serviço externo mockado · **Prioridade:** Alta · **Cenário:** indisponível no market do host.
- **Resultado esperado:** descartada com `discard_reason=unavailable_in_market`; não entra na seleção.
- **Automatizável:** Sim · **Status:** Não executado

##### CT-PB14-05 — Search sem resultado não quebra a geração
- **Tipo:** recuperação · **Prioridade:** Alta · **Cenário:** candidata não encontrada.
- **Resultado esperado:** descartada com `discard_reason=not_found`; geração prossegue. ·
  **Automatizável:** Sim · **Status:** Não executado

### PB-15 — Criação da playlist no Spotify

#### Objetivo da validação
Comprovar a criação de playlist privada real (20–30 faixas, cap de 2/artista) na conta do host, com
id/URL persistidos e link devolvido.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-15.

#### Pré-condições
Músicas correspondidas (PB-14); `SpotifyClient` mockado para unit e conta real para o e2e.

#### Casos de teste
##### CT-PB15-01 — Cap de 2 músicas por artista
- **Tipo:** limites · **Prioridade:** Alta · **Cenário:** artista com 3+ candidatas fortes.
- **Resultado esperado:** no máximo 2 faixas desse artista na playlist. · **Automatizável:** Sim ·
  **Status:** Não executado

##### CT-PB15-02 — Playlist final de 20 a 30 músicas
- **Tipo:** limites · **Prioridade:** Alta · **Resultado esperado:** contagem final ∈ [20,30]. ·
  **Automatizável:** Sim · **Status:** Não executado

##### CT-PB15-03 — Playlist privada criada na conta do host (e2e real)
- **Tipo:** e2e · **Prioridade:** Alta · **Cenário:** geração com conta Spotify real da demo.
- **Resultado esperado:** playlist **privada** aparece de fato na conta do host; `spotify_playlist_id`
  e URL salvos na execução; host recebe o link. · **Evidência esperada:** URL da playlist; captura no
  Spotify. · **Automatizável:** Não · **Status:** Não executado

##### CT-PB15-04 — Falha parcial não deixa dados inconsistentes
- **Tipo:** recuperação/persistência · **Prioridade:** Alta · **Cenário:** erro após criar a playlist e
  antes de salvar todas as faixas. · **Resultado esperado:** estado coerente (run reflete o real; sem
  faixas órfãs). · **Automatizável:** Parcialmente · **Status:** Não executado

##### CT-PB15-05 — Host sozinho gera a playlist
- **Tipo:** integração/regressão · **Prioridade:** Alta · **Cenário:** sala com um único integrante,
  sendo ele o host, e snapshot com candidatas suficientes.
- **Resultado esperado:** `POST /rooms/{code}/generate` conclui sem exigir segundo membro, cria playlist
  privada com 20–30 faixas, persiste ID/URL e libera a sala para nova geração.
- **Automatizável:** Sim (Spotify mockado) · **Status:** Não executado

### PB-16 — Resultado e explicabilidade

#### Objetivo da validação
Comprovar a tela de resultado com link, métricas, representação por integrante e justificativas
legíveis, **sem** expor dados sensíveis de terceiros, restrita a membros.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-16.

#### Pré-condições
Execução concluída (PB-13/PB-14).

#### Dados de teste
Execução com representação desigual entre membros; faixa incluída por veto de outro membro (para testar
privacidade da explicação).

#### Casos de teste
##### CT-PB16-01 — Link da playlist presente
- **Tipo:** API/frontend · **Prioridade:** Alta · **Resultado esperado:** resultado traz a URL da
  playlist. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-17)

##### CT-PB16-02 — Compatibilidade e fairness exibidos
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** compatibility e fairness da
  execução apresentados. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-17)

##### CT-PB16-03 — Representação por integrante
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** percentual/indicador por membro
  compreensível. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-17)

##### CT-PB16-04 — Justificativa por música
- **Tipo:** integração · **Prioridade:** Média · **Resultado esperado:** cada faixa tem `reason`
  resumido. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-17)

##### CT-PB16-05 — Privacidade: não expor rejeições de terceiros
- **Tipo:** privacidade · **Prioridade:** Alta · **Cenário:** explicação de faixa afetada por veto.
- **Resultado esperado:** texto agregado ("alguns membros indicaram baixa tolerância a X"), **sem**
  nomear quem rejeitou. · **Critério de aprovação:** nenhuma exposição individual. · **Automatizável:**
  Sim · **Status:** Aprovado (2026-07-17)

##### CT-PB16-06 — Acesso restrito a membros
- **Tipo:** autorização · **Prioridade:** Alta · **Resultado esperado:** não-membro recebe 403 em
  `GET /rooms/{code}/result`. · **Automatizável:** Sim · **Status:** Aprovado (2026-07-17)

### PB-17 — Interpretação estruturada do contexto

#### Objetivo da validação
Comprovar que o LLM retorna JSON válido conforme schema, que respostas inválidas/ausentes acionam
fallback determinístico, que dados brutos não são enviados ao LLM e que os critérios estruturados
são efetivamente consumidos pelo motor sem permitir que o LLM escolha músicas diretamente.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-17, integração com o componente de contexto do score coletivo do PB-11 e
Definition of Done (funcionalidade integrada ao incremento principal).

#### Pré-condições
`LLMClient` mockável; schema de contexto definido.

#### Dados de teste
Descrição "festa muito alegre" e "estudo relaxante"; resposta do LLM válida, JSON inválido e timeout.

#### Reabertura de 2026-07-17

`INC-PB17-CTX-01` foi observado em teste real em grupo: ocasião/descrição diferentes produziram a
mesma base prática de seleção. A rodada histórica aprovou schema/fallback/privacidade, mas declarou
`CT-PB17-05` “não aplicável”. Essa decisão foi superada pela expectativa já escrita neste plano e
por `CT-S3-INT-02`. Os casos antes aprovados entram como regressão; `CT-PB17-05` volta a ser portão.

#### Casos de teste
##### CT-PB17-01 — Saída válida segue o schema
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** JSON com ocasião, humor,
  energia, tags +/-, avoid. · **Automatizável:** Sim · **Status:** Aprovado (regressão QA 2026-07-18)

##### CT-PB17-02 — JSON inválido aciona fallback sem interromper
- **Tipo:** recuperação · **Prioridade:** Alta · **Cenário:** LLM devolve JSON malformado.
- **Resultado esperado:** rejeitado; geração segue com consenso/afinidade/popularidade. ·
  **Automatizável:** Sim · **Status:** Aprovado (regressão QA 2026-07-18)

##### CT-PB17-03 — LLM indisponível → fallback determinístico
- **Tipo:** recuperação · **Prioridade:** Alta · **Cenário:** timeout/erro do LLM.
- **Resultado esperado:** pipeline continua sem IA. · **Automatizável:** Sim · **Status:** Aprovado (regressão QA 2026-07-18)

##### CT-PB17-04 — Privacidade: dados brutos não vão ao LLM
- **Tipo:** privacidade · **Prioridade:** Alta · **Cenário:** inspecionar o payload enviado.
- **Resultado esperado:** só contexto do host / dados agregados; **sem** top tracks/artists brutos. ·
  **Automatizável:** Sim · **Status:** Aprovado (regressão QA 2026-07-18)

##### CT-PB17-05 — Contexto muda candidatas/tags
- **Tipo:** integração · **Prioridade:** Média · **Cenário:** "festa" vs "estudo".
- **Passos:** manter os mesmos perfis, snapshots, modo e candidatas; variar apenas ocasião/descrição;
  executar interpretação, scoring, seleção e criação do conjunto final.
- **Resultado esperado:** tags positivas/negativas diferem; cada candidata recebe `context_score`
  derivado dos critérios; ranking ou seleção final muda de forma coerente e reproduzível. Não basta
  persistir JSON diferente se as mesmas músicas mantiverem os mesmos scores contextuais.
- **Critério de aprovação:** pelo menos uma diferença material de score/ordem/seleção explicada pelo
  contexto, preservando determinismo e sem decisão direta do LLM.
- **Automatizável:** Sim · **Status:** Aprovado (QA independente 2026-07-18, rodada 3) — pool misto
  realista + perfil uniforme mostram que "festa" e "estudo" mudam o topo de forma coerente e
  reprodutível nos dois modos; prova por mutação (contexto neutro → rankings idênticos) confirma que a
  diferença é causada pelo contexto; efeito também confirmado pelo fallback determinístico

##### CT-PB17-06 — LLM não decide a playlist
- **Tipo:** regra de negócio · **Prioridade:** Alta · **Resultado esperado:** seleção final vem do
  motor; LLM só fornece critérios. · **Automatizável:** Sim · **Status:** Aprovado (regressão QA 2026-07-18)

### PB-07 — Vibe Check opcional

#### Objetivo da validação
Comprovar questionário de 3–5 perguntas, pulável, com preferências derivadas em [0,1] por usuário/sala,
atualizáveis a cada nova resposta.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-07.

#### Pré-condições
Sala com membro autenticado; rotas de Vibe Check.

#### Dados de teste
Conjunto de 3–5 perguntas; respostas do usuário; segunda resposta do mesmo usuário.

#### Casos de teste
##### CT-PB07-01 — Quantidade de perguntas dentro do limite
- **Tipo:** regra de negócio · **Prioridade:** Média · **Resultado esperado:** entre 3 e 5 perguntas. ·
  **Automatizável:** Sim · **Status:** Aprovado

##### CT-PB07-02 — Pular não bloqueia a geração
- **Tipo:** e2e · **Prioridade:** Alta · **Cenário:** usuário pula o Vibe Check.
- **Resultado esperado:** geração prossegue normalmente. · **Automatizável:** Sim · **Status:** Aprovado

##### CT-PB07-03 — Respostas por usuário e sala
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** `vibe_check_answers` associado a
  usuário+sala. · **Automatizável:** Sim · **Status:** Aprovado

##### CT-PB07-04 — Preferências derivadas em [0,1]
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** todos os valores normalizados. ·
  **Automatizável:** Sim · **Status:** Aprovado

##### CT-PB07-05 — Nova resposta atualiza a participação
- **Tipo:** idempotência/atualização · **Prioridade:** Média · **Cenário:** usuário responde de novo.
- **Resultado esperado:** derivadas atualizadas para a próxima geração; sem duplicar histórico
  indevidamente. · **Automatizável:** Sim · **Status:** Aprovado

##### CT-PB07-06 — Não-membro não responde
- **Tipo:** autorização · **Prioridade:** Média · **Resultado esperado:** 403 ao responder em sala alheia.
- **Automatizável:** Sim · **Status:** Aprovado

### Testes integrados da Sprint 3

#### Objetivo do incremento
O fluxo principal do MVP funciona de ponta a ponta, produzindo uma playlist real explicável.

#### PBs cobertos
PB-07, PB-14, PB-15, PB-16, PB-17.

#### Fluxos integrados
Sala pronta → contexto interpretado (PB-17/fallback) → (Vibe Check opcional) → motor → seleção →
criação de playlist real (PB-14) → resultado explicável (PB-16).

#### Casos de integração
##### CT-S3-INT-01 — E2E completo com playlist real
- **Tipo:** e2e · **Prioridade:** Alta · **Cenário:** grupo real conclui do login ao resultado.
- **Resultado esperado:** playlist privada criada; tela de resultado com métricas e representação. ·
  **Automatizável:** Não · **Status:** Aprovado parcialmente (QA 2026-07-18) — parte automatizável
  (Spotify mockado) verde: `POST /generate` com 2 membros → 202/completed, playlist registrada no run,
  ≥20 faixas `matched`, `GET /result` → 200; não-membro → 403. **Demonstração e2e real com conta
  Spotify permanece pendente** (limite de 5 usuários / Development Mode).

##### CT-S3-INT-02 — Contexto do LLM consumido pelo motor e pela busca
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** tags do contexto influenciam
  candidatas/scores; playlist reflete a ocasião. · **Automatizável:** Parcialmente · **Status:** Parte
  automatizável Aprovada (QA independente 2026-07-18) — contexto consumido pelo motor comprovado nos
  dois modos, com prova por mutação (PB-17) e confirmado ponta a ponta via API no ciclo integrado
  (mesmos snapshots/modo; só a ocasião muda → ordem final das faixas muda). Demonstração e2e real da
  playlist fica para o fechamento (CT-S3-INT-01).

##### CT-S3-INT-03 — Vibe Check influencia o ranking
- **Tipo:** integração · **Prioridade:** Média · **Cenário:** baixa `sadness_tolerance`.
- **Resultado esperado:** faixas com tag `sad` penalizadas na seleção. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA rodada 2, 2026-07-18) — `DEF-S3-INT-03-01` corrigido no commit `088597b`.
  `execute_generation` agora consulta `vibe_check_answers` e mistura um `vibe_score` (motor puro
  `engine/vibe_scoring.py`) ao `group_score` com influência limitada `0.20`; `valence` baixa penaliza
  faixas `sad`. Verificado de forma independente: reprodutor QA intocado
  (`test_s3_integration_qa.py`) agora passa e sondagem adversarial nova
  (`test_s3_vibe_scoring_qa.py`, 6 casos) confirma limite de influência (não inverte consenso forte),
  preservação do "pular" e monotonicidade de `valence`. Regressão: 217 passed / 6 skipped / 0 failed.

#### Casos de regressão
##### CT-S3-INT-04 — Regressão das Sprints 1 e 2
- **Tipo:** regressão · **Prioridade:** Alta · **Resultado esperado:** auth/salas/motor/execução
  continuam aprovados. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18) — suíte
  completa `APP_ENV=test pytest` (excluindo o novo arquivo integrado) → **201 passed / 6 skipped /
  0 failed**; sem regressão em Sprints 1–3.

#### Casos de falha
##### CT-S3-INT-05 — Falha de serviço externo não invalida o fluxo
- **Tipo:** recuperação · **Prioridade:** Alta · **Cenário:** LLM indisponível + algumas faixas não
  encontradas. · **Resultado esperado:** fallback de contexto + descartes motivados; playlist ainda é
  criada com faixas válidas. · **Automatizável:** Parcialmente · **Status:** Aprovado (QA 2026-07-18)
  — LLM indisponível (`httpx.post` erro) + 5 buscas sem resultado → geração conclui 202/completed,
  contexto de fallback persistido, 5 faixas descartadas com motivo `No results`, ≥20 `matched`.

#### Verificações de segurança
Token do host nunca no frontend; explicações sem dados sensíveis de terceiros; só host gera; só membro
vê o resultado.

#### Verificações de persistência
`playlist_runs` + `playlist_run_tracks` refletem a playlist real; estado consistente após recarga.

#### Verificações de experiência do usuário
Usuário percorre o fluxo do início ao fim; resultado compreensível; ocasião reflete no conteúdo.

#### Critérios de aprovação da Sprint
PBs 07, 14, 15, 16, 17 aprovados; CT-S3-INT-01..05 aprovados; regressão das Sprints 1–2 verde.

#### Evidências exigidas
URL da playlist criada; payload de resultado; logs sanitizados; `pytest` verde; capturas das telas.

#### Resultado da Sprint
**Casos automatizáveis Aprovados (QA rodada 2, 2026-07-18); falta só a demo e2e real.** Rodada 1
reprovou por `DEF-S3-INT-03-01` (Alta); o Dev corrigiu no commit `088597b` (Vibe Check integrado ao
ranking com influência limitada 0.20) e a rodada 2 revalidou de forma independente: CT-S3-INT-01
(parcial), INT-02, **INT-03 (agora Aprovado)**, INT-04 (regressão **217 passed / 6 skipped / 0
failed**) e INT-05 **Aprovados**. `DEF-S3-INT-03-01` **fechado**; nenhum defeito Alta/bloqueante
aberto. **Encerramento diferido:** a demonstração e2e **real** da playlist (`CT-S3-INT-01`) está com
**validação pendente, a ser feita futuramente devido a limitações de API** (contas Premium /
Development Mode). Assinatura atual: `SPRINT 3 EM VALIDAÇÃO — EVIDÊNCIA E2E REAL PENDENTE`; a
assinatura `SPRINT 3 CONCLUÍDA` só sai após essa demonstração. Relatório:
[`docs/relatorios-testes/SPRINT-03-INTEGRADO.md`](../relatorios-testes/SPRINT-03-INTEGRADO.md).

---

## Sprint 4 — Complementos e consolidação de qualidade

### PB-03 — Logout e remoção de dados

#### Objetivo da validação
Comprovar invalidação de sessão, negação de acesso após logout e remoção/anonimização de dados sem
expor terceiros.

#### Requisitos e critérios cobertos
Critérios 1–4 do PB-03.

#### Pré-condições
Usuário autenticado com dados (sessão, tokens, participação em sala).

#### Casos de teste
##### CT-PB03-01 — Logout invalida a sessão
- **Tipo:** segurança · **Prioridade:** Alta · **Resultado esperado:** `POST /auth/logout` invalida
  `app_session`. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB03-02 — Rotas autenticadas negam acesso após logout
- **Tipo:** autorização · **Prioridade:** Alta · **Resultado esperado:** `GET /auth/me` e rotas de sala
  → 401/403 após logout. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB03-03 — Remoção exclui/anonimiza dados pessoais
- **Tipo:** privacidade · **Prioridade:** Alta · **Resultado esperado:** dados previstos removidos/
  anonimizados; tokens apagados. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB03-04 — Remoção não afeta terceiros
- **Tipo:** privacidade/integridade · **Prioridade:** Alta · **Cenário:** usuário em sala com outros.
- **Resultado esperado:** dados dos demais membros intactos; sem exposição de tokens. ·
  **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

### PB-18 — Enriquecimento de contexto com Last.fm

#### Objetivo da validação
Comprovar a cascata (faixa → artista → gêneros Spotify → consenso), cache com confiança e resiliência a
erro/ausência.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-18.

#### Pré-condições
`LastFmClient` mockável; `track_context_cache` migrado.

#### Casos de teste
##### CT-PB18-01 — Tags da faixa preferidas às do artista
- **Tipo:** regra de negócio · **Prioridade:** Alta · **Resultado esperado:** usa tags da faixa quando
  existem; confiança maior. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB18-02 — Cascata quando faltam tags
- **Tipo:** recuperação · **Prioridade:** Alta · **Cenário:** sem tags de faixa/artista.
- **Resultado esperado:** usa gêneros Spotify e demais sinais; confiança menor registrada. ·
  **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB18-03 — Fonte e confiança registradas
- **Tipo:** unitário · **Prioridade:** Média · **Resultado esperado:** cada resultado tem `source` e
  `confidence`. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB18-04 — Cache válido é reutilizado
- **Tipo:** cache · **Prioridade:** Média · **Cenário:** consulta repetida da mesma faixa.
- **Resultado esperado:** sem nova chamada externa enquanto o cache é válido. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB18-05 — Erro/vazio do Last.fm não interrompe a geração
- **Tipo:** recuperação · **Prioridade:** Alta · **Resultado esperado:** cascata assume; geração segue.
- **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

### PB-19 — Sequenciamento da experiência musical

#### Objetivo da validação
Comprovar a ordenação: abertura forte, sem 2 do mesmo artista seguidas, risco no meio e cap respeitado.

#### Requisitos e critérios cobertos
Critérios 1–4 do PB-19.

#### Pré-condições
`engine/sequencer.py`; seleção final do PB-14.

#### Casos de teste
##### CT-PB19-01 — Sem duas faixas do mesmo artista consecutivas
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** nenhuma adjacência do mesmo
  artista. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB19-02 — Abertura com alta aceitação
- **Tipo:** unitário · **Prioridade:** Média · **Resultado esperado:** 1ª faixa entre as de maior
  aceitação. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB19-03 — Faixas de maior risco no meio
- **Tipo:** unitário · **Prioridade:** Média · **Resultado esperado:** posições de risco na região
  intermediária. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB19-04 — Cap de 2/artista preservado após sequenciar
- **Tipo:** limites · **Prioridade:** Alta · **Resultado esperado:** ordenação não viola o cap. ·
  **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB19-05 — Entrada mínima (poucas faixas / artista único)
- **Tipo:** limites/robustez · **Prioridade:** Média · **Cenário:** seleção pequena ou dominada por 1
  artista. · **Resultado esperado:** degradação graciosa sem erro; melhor esforço nas regras. ·
  **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

### PB-20 — Feedback pós-playlist

#### Objetivo da validação
Comprovar coleta de feedback por faixa e geral, associada à execução correta, com bloqueio de não-membro
e aviso de uso futuro.

#### Requisitos e critérios cobertos
Critérios 1–5 do PB-20.

#### Pré-condições
Execução concluída (PB-16); modelos de feedback migrados.

#### Casos de teste
##### CT-PB20-01 — Feedback por faixa
- **Tipo:** API · **Prioridade:** Média · **Resultado esperado:** like/dislike/more_like_this/never_again
  registrados. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB20-02 — Feedback geral (representação/satisfação)
- **Tipo:** API · **Prioridade:** Média · **Resultado esperado:** notas persistidas. · **Automatizável:**
  Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB20-03 — Associação à execução correta
- **Tipo:** integridade · **Prioridade:** Alta · **Resultado esperado:** feedback vinculado ao
  `playlist_run` e usuário certos. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB20-04 — Não-membro não registra feedback
- **Tipo:** autorização · **Prioridade:** Alta · **Cenário:** usuário fora da sala da execução.
- **Resultado esperado:** 403; nada registrado. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB20-05 — Aviso de uso futuro explícito
- **Tipo:** usabilidade · **Prioridade:** Baixa · **Resultado esperado:** UI informa que o feedback é
  para evoluções futuras. · **Automatizável:** Parcialmente · **Status:** Aprovado (QA 2026-07-18)

> **Qualidade, robustez e documentação (antigo PB-20)** deixou de ser um PB e virou a **Definition of
> Done**, verificada em **todos** os PBs (não só na Sprint 4):
> - cobertura do motor (scoring, justiça, rejeição, duplicidade, cap por artista);
> - cobertura da API (autorização 403, entrada duplicada, Generation Lock 409);
> - clientes externos mockados (token expirado, 429, JSON inválido, busca sem resultado);
> - nenhum token/segredo em testes ou logs;
> - README e roteiro de demonstração atualizados.

### Testes integrados da Sprint 4

#### Objetivo do incremento
Experiência complementada (logout/remoção, Last.fm, sequenciamento, feedback) e qualidade consolidada.

#### PBs cobertos
PB-03, PB-18, PB-19, PB-20.

#### Fluxos integrados
Fluxo principal + enriquecimento de contexto (Last.fm) + sequenciamento da playlist + coleta de
feedback; logout/remoção como fluxo transversal de privacidade.

#### Casos de integração
##### CT-S4-INT-01 — Last.fm melhora o contexto sem quebrar o fluxo
- **Tipo:** integração · **Prioridade:** Média · **Resultado esperado:** tags enriquecem o scoring;
  falha do Last.fm cai na cascata. · **Automatizável:** Parcialmente · **Status:** Aprovado (QA 2026-07-18) — geração conclui com Last.fm mockado (cache `source=lastfm_track_tags`, conf. 0.95) e também quando o Last.fm falha (cascata para gêneros/consenso)

##### CT-S4-INT-02 — Sequenciador aplicado à playlist real
- **Tipo:** e2e · **Prioridade:** Média · **Resultado esperado:** ordem final coerente na playlist
  criada. · **Automatizável:** Não · **Status:** Pendente (diferido) — demonstração e2e real com conta Spotify; lógica validada no PB-19 (unit/integração mockada)

##### CT-S4-INT-03 — Feedback associado à execução real
- **Tipo:** integração · **Prioridade:** Média · **Resultado esperado:** feedback persistido e vinculado
  corretamente. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18) — após geração real, feedback por faixa e geral persistidos e vinculados ao run/usuário corretos

#### Casos de regressão
##### CT-S4-INT-04 — Regressão completa das Sprints 1–3
- **Tipo:** regressão · **Prioridade:** Alta · **Resultado esperado:** fluxo principal e motor continuam
  aprovados. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18) — suíte completa 292 passed / 6 skipped / 0 failed

#### Casos de falha
##### CT-S4-INT-05 — Logout durante fluxo ativo
- **Tipo:** segurança/recuperação · **Prioridade:** Alta · **Cenário:** usuário faz logout no meio do
  uso. · **Resultado esperado:** sessão invalidada; ações seguintes negadas; sem estado inconsistente. ·
  **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18) — logout remove a sessão; result/me/feedback com o mesmo token → 401; nada persiste

#### Verificações de segurança
Logout invalida sessão; remoção não expõe terceiros; nenhum segredo em logs/testes.

#### Verificações de persistência
Cache do Last.fm consistente; feedback vinculado; remoção efetiva e irreversível conforme política.

#### Verificações de experiência do usuário
Playlist bem sequenciada; feedback simples; aviso de uso futuro; logout/remoção claros.

#### Critérios de aprovação da Sprint
PBs 03, 18, 19, 20 aprovados; CT-S4-INT-01..05 aprovados; regressão das Sprints 1–3 verde; suíte
completa verde; documentação e roteiro de demo prontos.

#### Evidências exigidas
`pytest` completo; varredura de segredos; README/roteiro; capturas do fluxo; cache/feedback persistidos.

#### Resultado da Sprint
**EM VALIDAÇÃO — e2e real diferida (QA 2026-07-18).** PBs individuais (PB-03/18/19/20) VALIDADOS; a
parte automatizável do ciclo integrado passou: CT-S4-INT-01 (Last.fm + cascata), INT-03 (feedback no
run real), INT-04 (regressão 292 passed / 6 skipped / 0 failed) e INT-05 (logout mid-flow) Aprovados.
**CT-S4-INT-02** (sequenciador na playlist real) fica diferido por exigir conta Spotify. Assinatura
`SPRINT 4 CONCLUÍDA` só após a demo e2e real. Relatório:
[`docs/relatorios-testes/SPRINT-04-INTEGRADO.md`](../relatorios-testes/SPRINT-04-INTEGRADO.md).

---

## Sprint 5 — Expansão pós-MVP

### PB-21 — Modo Descoberta

#### Objetivo da validação
Comprovar que o modo opcional favorece novidade/diversidade apenas quando habilitado, preserva os
mecanismos de rejeição e representação e explica seu efeito no resultado.

#### Requisitos e critérios cobertos
Critérios 1–4 do PB-21.

#### Pré-condições
PB-11, PB-12 e PB-16 validados; `DISCOVERY_MODE_ENABLED` controlável no ambiente de teste.

#### Casos de teste
##### CT-PB21-01 — Feature flag desligada
- **Tipo:** configuração/API · **Prioridade:** Alta · **Resultado esperado:** “Descoberta” não é
  anunciado pela API/UI e tentativa direta de seleção é rejeitada sem alterar a sala. ·
  **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB21-02 — Feature flag ligada
- **Tipo:** API/integração · **Prioridade:** Alta · **Resultado esperado:** modo aparece entre os
  disponíveis, pode ser selecionado pelo host e é persistido. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB21-03 — Novidade e diversidade recebem peso superior
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** peso de novidade supera o
  Democrático e candidatas novas/diversas ganham preferência verificável. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB21-04 — Rejeição e representação preservadas
- **Tipo:** unitário/regressão · **Prioridade:** Alta · **Resultado esperado:** veto forte ainda
  penaliza e a elevação do integrante menos representado continua aplicada. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB21-05 — Explicação no resultado
- **Tipo:** integração · **Prioridade:** Média · **Resultado esperado:** explicação persistida informa
  que o modo favoreceu descoberta, novidade e diversidade. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB21-06 — Seletor segue os modos anunciados pelo servidor
- **Tipo:** frontend/usabilidade · **Prioridade:** Média · **Resultado esperado:** UI não mantém lista
  divergente e descreve o propósito do modo Descoberta. · **Automatizável:** Parcialmente ·
  **Status:** Aprovado (QA 2026-07-18)

---

### PB-22 — Agrupamento de perfis musicais

#### Objetivo da validação
Comprovar que perfis temporários autorizados são agrupados de forma determinística, que a ausência
de evidência suficiente é explícita e que os clusters ficam disponíveis ao motor sem antecipar o
ranqueamento de músicas-ponte.

#### Requisitos e critérios cobertos
Critérios 1–4 do PB-22.

#### Pré-condições
PB-09 validado; snapshots musicais temporários já convertidos em `UserTasteProfile`.

#### Casos de teste
##### CT-PB22-01 — Somente sinais musicais temporários autorizados
- **Tipo:** unitário/privacidade · **Prioridade:** Alta · **Resultado esperado:** agrupamento consome
  somente faixas, artistas e gêneros extraídos de `UserTasteProfile`; o resultado não replica esses
  dados brutos nem requer banco ou rede. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB22-02 — Evidência insuficiente explícita
- **Tipo:** unitário/limites · **Prioridade:** Alta · **Resultado esperado:** menos de três perfis,
  perfil esparso ou ausência de qualquer par semelhante retorna `insufficient_evidence`, sem criar
  subgrupos artificiais. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB22-03 — Agrupamento determinístico
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** a mesma coleção de perfis produz
  os mesmos pares, membros e IDs de cluster independentemente da ordem de entrada. ·
  **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB22-04 — Grupo homogêneo sem falsa divisão
- **Tipo:** unitário/negócio · **Prioridade:** Alta · **Resultado esperado:** perfis conectados pela
  afinidade formam `single_group`, sem subgrupos distintos inventados. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB22-05 — Clusters disponíveis ao motor
- **Tipo:** integração de motor · **Prioridade:** Alta · **Resultado esperado:** candidatas ranqueadas
  recebem IDs transitórios dos clusters de seus integrantes de origem, sem alterar seus dados brutos
  ou aplicar ainda a regra de músicas-ponte. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB22-06 — Configuração e identidade inválidas
- **Tipo:** unitário/robustez · **Prioridade:** Média · **Resultado esperado:** limiar fora de 0..1 e
  `user_id` duplicado são rejeitados explicitamente. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

---

### PB-23 — Identificação de músicas-ponte

#### Objetivo da validação
Comprovar que o motor identifica e marca candidatas com boa aceitação em múltiplos subgrupos, mantém
os modos existentes intactos quando o recurso está desligado e indica as faixas-ponte no resultado.

#### Requisitos e critérios cobertos
Critérios 1–4 do PB-23.

#### Pré-condições
PB-11 e PB-22 validados; agrupamento no estado `clustered`; flag do recurso controlável no teste.

#### Casos de teste
##### CT-PB23-01 — Boa aceitação em múltiplos subgrupos
- **Tipo:** unitário/motor · **Prioridade:** Alta · **Resultado esperado:** candidata cuja média de
  afinidade atinge o limiar em pelo menos dois clusters recebe avaliação positiva, score de ponte e
  IDs dos clusters aceitos. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB23-02 — Afinidade restrita a um subgrupo não forma ponte
- **Tipo:** unitário/negócio · **Prioridade:** Alta · **Resultado esperado:** candidata aceita por um
  único cluster permanece sem marcação de ponte. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB23-03 — Marcação durante o ranqueamento
- **Tipo:** integração de motor · **Prioridade:** Alta · **Resultado esperado:** com a flag ligada e
  subgrupos distintos, `_rank_candidates` anexa `is_bridge`, `bridge_score` e clusters aceitos às
  candidatas correspondentes. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB23-04 — Recurso desligado preserva modos existentes
- **Tipo:** configuração/regressão · **Prioridade:** Alta · **Resultado esperado:** flag falsa por
  padrão; nos modos Democrático, Festa Segura e Descoberta, ordem e scores históricos não mudam e
  nenhuma candidata é marcada. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB23-05 — Marcação persistida e indicada no resultado
- **Tipo:** integração/API/frontend · **Prioridade:** Alta · **Resultado esperado:** matching persiste
  `is_bridge`; resposta da sala identifica cada faixa-ponte e apresenta justificativa agregada; UI
  exibe a sinalização sem revelar preferências individuais. · **Automatizável:** Parcialmente ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB23-06 — Ausência de subgrupos e configuração inválida
- **Tipo:** unitário/robustez · **Prioridade:** Média · **Resultado esperado:** agrupamento ausente,
  insuficiente ou único não produz pontes; limiar fora de 0..1 é rejeitado; resultado permanece
  determinístico sob reordenação dos perfis. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

---

### PB-24 — Balanceamento entre subgrupos

#### Objetivo da validação
Comprovar que a seleção opcional limita a predominância de um subgrupo quando existem alternativas,
sem promover vetos nem desfazer a justiça, e explica quando o balanceamento alterou a ordem.

#### Requisitos e critérios cobertos
Critérios 1–4 do PB-24.

#### Pré-condições
PB-12, PB-16, PB-22 e PB-23 validados; agrupamento `clustered`; flags controláveis no teste.

#### Casos de teste
##### CT-PB24-01 — Limite de predominância com alternativas suficientes
- **Tipo:** unitário/motor · **Prioridade:** Alta · **Resultado esperado:** no prefixo alvo, nenhum
  cluster excede `SUBGROUP_MAX_SHARE` quando o pool seguro oferece representantes suficientes;
  subgrupos são intercalados deterministicamente. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB24-02 — Melhor esforço quando faltam representantes
- **Tipo:** unitário/limites · **Prioridade:** Alta · **Resultado esperado:** seleção mantém tamanho e
  conjunto de candidatas sem falhar; só ultrapassa o limite quando não existem alternativas seguras.
  · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB24-03 — Rejeição e justiça preservadas
- **Tipo:** unitário/regressão · **Prioridade:** Alta · **Resultado esperado:** balanceamento ocorre
  depois de `evaluate_candidate_fairness`/`elevate_least_represented`, não promove candidatas com veto
  e não altera scores nem o conjunto já selecionado pela justiça. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB24-04 — Funcionalidade opcional e configurável
- **Tipo:** configuração/regressão · **Prioridade:** Alta · **Resultado esperado:** flag falsa por
  padrão; desligada, preserva exatamente os três modos existentes; ligada, respeita o limite entre
  0,5 e 1 configurado. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

##### CT-PB24-05 — Aplicação persistida e explicada
- **Tipo:** integração/API · **Prioridade:** Alta · **Resultado esperado:** quando a ordem é alterada,
  o run persiste `subgroup_balancing_applied=true` e a explicação agregada informa o balanceamento;
  quando não aplicado, a explicação não aparece. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-PB24-06 — Estados sem subgrupos, entradas inválidas e determinismo
- **Tipo:** unitário/robustez · **Prioridade:** Média · **Resultado esperado:** clustering ausente,
  insuficiente ou único mantém a ordem; tamanho/limite inválidos são rejeitados; mesma entrada produz
  mesma saída e metadados. · **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18)

### Testes integrados da Sprint 5

#### Objetivo do incremento
Os quatro recursos pós-MVP (Modo Descoberta, agrupamento, faixas-ponte e balanceamento) são opt-in por
feature flag. A validação integrada comprova que **compõem** numa geração real quando ligados e ficam
**inertes** quando desligados, sem regredir o MVP. Casos definidos pelo QA no fechamento da Sprint 5.

#### PBs cobertos
PB-21, PB-22, PB-23, PB-24.

##### CT-S5-INT-01 — Recursos pós-MVP compõem com todas as flags ligadas
- **Tipo:** integração/e2e · **Prioridade:** Alta · **Cenário:** dois subgrupos reais (pop/rock), modo
  Descoberta e as três flags ligadas. · **Resultado esperado:** geração conclui; a candidata comum a
  todos os subgrupos é marcada `is_bridge`; `subgroup_balancing_applied` persistido; o resultado traz
  as explicações de Descoberta e de faixa-ponte. · **Automatizável:** Parcialmente (Spotify mockado;
  e2e real diferido) · **Status:** Aprovado (QA 2026-07-18)

##### CT-S5-INT-02 — Flags desligadas preservam o comportamento do MVP
- **Tipo:** configuração/regressão · **Prioridade:** Alta · **Resultado esperado:** com as flags no
  padrão (off), nenhuma faixa é marcada como ponte, `subgroup_balancing_applied=false` e nenhuma
  explicação pós-MVP aparece; a geração conclui normalmente. · **Automatizável:** Sim ·
  **Status:** Aprovado (QA 2026-07-18)

##### CT-S5-INT-03 — Regressão completa das Sprints 1–4
- **Tipo:** regressão · **Prioridade:** Alta · **Resultado esperado:** toda a suíte continua verde. ·
  **Automatizável:** Sim · **Status:** Aprovado (QA 2026-07-18 — 381 passed / 6 skipped / 0 failed)

#### Resultado da Sprint
**EM VALIDAÇÃO — parte automatizável aprovada (QA 2026-07-18).** Os quatro PBs (PB-21..24) estão
`VALIDADO` e o ciclo integrado automatizável passou (CT-S5-INT-01..03). Como recurso pós-MVP e opt-in,
não há demonstração e2e real obrigatória distinta das já diferidas nas Sprints 3–4; a assinatura formal
`SPRINT 5 CONCLUÍDA` fica condicionada às demonstrações reais pendentes do incremento. Relatório:
[`docs/relatorios-testes/SPRINT-05-INTEGRADO.md`](../relatorios-testes/SPRINT-05-INTEGRADO.md).

---

## Sprint 6 — Estabilização e evolução contextual

Os casos abaixo consolidam o contrato de QA do handoff
[`SPRINT_06_IMPLEMENTACAO.md`](SPRINT_06_IMPLEMENTACAO.md). Evidências do implementador não alteram
o status inicial: cada caso permanece `Não executado` até o QA independente registrar o resultado.

### PB-25 — Resiliência e eficiência da integração Spotify

#### Objetivo da validação
Comprovar reuso de IDs nativos e interrupção correta em rate limit, sem falsos descartes.

##### CT-PB25-01 — Candidata nativa não usa Search
- **Tipo:** integração/mock · **Prioridade:** Alta · **Resultado esperado:** ID/URI válidos produzem
  match com confiança 1,0 e zero chamadas a Search. · **Automatizável:** Sim · **Status:** Aprovado

##### CT-PB25-02 — Candidata externa continua usando matching
- **Tipo:** regressão · **Prioridade:** Alta · **Resultado esperado:** fonte externa usa Search,
  normalização e limiar de confiança. · **Automatizável:** Sim · **Status:** Aprovado

##### CT-PB25-03 — Primeiro 429 interrompe o lote
- **Tipo:** rate limit · **Prioridade:** Alta · **Resultado esperado:** nenhuma chamada posterior;
  `Retry-After` preservado e itens restantes não viram descartes. · **Automatizável:** Sim ·
  **Status:** Aprovado

##### CT-PB25-04 — Falha libera a sala para retry
- **Tipo:** API/recuperação · **Prioridade:** Alta · **Resultado esperado:** 429 sanitizado, run
  `failed`, sala `open` e nova tentativa permitida. · **Automatizável:** Sim · **Status:** Aprovado

##### CT-PB25-05 — Erro isolado permanece por candidata
- **Tipo:** regressão · **Prioridade:** Média · **Resultado esperado:** not found/low match de uma
  faixa não interrompe o lote. · **Automatizável:** Sim · **Status:** Aprovado

### PB-26 — Pool contextual híbrido

#### Objetivo da validação
Comprovar proveniência, aderência a intenções específicas, composição híbrida e fallback seguro.

##### CT-PB26-01 — Descoberta por tag e similaridade
- **Tipo:** integração/mock · **Prioridade:** Alta · **Resultado esperado:** tags e sementes geram
  candidatas deduplicadas com origem correta. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB26-02 — Intenção específica tem prioridade
- **Tipo:** regra de negócio · **Prioridade:** Alta · **Cenário:** `festa punk rock pesada`. ·
  **Resultado esperado:** punk/rock afetam oferta e score antes de tags genéricas. ·
  **Automatizável:** Sim · **Status:** Não executado

##### CT-PB26-03 — Similar não herda metadados da semente
- **Tipo:** privacidade/correção · **Prioridade:** Alta · **Resultado esperado:** cada descoberta é
  enriquecida com seus próprios sinais; falha cai no fallback. · **Automatizável:** Sim ·
  **Status:** Não executado

##### CT-PB26-04 — Composição preserva âncoras e vetos
- **Tipo:** motor · **Prioridade:** Alta · **Resultado esperado:** participação contextual configurada,
  piso de Tops e nenhuma promoção de veto. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB26-05 — Last.fm ausente preserva comportamento anterior
- **Tipo:** recuperação/regressão · **Prioridade:** Alta · **Resultado esperado:** geração baseada
  em Tops continua determinística. · **Automatizável:** Sim · **Status:** Não executado

### PB-27 — Acompanhamento compartilhado da geração

##### CT-PB27-01 — Progresso persistido é monotônico
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** estágios reais e percentual
  nunca retrocedem. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB27-02 — Todos os membros veem a mesma execução
- **Tipo:** API/polling · **Prioridade:** Alta · **Resultado esperado:** host e membro recebem o mesmo
  `run_id`, estado e progresso. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB27-03 — Somente host inicia ou repete
- **Tipo:** autorização · **Prioridade:** Alta · **Resultado esperado:** membro observa, mas recebe
  403 ao gerar. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB27-04 — Erro é sanitizado e volta ao lobby
- **Tipo:** recuperação/frontend · **Prioridade:** Alta · **Resultado esperado:** ambos observam a
  falha sem stack/token e a sala volta ao estado utilizável. · **Automatizável:** Parcialmente ·
  **Status:** Não executado

##### CT-PB27-05 — Migração reversível
- **Tipo:** banco · **Prioridade:** Média · **Resultado esperado:** `0017` faz upgrade/downgrade sem
  perder colunas históricas. · **Automatizável:** Parcialmente · **Status:** Não executado

### PB-28 — Conformidade visual do Login/Landing

##### CT-PB28-01 — Conformidade com design oficial
- **Tipo:** visual · **Prioridade:** Alta · **Resultado esperado:** hierarquia, tokens e breakpoints
  coerentes com `01-login-landing.png`. · **Automatizável:** Parcialmente · **Status:** Não executado

##### CT-PB28-02 — OAuth e duplo clique
- **Tipo:** frontend/regressão · **Prioridade:** Alta · **Resultado esperado:** CTA abre `/auth/login`
  uma vez e mostra carregamento. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB28-03 — Acessibilidade e erro
- **Tipo:** acessibilidade · **Prioridade:** Alta · **Resultado esperado:** foco visível, semântica,
  `alert` e recuperação do erro. · **Automatizável:** Parcialmente · **Status:** Não executado

##### CT-PB28-04 — Responsividade e movimento reduzido
- **Tipo:** frontend · **Prioridade:** Média · **Resultado esperado:** sem overflow nos breakpoints e
  respeito a `prefers-reduced-motion`. · **Automatizável:** Parcialmente · **Status:** Não executado

### PB-29 — Estado compartilhado e privado do Vibe Check

##### CT-PB29-01 — Estados e totais sem respostas
- **Tipo:** privacidade/API · **Prioridade:** Alta · **Resultado esperado:** somente estado por membro
  e totais agregados; nenhum valor privado. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB29-02 — Pular é ausência neutra
- **Tipo:** motor/integração · **Prioridade:** Alta · **Resultado esperado:** `skipped` usa valores
  nulos e não influencia ranking. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB29-03 — Usuário edita somente o próprio registro
- **Tipo:** autorização/privacidade · **Prioridade:** Alta · **Resultado esperado:** GET privado e
  upserts isolados por membro. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB29-04 — Resposta substitui pulo e vice-versa
- **Tipo:** idempotência · **Prioridade:** Alta · **Resultado esperado:** transições atualizam uma
  única linha e o resumo coletivo. · **Automatizável:** Sim · **Status:** Não executado

##### CT-PB29-05 — Migração e histórico
- **Tipo:** banco · **Prioridade:** Média · **Resultado esperado:** `0018` reversível; registros antigos
  recebem estado compatível. · **Automatizável:** Parcialmente · **Status:** Não executado

### Testes integrados da Sprint 6

##### CT-S6-INT-01 — Geração compartilhada com contexto específico
- **Tipo:** integração/e2e · **Prioridade:** Alta · **Resultado esperado:** dois membros observam
  progresso e resultado; contexto específico altera o pool; somente host gera. ·
  **Automatizável:** Parcialmente · **Status:** Não executado

##### CT-S6-INT-02 — Falhas externas preservam privacidade e retry
- **Tipo:** recuperação · **Prioridade:** Alta · **Resultado esperado:** Last.fm/Ollama falham aberto;
  Spotify 429 interrompe e libera retry; payloads continuam sanitizados. · **Automatizável:** Sim ·
  **Status:** Não executado

##### CT-S6-INT-03 — Regressão completa e frontend
- **Tipo:** regressão · **Prioridade:** Alta · **Resultado esperado:** suíte completa, migrações e
  build verdes; Login/Room/Result inspecionados. · **Automatizável:** Parcialmente ·
  **Status:** Não executado

#### Resultado da Sprint
Pendente. Implementação técnica registrada; QA ainda não emitiu veredito dos PBs 25–29.

---

## Sprint 7 — Biblioteca musical ampliada e eficiente

### PB-30 — Autorização e inventário de playlists

#### Objetivo da validação
Comprovar consentimento mínimo, paginação completa e respeito às playlists realmente acessíveis.

##### CT-PB30-01 — Novo escopo e reconsentimento
- **Tipo:** OAuth/segurança · **Prioridade:** Alta · **Resultado esperado:** solicita
  `playlist-read-private`; token antigo sem escopo recebe reauth acionável, sem loop. ·
  **Automatizável:** Sim · **Status:** Aprovado — revalidado em 2026-07-31; escopos privado e
  colaborativo, detecção do token antigo e limpeza após callback passaram.

##### CT-PB30-02 — Inventário pagina todas as playlists
- **Tipo:** cliente/mock · **Prioridade:** Alta · **Resultado esperado:** segue `next`/offset até o fim,
  com limite de 50 e sem duplicar IDs. · **Automatizável:** Sim · **Status:** Aprovado — revalidado
  em 2026-07-31; paginação de inventário e itens passou com transporte Spotify mockado.

##### CT-PB30-03 — Somente conteúdo elegível segue para sync
- **Tipo:** autorização · **Prioridade:** Alta · **Resultado esperado:** própria/colaborativa acessível
  entra; seguida sem itens/403 é ignorada com motivo. · **Automatizável:** Sim · **Status:** Aprovado
  — revalidado em 2026-07-31; OAuth e serviço exigem `playlist-read-collaborative`, enquanto seguida
  sem acesso continua sendo ignorada com motivo. `DEF-PB30-01` revalidado.

##### CT-PB30-04 — Inventário mínimo e privado
- **Tipo:** persistência/privacidade · **Prioridade:** Alta · **Resultado esperado:** ID, acesso,
  total e `snapshot_id`; nenhum token, imagem ou descrição desnecessária. · **Automatizável:** Sim ·
  **Status:** Aprovado — revalidado em 2026-07-31; `items.total` é a fonte principal,
  `tracks.total` funciona como fallback e somente metadados mínimos são persistidos.
  `DEF-PB30-02` revalidado.

##### CT-PB30-05 — 401/403/429 diferenciados
- **Tipo:** recuperação · **Prioridade:** Alta · **Resultado esperado:** reauth, inacessível e rate
  limit produzem estados sanitizados distintos. · **Automatizável:** Sim · **Status:** Aprovado —
  revalidado em 2026-07-31; os três estados e `Retry-After` foram comprovados com mocks.

### PB-31 — Biblioteca musical limitada a 500 faixas

##### CT-PB31-01 — Tops ocupam as primeiras vagas
- **Tipo:** regra de negócio · **Prioridade:** Alta · **Resultado esperado:** até 150 Tops únicos das
  três faixas temporais; artistas não contam no cap. · **Automatizável:** Sim · **Status:** Aprovado
  — 2026-07-31; 150 Tops ocuparam as primeiras posições e 1.000 artistas não consumiram vagas.

##### CT-PB31-02 — Limite absoluto 500
- **Tipo:** fronteira/banco · **Prioridade:** Alta · **Cenários:** 0, 499, 500, 501 e milhares de
  entradas. · **Resultado esperado:** contagem persistida sempre `<=500`. · **Automatizável:** Sim ·
  **Status:** Aprovado — 2026-07-31; fronteiras 0/499/500/501/2.000 persistiram no máximo 500.

##### CT-PB31-03 — Dedupe preserva proveniência
- **Tipo:** duplicidade · **Prioridade:** Alta · **Resultado esperado:** uma vaga por ID, com todas as
  origens/ranks referenciadas. · **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31; Tops em
  duas faixas e duas playlists produziram uma faixa com quatro origens/ranks.

##### CT-PB31-04 — Preenchimento distribuído entre playlists
- **Tipo:** justiça/determinismo · **Prioridade:** Alta · **Resultado esperado:** round-robin estável;
  uma playlist longa não elimina todas as demais. · **Automatizável:** Sim · **Status:** Aprovado —
  2026-07-31; permutação de entrada foi estável e playlist 2×100 permaneceu representada.

##### CT-PB31-05 — Metadados mínimos e remoção
- **Tipo:** privacidade · **Prioridade:** Alta · **Resultado esperado:** sem payload bruto; exclusão
  da conta apaga inventário, biblioteca e sinais. · **Automatizável:** Sim · **Status:** Aprovado —
  2026-07-31; payload privado não foi persistido e exclusão preservou o outro usuário.

##### CT-PB31-06 — Migração reversível e unicidade
- **Tipo:** banco · **Prioridade:** Alta · **Resultado esperado:** upgrade/downgrade/upgrade; uma linha
  por usuário/faixa mesmo sob duplicidade. · **Automatizável:** Parcialmente · **Status:** Aprovado —
  2026-07-31; ciclo reversível, unicidade, checks e rollback atômico comprovados.

### PB-32 — Sincronização incremental e resiliente

##### CT-PB32-01 — Cache fresco faz zero chamada Spotify
- **Tipo:** cache · **Prioridade:** Alta · **Resultado esperado:** biblioteca <7 dias retornada sem
  inventário, itens ou Top externo. · **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31;
  mock adversarial confirmou zero chamadas externas com cache fresco.

##### CT-PB32-02 — `snapshot_id` evita refetch de itens
- **Tipo:** cache incremental · **Prioridade:** Alta · **Resultado esperado:** playlist inalterada não
  chama `/items`; apenas alteradas são paginadas. · **Automatizável:** Sim · **Status:** Aprovado —
  2026-07-31; apenas o `snapshot_id` alterado acionou download.

##### CT-PB32-03 — Sem N+1 por faixa
- **Tipo:** performance/mock · **Prioridade:** Alta · **Cenário:** 500 itens. · **Resultado esperado:**
  somente inventário, páginas de Tops/itens e zero `GET /tracks/{id}` ou Search. ·
  **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31; páginas de 50 e concorrência externa 1
  comprovadas, sem busca individual.

##### CT-PB32-04 — 429 e quota preservam cache pronto
- **Tipo:** recuperação · **Prioridade:** Alta · **Resultado esperado:** respeita `Retry-After`,
  distingue `QUOTA_EXCEEDED`, não promove parcial e serve stale. · **Automatizável:** Sim ·
  **Status:** Aprovado — 2026-07-31; QA adicionou falha 429 na segunda playlist e confirmou que a
  primeira página baixada não substituiu o cache pronto.

##### CT-PB32-05 — Sincronizações concorrentes convergem
- **Tipo:** concorrência · **Prioridade:** Alta · **Resultado esperado:** sem HTTP 500/duplicidade;
  biblioteca final única e pronta. Deve reproduzir e fechar `DEF-PB08-01`. · **Automatizável:** Sim
  com PostgreSQL · **Status:** Aprovado — revalidação 2026-07-31; sessões independentes convergiram,
  locks não vazam entre event loops e advisory lock PostgreSQL é adquirido/liberado por usuário.

##### CT-PB32-06 — Falha inicial não apaga Tops
- **Tipo:** recuperação · **Prioridade:** Alta · **Resultado esperado:** sem biblioteca anterior,
  erro acionável; snapshot PB-08 permanece intacto. · **Automatizável:** Sim · **Status:** Aprovado —
  2026-07-31; 429 inicial preservou os três snapshots Top e não criou biblioteca parcial.

### PB-33 — Perfil ponderado e seleção limitada de candidatas

##### CT-PB33-01 — Pesos default por origem
- **Tipo:** motor · **Prioridade:** Alta · **Resultado esperado:** `1.00/0.85/0.65/0.45/0.35`
  centralizados e sensíveis no score. · **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31;
  constantes e sensibilidade verificadas no motor.

##### CT-PB33-02 — Múltiplas origens combinam sem duplicar
- **Tipo:** motor/dedupe · **Prioridade:** Alta · **Resultado esperado:** uma candidata, evidências
  combinadas, peso final `<=1`. · **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31;
  origens preservadas, candidata única e teto comprovado.

##### CT-PB33-03 — Cap de 250 candidatas por pessoa
- **Tipo:** limite · **Prioridade:** Alta · **Cenários:** bibliotecas 0, 50, 250 e 500. ·
  **Resultado esperado:** nunca mais de 250; alvo Top/playlist e preenchimento ocioso respeitados. ·
  **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31; limites 0/50/250/500 e redistribuição
  150/100 aprovados.

##### CT-PB33-04 — Biblioteca grande não domina a pequena
- **Tipo:** justiça · **Prioridade:** Alta · **Cenário:** membro A com 500, B com 50. ·
  **Resultado esperado:** contribuição/coverage por pessoa mantém pesos iguais; A não ganha 10x voz. ·
  **Automatizável:** Sim · **Status:** Aprovado — revalidação 2026-07-31; bibliotecas 500×50 agora
  somam o mesmo orçamento de voz 1 por pessoa, preservando pesos relativos internos.

##### CT-PB33-05 — Playlist não equivale a Top no perfil
- **Tipo:** compatibilidade/regressão · **Prioridade:** Alta · **Resultado esperado:** faixa ocasional
  tem afinidade menor e não dilui compatibilidade como conjunto binário bruto. ·
  **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31; playlist 0,45 ficou abaixo de Top 1,00
  e a compatibilidade ponderada permaneceu simétrica.

##### CT-PB33-06 — Determinismo e pureza
- **Tipo:** unitário · **Prioridade:** Alta · **Resultado esperado:** permutações equivalentes geram
  o mesmo resultado; zero rede/banco. · **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31;
  permutações/contexto estáveis e módulo sem dependência de rede ou banco.

### PB-34 — Integração e observabilidade da biblioteca ampliada

##### CT-PB34-01 — Status da biblioteca é sanitizado
- **Tipo:** API/privacidade · **Prioridade:** Alta · **Resultado esperado:** estado, 0..500, idade,
  stale/warning e totais agregados do próprio usuário; sem lista privada. · **Automatizável:** Sim ·
  **Status:** Aprovado — 2026-07-31; payload fechado e sem IDs de playlist/faixa.

##### CT-PB34-02 — Refresh idempotente e acionável
- **Tipo:** API · **Prioridade:** Alta · **Resultado esperado:** reenvio não duplica; reauth/rate/quota
  têm respostas distintas. · **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31; 429,
  `Retry-After`, quota e reauth distintos e sanitizados.

##### CT-PB34-03 — Home mostra quantidade e idade
- **Tipo:** frontend · **Prioridade:** Média · **Resultado esperado:** componente existente exibe
  sync sem tela nova, com loading/stale/erro acessíveis. · **Automatizável:** Parcialmente ·
  **Status:** Aprovado — 2026-07-31; estados presentes na Home e build Vite verde.

##### CT-PB34-04 — Geração usa biblioteca ou fallback Top
- **Tipo:** integração · **Prioridade:** Alta · **Resultado esperado:** ready usa perfil ponderado;
  ausente/falha usa PB-08 e ainda conclui quando há Tops suficientes. · **Automatizável:** Sim ·
  **Status:** Aprovado — revalidação 2026-07-31; biblioteca ausente, com zero faixas ou pool vazio
  aciona fallback Top PB-08, enquanto biblioteca utilizável segue ponderada.

##### CT-PB34-05 — Faixas nativas não usam Search
- **Tipo:** regressão PB-25 · **Prioridade:** Alta · **Resultado esperado:** Top/playlist com ID/URI
  válidos são reutilizados; apenas externas usam Search. · **Automatizável:** Sim ·
  **Status:** Aprovado — 2026-07-31; identidade nativa e peso 0,45 preservados.

##### CT-PB34-06 — Explicação agregada sem origem privada
- **Tipo:** privacidade/resultado · **Prioridade:** Alta · **Resultado esperado:** proporções
  Top/playlist/contexto, sem nomes de playlists, faixas de perfil bruto ou usuário associado. ·
  **Automatizável:** Sim · **Status:** Aprovado — 2026-07-31; explicação contém somente percentuais
  agregados.

### Testes integrados da Sprint 7

##### CT-S7-INT-01 — Três usuários sincronizam e geram
- **Tipo:** integração/e2e mockado · **Prioridade:** Alta · **Resultado esperado:** cada biblioteca
  `<=500`, pool `<=250` por pessoa e playlist final com 20–30 faixas. · **Automatizável:** Sim ·
  **Status:** Não executado

##### CT-S7-INT-02 — Cache fresco e incremental reduzem chamadas
- **Tipo:** performance/cache · **Prioridade:** Alta · **Resultado esperado:** segunda leitura <7d
  faz zero chamada; após TTL, só playlists alteradas baixam itens. · **Automatizável:** Sim ·
  **Status:** Não executado

##### CT-S7-INT-03 — Falha de quota/rate preserva demonstração
- **Tipo:** recuperação · **Prioridade:** Alta · **Resultado esperado:** cache pronto/stale continua
  gerando; sem parcial, 500 ou falsos descartes. · **Automatizável:** Sim · **Status:** Não executado

##### CT-S7-INT-04 — Privacidade e remoção ponta a ponta
- **Tipo:** privacidade · **Prioridade:** Alta · **Resultado esperado:** isolamento entre usuários,
  nada bruto no LLM/resultado e `DELETE /auth/me` remove a biblioteca pessoal. ·
  **Automatizável:** Sim · **Status:** Não executado

##### CT-S7-INT-05 — Regressão completa
- **Tipo:** regressão · **Prioridade:** Alta · **Resultado esperado:** Sprints 1–6, migrações,
  build e motor continuam verdes. · **Automatizável:** Sim · **Status:** Não executado

##### CT-S7-INT-06 — Spike real Spotify sanitizado
- **Tipo:** e2e real · **Prioridade:** Alta · **Cenário:** três contas allowlisted. ·
  **Resultado esperado:** reconsentimento, inventário elegível, sync, cache e geração reais; evidência
  sem token/nome de playlist/faixas pessoais. · **Automatizável:** Não · **Status:** Não executado

#### Critérios de aprovação da Sprint
PB-30..34 validados em ordem; CT-S7-INT-01..06 aprovados; limite 500 e pool 250 comprovados nas
fronteiras; nenhuma regressão, segredo, N+1 por faixa ou defeito alto/bloqueante aberto.

#### Resultado da Sprint
Não iniciada. Planejamento aprovado documentalmente não equivale a implementação ou QA.

---

## Apêndice — Rastreabilidade PB × critérios × casos

| PB | Sprint | Nº de casos individuais | Testes integrados |
|---|---|---:|---|
| PB-01 | 1 | 6 (CT-PB01-01..06) | CT-S1-INT-* |
| PB-02 | 1 | 7 (CT-PB02-01..07) | CT-S1-INT-* |
| PB-04 | 1 | 6 (CT-PB04-01..06) | CT-S1-INT-* |
| PB-05 | 1 | 7 (CT-PB05-01..07) | CT-S1-INT-* |
| PB-06 | 1 | 5 (CT-PB06-01..05) | CT-S1-INT-* |
| PB-08 | 1 | 6 (CT-PB08-01..06) | CT-S1-INT-* |
| PB-09 | 2 | 4 (CT-PB09-01..04) | CT-S2-INT-* |
| PB-10 | 2 | 5 (CT-PB10-01..05) | CT-S2-INT-* |
| PB-11 | 2 | 4 (CT-PB11-01..04) | CT-S2-INT-* |
| PB-12 | 2 | 7 (CT-PB12-01..07) | CT-S2-INT-* |
| PB-13 | 2 | 6 (CT-PB13-01..06) | CT-S2-INT-* |
| PB-14 | 3 | 5 (CT-PB14-01..05) | CT-S3-INT-* |
| PB-15 | 3 | 5 (CT-PB15-01..05) | CT-S3-INT-* |
| PB-16 | 3 | 6 (CT-PB16-01..06) | CT-S3-INT-* |
| PB-17 | 3 | 6 (CT-PB17-01..06) | CT-S3-INT-* |
| PB-07 | 3 | 6 (CT-PB07-01..06) | CT-S3-INT-* |
| PB-03 | 4 | 4 (CT-PB03-01..04) | CT-S4-INT-* |
| PB-18 | 4 | 5 (CT-PB18-01..05) | CT-S4-INT-* |
| PB-19 | 4 | 5 (CT-PB19-01..05) | CT-S4-INT-* |
| PB-20 | 4 | 5 (CT-PB20-01..05) | CT-S4-INT-* |
| PB-21 | 5 | 6 (CT-PB21-01..06) | CT-S5-INT-* |
| PB-22 | 5 | 6 (CT-PB22-01..06) | CT-S5-INT-* |
| PB-23 | 5 | 6 (CT-PB23-01..06) | CT-S5-INT-* |
| PB-24 | 5 | 6 (CT-PB24-01..06) | CT-S5-INT-* |
| PB-25 | 6 | 5 (CT-PB25-01..05) | CT-S6-INT-* |
| PB-26 | 6 | 5 (CT-PB26-01..05) | CT-S6-INT-* |
| PB-27 | 6 | 5 (CT-PB27-01..05) | CT-S6-INT-* |
| PB-28 | 6 | 4 (CT-PB28-01..04) | CT-S6-INT-* |
| PB-29 | 6 | 5 (CT-PB29-01..05) | CT-S6-INT-* |
| PB-30 | 7 | 5 (CT-PB30-01..05) | CT-S7-INT-* |
| PB-31 | 7 | 6 (CT-PB31-01..06) | CT-S7-INT-* |
| PB-32 | 7 | 6 (CT-PB32-01..06) | CT-S7-INT-* |
| PB-33 | 7 | 6 (CT-PB33-01..06) | CT-S7-INT-* |
| PB-34 | 7 | 6 (CT-PB34-01..06) | CT-S7-INT-* |
