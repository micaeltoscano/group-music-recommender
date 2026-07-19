# Levantamento inicial — Modelagem UML do Vibe Check

> Documento de análise, não de modelagem. Nenhum diagrama foi gerado nesta etapa.
> Base: código em `backend/app` (FastAPI + SQLAlchemy + Alembic) e `frontend/src` (React/Vite),
> cruzado com `v3-Backlog_Scrum_VibeCheck.docx.pdf` (RF-01..RF-11, épicos, personas) e com os
> documentos locais `docs/produto/BACKLOG_PRODUTO.md` e `docs/planejamento/PLANO_EXECUCAO.md`.

## 0. Panorama técnico

- **Backend:** Python + FastAPI, SQLAlchemy 2.0 (Mapped/mapped_column) + Alembic, PostgreSQL
  (SQLite só em teste) — consistente com RFN-10/11/12 do backlog.
  - `app/api/*` — camada de rotas (auth, rooms, music, vibe_check, feedback, health).
  - `app/services/*` — casos de uso/orquestração (room_service, music_service, generation_service,
    result_service, feedback_service, privacy_service, contextual_pool_service,
    context_enrichment_service).
  - `app/engine/*` — o **Preference Negotiation Engine (PNE)**: módulos puros, sem I/O nem banco
    (taste, candidates, scoring, fairness, clustering, bridge, subgroup_balance, context_scoring,
    vibe_scoring, contextual_pool, sequencer, track_matcher, weights) — bate com RNF-03/RNF-04
    ("motor... sem chamadas de rede", "reprodutibilidade").
  - `app/clients/*` — integrações externas: `spotify_client`, `lastfm_client`, `llm_client`
    (Ollama local), `crypto` (Fernet).
  - `app/db/models.py` — 12 entidades ORM (ver seção 2).
- **Frontend:** React (Vite), rotas em `App.jsx`: `/login`, `/` (Home), `/rooms/:code` (Room/lobby),
  `/rooms/:code/vibe-check`, `/rooms/:code/result`, `/rooms/:code/feedback`.
- **Testes:** `backend/tests` nomeados por PB (`test_pbNN_*` e variantes `_qa`), cobrindo até PB-24,
  mais PB-25 a PB-29 e integrações de Sprint (S3–S6) — ver inconsistência (d.1).

## 1. Atores identificados

| Ator | Origem | Observações |
|---|---|---|
| **Host / Anfitrião** | Persona "Marina" (doc) + `role="host"` em `MusicSessionMember` e guardas `RoomHostRequiredError` (código) | Único que cria sala, define contexto/modo (PB-05/PB-06), dispara geração (PB-12/13) e recebe a playlist na própria conta Spotify. |
| **Convidado / Integrante** | Personas "Rafael" (gosto minoritário) e "Lucas" (casual) (doc) + `role` genérico de membro, endpoints de join/vibe-check/feedback (código) | As duas personas mapeiam para o mesmo ator técnico (`MusicSessionMember` sem papel especial); a diferença é comportamental (responder vs. pular o Vibe Check), não estrutural. |
| **Spotify (ator externo/sistema)** | RF-01/RF-04/RF-08 (doc) + `app/clients/spotify_client.py` (OAuth, top tracks/artists, search, criação de playlist) | Autoridade de identidade (OAuth) e de catálogo/execução (matching + playlist real). |
| **Last.fm (ator externo/sistema)** | RF-03 "fontes externas" / PB-17 do doc + `app/clients/lastfm_client.py` | Só enriquece tags de contexto; erros são absorvidos (RNF-08). |
| **LLM local / Ollama (ator externo/sistema)** | RF-03 "interpretação estruturada de textos livres" / PB-16 do doc + `app/clients/llm_client.py` (`_call_ollama`, fallback determinístico) | Não decide músicas (RF-09/backlog); só traduz contexto livre em `LLMContext` estruturado, com fallback obrigatório. |

Não foram encontrados atores adicionais no código (não há papel de "moderador"/"admin" além de host, nem
autenticação alternativa a Spotify OAuth, conforme RF-01).

## 2. Classes/entidades candidatas

### 2.1 Entidades persistentes (`app/db/models.py`, SQLAlchemy ORM)

