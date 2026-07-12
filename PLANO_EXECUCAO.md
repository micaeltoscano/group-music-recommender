# Plano de Execução — Vibe Check

Este arquivo é a memória operacional do projeto. O `BACKLOG_PRODUTO.md` define o escopo e os critérios de aceitação; o `README.md` descreve o produto e a arquitetura. Aqui ficam apenas a ordem de execução, o trabalho atual e o ponto exato de retomada.

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
- **Trabalho em andamento e retomada:** este arquivo.
- **Comportamento real:** código e testes automatizados.

Em caso de contradição, registrar a decisão neste arquivo e corrigir os documentos afetados na mesma história.

## 3. Regras de trabalho

- Manter apenas uma história principal em andamento.
- Implementar primeiro o menor fluxo verificável.
- Não iniciar extras antes de concluir o caminho principal do MVP.
- Toda história precisa cumprir seus critérios de aceitação e a Definition of Done do backlog.
- Criar testes junto com a funcionalidade, não apenas no final.
- Nunca versionar ou registrar tokens, chaves e segredos.
- Manter o motor em `engine/` puro, determinístico e sem banco ou rede.
- Registrar ideias novas no backlog sem interromper a história atual.
- Usar commits pequenos identificados pela história, por exemplo: `feat(PB-04): criar sala efêmera`.

## 4. Marcos de entrega

### M0 — Preparação externa

- [ ] Criar o aplicativo no Spotify Developer Dashboard.
- [ ] Configurar a redirect URI local.
- [ ] Definir as contas autorizadas para a demonstração.
- [ ] Confirmar as versões de Python, Node.js e Docker usadas pela equipe.
- [ ] Preparar variáveis locais sem versionar segredos.

**Saída esperada:** credenciais e ambiente disponíveis para o spike, sem segredos no Git.

### M1 — Fundação e validação do Spotify

Histórias: `PB-01`, spike técnico e `PB-02`.

- [x] Criar backend FastAPI. — PB-01
- [x] Criar frontend React com Vite. — PB-01 (scaffold pronto; execução pendente de Node)
- [x] Subir PostgreSQL com Docker Compose. — PB-01
- [x] Configurar SQLAlchemy e Alembic. — PB-01 (migração `0001_initial`)
- [x] Criar `.env.example` e instruções de execução. — PB-01
- [ ] Validar OAuth com proteção por `state`.
- [ ] Validar top tracks, top artists e Spotify Search.
- [ ] Validar criação de playlist privada e adição de faixas.
- [ ] Persistir tokens criptografados somente no backend.
- [ ] Implementar sessão por cookie httpOnly e `/auth/me`.

**Saída esperada:** um usuário entra pelo Spotify e o backend consegue criar uma playlist privada de teste.

### M2 — Sala utilizável

Histórias: `PB-04`, `PB-05`, `PB-06` e `PB-08`.

- [ ] Criar sala efêmera com código curto e expiração de 24 horas.
- [ ] Registrar host e permitir entrada de membros sem duplicidade.
- [ ] Aplicar limite de cinco integrantes e guardas de acesso.
- [ ] Atualizar sala no frontend por polling.
- [ ] Permitir que o host defina contexto e modo de consenso.
- [ ] Coletar e armazenar snapshots de top tracks e top artists.
- [ ] Reutilizar snapshots válidos e tratar reautenticação.

**Saída esperada:** duas ou mais pessoas entram em uma sala e seus dados musicais ficam prontos para o motor.

### M3 — Motor de negociação

Histórias: `PB-09`, `PB-10`, `PB-11` e `PB-12`.

- [ ] Modelar gosto individual e compatibilidade.
- [ ] Montar e deduplicar o pool de candidatas.
- [ ] Registrar a origem e os descartes de candidatas.
- [ ] Implementar pesos configuráveis de score individual e coletivo.
- [ ] Implementar rejeição, least misery, cobertura e fairness.
- [ ] Implementar os modos Democrático e Festa Segura.
- [ ] Testar grupos unitários, listas vazias, gostos divergentes e vetos fortes.

**Saída esperada:** para entradas fixas, o motor produz uma seleção reproduzível e explica seus scores sem realizar chamadas externas.

### M4 — Fluxo principal completo

Histórias: `PB-13`, `PB-14` e `PB-15`.