- **User** — `id, spotify_id, display_name, image_url, created_at, updated_at`
  - 1—1 `SpotifyToken` (composição, `cascade delete-orphan`)
  - 1—N `AppSession` (composição)
  - 1—N `MusicSession` como host (`hosted_music_sessions`)
  - 1—N `MusicSessionMember` (associação N-N com `MusicSession`)
  - 1—N `UserMusicSnapshot`
- **SpotifyToken** — `user_id (PK/FK), access_token, refresh_token (cifrados), token_expires_at,
  refresh_token_expires_at, reauth_required_at, scopes, updated_at`
- **AppSession** — `id, user_id, session_token_hash, expires_at, created_at`
- **MusicSession** ("sala") — `id, code, host_user_id, occasion, description, mode, status,
  created_at, expires_at`
  - 1—N `MusicSessionMember`, 1—N `PlaylistRun`
- **MusicSessionMember** (classe associativa User×MusicSession) — PK composta
  `(session_id, user_id)`, `role, joined_at`
- **UserMusicSnapshot** — `id, user_id, time_range, top_tracks_json, top_artists_json, fetched_at`;
  único por `(user_id, time_range)` — é o "Perfil Musical" bruto citado no backlog (PB-08/RF-04)
- **VibeCheckAnswer** — `id, session_id, user_id, status(pending/answered/skipped), energy, valence,
  popularity, created_at, updated_at`; único por `(session_id, user_id)`
- **PlaylistRun** ("Execução/Geração") — `id, session_id, status(running/completed/failed),
  error_message, progress_stage, progress_percent, spotify_playlist_id, spotify_playlist_url,
  compatibility_score, fairness_score, explanation_json, llm_context_json,
  subgroup_balancing_applied, created_at, updated_at`
  - 1—N `PlaylistRunTrack`
- **PlaylistRunTrack** — `id, run_id, candidate_id, spotify_id, spotify_uri, name, artist,
  match_confidence, discard_reason, status(matched/discarded/selected?), source, is_bridge,
  selection_rank, created_at`
- **TrackContextCache** — `id, spotify_track_id (único), track_name, artist_name,
  lastfm_track_tags_json, lastfm_artist_tags_json, spotify_artist_genres_json,
  context_scores_json, source, confidence, fetched_at` — cache independente (sem FK), chaveado por
  `spotify_track_id`, referenciado logicamente pelas candidatas do motor.
- **MemberTrackFeedback** — `id, user_id, playlist_run_id, spotify_track_id, liked, disliked,
  more_like_this, never_again, created_at, updated_at`; único por `(user_id, run_id, track_id)`
- **PlaylistFeedback** — `id, user_id, playlist_run_id, representation_score(0-5),
  satisfaction_score(0-5), comments, created_at, updated_at`; único por `(user_id, run_id)`

### 2.2 Objetos de domínio do motor (`app/engine/*`, em memória, sem persistência)

- **UserTasteProfile** (`taste.py`) — `user_id, tracks:set, artists:set, genres:set`, construído a
  partir do snapshot; `jaccard_similarity`, `calculate_pairwise_compatibility`,
  `calculate_group_compatibility` (RF-05/PB-09).
- **CandidateTrack** (`candidates.py`) — `id, raw_data, source_user_ids, source_cluster_ids,
  is_bridge, bridge_score, bridge_cluster_ids, subgroup_balancing_applied, balanced_cluster_id,
  origin` — a "Música Candidata" do backlog (RF-06/PB-10).
- **DiscardedTrack** — `raw_data, reason, user_id` (candidatas descartadas com motivo, PB-10 critério 4).
- **ContextCriteria** (`context_scoring.py`, dataclass frozen) — `occasion, mood, energy,
  tags_positive, tags_negative, avoid` — saída estruturada do LLM (RF-03/PB-16).
- **VibePreferences** (`vibe_scoring.py`, dataclass frozen) — `energy, valence, popularity` em
  `[0,1]`, agregadas do grupo a partir de `VibeCheckAnswer` (PB-07).
- **ProfileSimilarity / TasteCluster / TasteClusteringResult** (`clustering.py`) — agrupamento de
  perfis (PB-21/22 do código; ver seção de numeração na inconsistência d.2).
- **ClusterAcceptance / BridgeTrackEvaluation** (`bridge.py`) — músicas-ponte entre subgrupos.
- **ClusterAllocation / SubgroupBalanceResult** (`subgroup_balance.py`) — balanceamento final.
- **SequencerTrack** (`sequencer.py`, dataclass frozen/slots) — ordenação final da playlist (PB-19
  do backlog / PB-19 sequenciador no código, mesmo número).

### 2.3 Relações principais (resumo para diagrama de classes)

```
User "1" --- "1" SpotifyToken        (composição)
User "1" --- "0..*" AppSession        (composição)
User "1" --- "0..*" MusicSession      (host_user_id)
User "1" --- "0..*" MusicSessionMember -- "0..*" MusicSession   (associação N-N com atributo role)
User "1" --- "0..*" UserMusicSnapshot
MusicSession "1" --- "0..*" PlaylistRun
PlaylistRun "1" --- "0..*" PlaylistRunTrack
PlaylistRun "1" --- "0..*" MemberTrackFeedback (via user_id)
PlaylistRun "1" --- "0..*" PlaylistFeedback (via user_id)
MusicSession "1" --- "0..*" VibeCheckAnswer -- "1" User
TrackContextCache  (independente, referenciado por spotify_track_id, não é FK real)
```

No motor (não persistido): `UserTasteProfile[]` + `ContextCriteria` + `VibePreferences` →
`CandidateTrack[]` (via clustering/bridge/subgroup_balance) → `SequencerTrack[]` → gravados como
`PlaylistRunTrack`.

## 3. Fluxos candidatos a diagrama de sequência

Ordenados por relevância/complexidade:

1. **Geração ponta-a-ponta da playlist (`execute_generation`, `generation_service.py`)** —
   *Justificativa:* é o coração do produto (PNE completo): interpretação de contexto via LLM →
   snapshots/perfis → clustering de gosto → pool de candidatas → enriquecimento Spotify/Last.fm →
   descoberta contextual → scoring individual/coletivo/fairness → bridge/subgroup balance →
   matching no Spotify → sequenciamento → criação da playlist real → fechamento do run. Concentra
   quase todos os atores (Host, Spotify, Last.fm, LLM) e a maioria das entidades.
2. **Autenticação Spotify OAuth (`/auth/login` → `/auth/callback`, `auth.py`)** — *Justificativa:*
   pré-requisito técnico de todo o resto (RF-01/PB-02); ilustra o padrão state→code→token,
   upsert de `User`/`SpotifyToken`, criação de `AppSession` e a criptografia em repouso (RNF-01).
3. **Criação e entrada em sala por código (`create_room`/`join_room`, `room_service.py`)** —
   *Justificativa:* mostra os dois atores humanos interagindo (Host cria, Convidado entra),
   concorrência real (`SELECT ... FOR UPDATE`), limite de 5 membros e o guard de autorização
   (403 para não-membro) — RF-02/PB-04/PB-05.
4. **Contexto, modo de consenso e Vibe Check (`update_room_context/mode`, `vibe_check.py`)** —
   *Justificativa:* único fluxo host-only vs. membro-comum lado a lado, e o único ponto de
   coleta direta de preferência subjetiva do usuário (energy/valence/popularity) antes da geração
   — RF-03/PB-06/PB-07/PB-29 (status pending/answered/skipped).
5. **Resultado e explicabilidade (`GET /rooms/{code}/result` → `build_room_result`,
   `result_service.py`)** — *Justificativa:* fluxo de leitura que expõe fairness/compatibilidade e
   justificativas por faixa sem vazar rejeições individuais (RNF-02/RF-09/PB-15).
6. **Feedback pós-playlist (`save_track_feedback`/`save_playlist_feedback`,
   `feedback_service.py`)** — *Justificativa:* fecha o ciclo do usuário (like/dislike/never again +
   notas de satisfação/representação), com guarda de acesso e de execução concluída — RF-09/PB-20.

## 4. Inconsistências entre backlog e código