- [ ] Criar e persistir execuções de geração.
- [ ] Impedir gerações concorrentes com resposta 409.
- [ ] Resolver candidatas via Spotify Search usando o token do host.
- [ ] Validar correspondência, URI e disponibilidade.
- [ ] Aplicar limite de duas faixas por artista.
- [ ] Criar playlist privada real na conta do host.
- [ ] Exibir compatibilidade, fairness, representação e motivos agregados.
- [ ] Verificar o fluxo completo com contas reais da demonstração.

**Saída esperada:** o fluxo principal do MVP funciona de ponta a ponta.

### M5 — Complementos priorizados

Avaliar apenas depois do M4 e conforme o tempo restante:

1. `PB-07` — Vibe Check opcional.
2. `PB-16` — interpretação estruturada por LLM.
3. `PB-17` — enriquecimento por Last.fm.
4. `PB-18` — sequenciamento da playlist.
5. `PB-03` — logout e remoção de dados.
6. `PB-19` — feedback.
7. `PB-20` — consolidação de qualidade, documentação e demonstração.

`PB-21` e `PB-22` permanecem fora do MVP.

## 5. Trabalho atual

### História ativa: PB-01 — Fundação técnica

**Objetivo da sessão:** criar uma base local integrada e reproduzível para frontend, backend e banco de dados.

**Critérios de aceitação:**

- [~] Frontend e backend iniciam conforme instruções documentadas. — **Backend: verificado** (uvicorn sobe, `/health` e `/docs` → 200). **Frontend: build verificado** em container Node 20 (`npm install` + `vite build` OK, 28 módulos, `dist/` gerado); falta apenas rodar o `npm run dev` **nativo** no host, pendente de instalar Node local (ver bloqueios).
- [x] Backend conecta ao PostgreSQL. — verificado: `GET /health/db` → 200 `{"status":"ok","database":"ok"}`.
- [x] Migração inicial do Alembic executa e reverte sem erro. — verificado: `upgrade head` cria `users`; `downgrade base` remove; `upgrade head` reaplica.
- [x] Configurações sensíveis vêm de variáveis de ambiente não versionadas. — `.env` ignorado pelo Git e vazio; `.env.example` sem segredos; config via `pydantic-settings`.

**Tarefas realizadas nesta sessão:**

1. [x] Estrutura inicial criada: `backend/` (FastAPI), `frontend/` (React/Vite) e `docker-compose.yml`.
2. [x] PostgreSQL (compose), SQLAlchemy, Alembic (migração `0001_initial` → tabela `users`) e endpoints de saúde (`/health`, `/health/db`).
3. [x] Instalação, comandos de inicialização e verificação documentados no `README.md` (seção "Execução local — Fundação técnica (PB-01)").

**Fora do escopo desta história:** OAuth, salas, motor, LLM, Last.fm e interface definitiva.

**Como verificar (comandos):**

```bash
cp .env.example .env
docker compose up -d db
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
alembic upgrade head && alembic downgrade base && alembic upgrade head   # migração ida e volta
pytest                                                                   # 4 testes
uvicorn app.main:app --reload --port 8000 &                              # backend
curl http://localhost:8000/health && curl http://localhost:8000/health/db
cd ../frontend && npm install && npm run dev                             # requer Node ≥18
```

**Resultado da verificação (2026-07-12):**

- Backend sobe e responde: `/` , `/health`, `/health/db` (200), `/docs` (200).
- Backend conecta ao Postgres (`SELECT 1` via `/health/db`).
- Alembic: `upgrade head` → `downgrade base` → `upgrade head` sem erros; tabela `users` criada/removida/recriada.
- `pytest`: **4 passed**.
- Frontend: `npm install` + `vite build` OK em container Node 20 (28 módulos, `dist/` gerado) — o código compila.
- Nenhum segredo versionado: `.env` não rastreado e com 0 bytes; `.venv` não rastreado.
- **Não verificado:** start nativo do frontend (`npm run dev`) no host, por ausência de Node.js/npm no ambiente (o build via container supre parcialmente).

**Status:** concluída no backend/banco/migração; **pendente apenas a execução do frontend** (bloqueio de ambiente: Node ausente). Ver "Diário de retomada".

## 6. Decisões registradas