1. **Deslocamento de numeração dos PB entre a seção 5.2 e a seção 5.3/5.4 do próprio PDF, e o
   código segue a segunda.** Na seção 5.2 do documento anexado, PB-01 = "Autenticação com Spotify".
   Já na tabela "Backlog Resumido e Priorizado" (5.3) e nos Sprint Backlogs (5.4), a linha 1 já
   aparece como **PB-02 — Autenticação Spotify**, ou seja, o próprio documento tem duas numerações
   internas divergentes (a narrativa de histórias vs. a tabela resumida), deslocadas em uma posição
   a partir do PB-01. O código/repositório (migrations, testes `test_pb0N_*`, `PLANO_EXECUCAO.md`)
   segue **a numeração da tabela/sprints**: PB-01 = fundação técnica (scaffold, sem história própria
   na seção 5.2), PB-02 = autenticação, ..., PB-24 = balanceamento de subgrupos. Qualquer diagrama ou
   relatório de QA deve citar PB-XX pela numeração do código/`PLANO_EXECUCAO.md`, não pela seção 5.2
   isolada do PDF, para não gerar referência cruzada errada.
2. **PB-25 a PB-29 existem no código e nos testes, mas não no Backlog Scrum v1.0 anexado.**
   `docs/planejamento/SPRINT_06_IMPLEMENTACAO.md` documenta uma "Sprint 6 — Evolução/estabilização"
   com PB-25 (resiliência Spotify), PB-26 (pool contextual híbrido com Last.fm), PB-27
   (acompanhamento compartilhado da geração — migração `0017_pb27_generation_progress`), PB-28
   (conformidade visual do Login) e PB-29 (estado compartilhado/privado do Vibe Check — migração
   `0018_pb29_vibe_status`). Isso é consistente com o branch atual
   (`feat/SPRINT06/stabilization`), mas são histórias técnicas de estabilização sem critérios de
   aceitação formais no documento fornecido pelo usuário — tratar como extensão local, não como
   parte do escopo oficial do backlog acadêmico ao desenhar os diagramas de caso de uso.
3. **"Rejeição" (RF-07/PB-11/PB-12) é inferida, não coletada explicitamente.** O backlog descreve
   "uma rejeição forte deve reduzir o score... mesmo quando ela agradar a maioria" e a persona
   Rafael espera "evitar músicas pelas quais possui forte rejeição". No código, `apply_rejection_penalty`
   (`engine/fairness.py`) trata como "rejeição" qualquer `individual_score <= veto_threshold`
   (default 0.05) — ou seja, é um efeito colateral do score de afinidade baixo, não um sinal
   explícito de "eu rejeito este artista/faixa". O `VibeCheckAnswer` só coleta `energy`, `valence`,
   `popularity` numéricos; não há endpoint/tabela para o integrante marcar uma rejeição direta antes
   da geração. O único feedback explícito de rejeição (`disliked`/`never_again` em
   `MemberTrackFeedback`) é **pós-playlist** e o próprio backlog (PB-19/20) exige que não alimente o
   ranqueamento do MVP. Vale confirmar com o time se isso é uma lacuna de escopo ou uma decisão de
   design deliberada antes de modelar o caso de uso "Rejeitar música".
4. **Épico "EP-08 — Evolução do produto" é citado (PB-20/Modo Descoberta, seção 5.2.20) mas não
   consta na tabela de Épicos (seção 5.1, que só lista EP-01..EP-07)** — gap pré-existente no
   próprio PDF, não introduzido pelo código; mencionar na legenda do diagrama de casos de uso caso
   EP-08 seja usado como agrupador.
5. **`PlaylistRunTrack.status` e `source`** não têm um enum fechado nem tabela de domínio no código
   (são `String`/`Text` livres) — os valores observados nos serviços (`matched`, `discarded`, uso de
   `discard_reason`) cobrem os critérios de PB-13/PB-14, mas não há uma "Fonte da candidata" com
   estrutura própria como a linguagem do backlog ("origem de cada candidata deve ser registrada")
   sugere; hoje `source` é uma string serializada (comentário no código: "JSON ou lista em string").
   Não é um defeito, mas ao desenhar o diagrama de classes é preciso decidir se `source`/`origin`
   viram um Value Object explícito ou permanecem atributos primitivos.

---

**Próximo passo (aguardando sua revisão):** com este levantamento validado, seguimos para os
diagramas (casos de uso, classes e as sequências da seção 3) em arquivos separados dentro de
`diagrams/`.