| Data | Decisão | Motivo |
|---|---|---|
| 2026-07-12 | Implementar primeiro o caminho principal do MVP. | Reduzir dispersão e obter um fluxo demonstrável cedo. |
| 2026-07-12 | Tratar LLM, Last.fm, Vibe Check e feedback como complementos após o fluxo principal. | Todos possuem fallback ou não são indispensáveis à primeira validação. |
| 2026-07-12 | Executar um spike Spotify no primeiro marco. | Antecipar o maior risco externo do projeto. |
| 2026-07-12 | Versões de referência registradas: Python 3.11.9, Docker 29.6.1 / Compose v5.2.0. Node.js/npm ausentes no ambiente. | Cumprir o marco M0 (confirmar versões) e explicar a única verificação pendente do PB-01. |
| 2026-07-12 | Stack do backend fixada: FastAPI + SQLAlchemy 2.0 + Alembic + `psycopg2-binary`; config via `pydantic-settings`. | Base estável e amplamente suportada em Python 3.11; segredos apenas em variáveis de ambiente. |
| 2026-07-12 | Migração inicial cria somente a tabela `users`. | Validar upgrade/downgrade de forma real sem antecipar tabelas de histórias futuras (mantém o recorte do PB-01). |

## 7. Riscos e bloqueios atuais

- O Spotify Development Mode limita o aplicativo a cinco usuários autorizados.
- Os endpoints permitidos precisam ser confirmados em um aplicativo novo.
- O núcleo estimado do MVP excede com folga uma sprint e pode ultrapassar um mês.
- **Bloqueio de ambiente (PB-01):** Node.js/npm não estão instalados nesta máquina, então o start do frontend (`npm run dev`) não pôde ser verificado. O código do Vite está pronto; falta instalar Node ≥18 e rodar. Python 3.11.9 e Docker 29.6.1 já confirmados.
- A capacidade real da equipe (velocidade) ainda precisa ser medida na primeira sprint.

## 8. Diário de retomada

Atualizar esta seção ao encerrar cada sessão.

- **Data da última sessão:** 2026-07-12.
- **História em andamento:** PB-01 (fundação técnica) — praticamente concluída.
- **Último resultado concluído:** fundação técnica criada e verificada — backend FastAPI + PostgreSQL (Docker) + Alembic (upgrade/downgrade da migração inicial) + `.env.example` sem segredos + `pytest` (4 passed). Frontend Vite com scaffold pronto.
- **Onde parou:** backend, banco e migração validados de ponta a ponta; **falta apenas executar o frontend** — `npm run dev` não rodou porque Node.js/npm não estão instalados nesta máquina.
- **Próxima ação exata:** (1) instalar Node.js ≥18 (ex.: via nvm ou instalador oficial) e rodar `cd frontend && npm install && npm run dev`, confirmando a tela de status em `http://localhost:5173`; (2) marcar o critério "frontend inicia" como concluído; (3) iniciar **PB-02 — Autenticação com Spotify** (depende de M0: app no Spotify Dashboard e redirect URI).
- **Comando/teste para retomada:**
  ```bash
  node --version            # confirmar Node ≥18 instalado
  cd frontend && npm install && npm run dev
  # em outro terminal, backend + banco:
  docker compose up -d db
  cd backend && source .venv/bin/activate && alembic upgrade head && uvicorn app.main:app --reload --port 8000
  ```
- **Bloqueios:** Node.js/npm ausentes no ambiente (impede verificar o start do frontend). Credenciais Spotify serão necessárias a partir de PB-02.

## 9. Checklist de encerramento de sessão

- [x] Rodei os testes e verificações relevantes. — `pytest` (4 passed); Alembic upgrade/downgrade; health checks 200.
- [x] Comparei o resultado com os critérios da história. — 3/4 critérios verificados; "frontend inicia" pendente (Node ausente).
- [x] Atualizei checkboxes e status sem declarar trabalho incompleto como pronto.
- [x] Registrei decisões ou bloqueios novos. — versões, stack, migração mínima; bloqueio de Node.
- [x] Atualizei o diário de retomada com a próxima ação exata.
- [x] Atualizei a documentação afetada. — `README.md` (seção de execução) e este plano.
- [x] Confirmei que nenhum segredo ou token foi adicionado. — `.env` não rastreado e vazio; `.env.example` sem segredos.
- [ ] Preparei um commit pequeno e relacionado à história. — **pendente**: aguardando o usuário decidir sobre o commit.

## 10. Modelo de pedido para uma sessão assistida

```text
História ativa: PB-XX
Objetivo desta sessão:
Critérios de aceitação envolvidos:
Arquivos ou componentes em escopo:
Fora do escopo:
Como verificar:

Antes de alterar, inspecione o estado atual. Implemente somente este recorte,
execute as verificações relevantes e atualize o PLANO_EXECUCAO.md com o ponto
exato de retomada.
```
