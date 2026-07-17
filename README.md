# Group Music Recommender ("Vibe Check")

## Context

Projeto de Engenharia de Software: um sistema web de recomendação musical **em grupo**, uma versão melhorada do Blend/Match do Spotify. Um usuário cria uma sala/sessão efêmera, várias pessoas entram com um **código curto**, todos logam via **Spotify OAuth**, e o sistema gera uma **playlist real na conta Spotify do host**.

O diferencial **não** é "misturar gostos": é um **sistema de negociação musical** que equilibra gostos, contexto, justiça e rejeição para criar playlists que representam o grupo inteiro.

> "Spotify entende o passado musical. O Vibe Check entende o humor do momento. O motor de consenso entende o grupo. O sistema gera uma playlist que representa todo mundo."

Repositório greenfield (só `README.md` e `development_guide.md`). Prazo ~1 mês para o MVP; arquitetura preparada para crescimento.

### Decisões fixas
- **Auth:** exclusivamente Spotify OAuth (sem senha/JWT próprio como auth principal).
- **Sessões:** efêmeras, por código curto (sem grupos persistentes no MVP).
- **Saída:** playlist real criada no Spotify do host.
- **Spotify:** usar só OAuth, top tracks/artists, Search, criar playlist, add items. **Não** depender de `Recommendations`, `Audio Features`, `Audio Analysis` (descontinuados p/ apps novos).
- **Tokens:** ficam só no backend, criptografados; o frontend **nunca** recebe access/refresh token do Spotify.
- **LLM (Claude, `claude-sonnet-5`):** interpreta **intenção/contexto** e produz JSON estruturado. **Não** é juiz final da playlist. O **motor próprio** decide, ranqueia e explica.
- **Stack:** FastAPI + React (Vite) + Postgres + SQLAlchemy/Alembic.
- **Spotify Development Mode:** limite de **5 usuários autorizados no app inteiro** (não por sala). MVP planejado p/ ≤ 5 usuários totais; contas Premium pré-cadastradas na demo. Extended Quota Mode fica no radar desde o início (aprovação depende do Spotify).

### Scopes Spotify
`user-top-read`, `playlist-modify-private` (padrão: playlist **privada**), `playlist-modify-public` **só se** playlists públicas forem permitidas, `user-read-private` **só se** precisar de país/market do usuário.

---

## 1. Visão geral do produto

App de "negociação musical" para grupos. Nome interno do motor: **Preference Negotiation Engine (PNE)**, com 5 camadas:

1. **Individual Taste Modeling** — modela o gosto de cada membro (top tracks/artists, artistas das faixas, gêneros).
2. **Context Understanding** — LLM interpreta ocasião + descrição livre do host → critérios estruturados.
3. **Mood & Theme Scoring** — tags Last.fm + gêneros/artistas Spotify + contexto do LLM + (opcional) análise temática de letras.
4. **Fair Group Optimization** — maximiza satisfação média **com restrições** de justiça, rejeição extrema e representação de minorias.
5. **Playlist Experience Sequencing** — ordena a playlist com fluxo, não por ranking bruto.

## 2. Escopo do MVP

1. Login com Spotify.
2. Criar sala por código curto / entrar por código.
3. Host define ocasião e/ou descrição livre; escolhe **modo de consenso**.
4. **Vibe Check** opcional (3–5 perguntas gamificadas → variáveis do algoritmo).
5. Coleta de top tracks/artists dos membros (com cache/snapshot).
6. Compatibilidade do grupo + Individual Taste Modeling.
7. Geração de pool de candidatas + scoring (individual → grupo) + rejection + fairness.
8. **Modos**: Democrático e Festa Segura (Descoberta se der tempo).
9. Mood & Context Scoring com **Last.fm** (com fallback em cascata).
10. Playlist Experience Sequencer (regras simples).
11. Criação de playlist real no Spotify do host.
12. Tela de resultado com explicabilidade + "Why this playlist is fair?".
13. Estrutura de **feedback pós-playlist** (like/dislike + representação) — coletada, base para futuro.

## 3. Fora do escopo (MVP)

- Login próprio / senha.
- Grupos persistentes.
- Endpoints descontinuados do Spotify.
- Lyrics Theme Classifier em produção (fica como extra acadêmico/offline/opcional).
- Group Taste Clustering / Modo Ponte Musical (arquitetura prevista, impl. só se sobrar tempo).
- Aprendizado (Learning to Rank, bandits, perfis persistentes) — só roadmap.

### 3.1 Limites e restrições operacionais (fechados do MVP)

- **Usuários:** ≤ 5 no app inteiro (Development Mode). Contas Premium pré-cadastradas.
- **Sala:** 1 a 5 membros. **Playlist:** 20 a 30 músicas. **Máx. 2 músicas por artista.**
- **Sessão expira em 24h** (`music_sessions.expires_at`). **Vibe Check:** máx. 5 perguntas.
- **Gerações por sala:** MVP permite **múltiplos `playlist_runs`** (regenerar), mas **uma geração por vez** (ver Generation Lock). Cada run cria uma playlist nova no Spotify.
- **Snapshots musicais** expiram após **X dias** (default 7) e são refetchados.

### 3.2 Segurança OAuth e privacidade

- **OAuth:** parâmetro `state` contra CSRF; validar `redirect_uri`; cookie de sessão **httpOnly + Secure (prod) + SameSite** adequado; nunca expor nem **logar** access/refresh token; `logout` invalida `app_session`.
- **Retenção:** salas efêmeras expiram; snapshots expiram; usuário pode fazer logout e apagar seus dados.
- **LLM e privacidade:** **não** enviar dados brutos do Spotify ao LLM. O LLM recebe só o **contexto do host** e critérios **agregados/anônimos** quando necessário.
- **Explicabilidade com privacidade:** motivos legíveis **sem** expor dados sensíveis de outros membros. Evitar "Pedro odeia funk"; preferir agregado: "alguns membros indicaram baixa tolerância a músicas muito tristes".

## 4. Arquitetura

```
React (Vite) ──HTTP (cookie httpOnly)──> FastAPI ──> Postgres (SQLAlchemy/Alembic)
                                            │
                                            ├─ SpotifyClient (OAuth, top, search, create playlist) + refresh central
                                            ├─ LLMClient (Claude claude-sonnet-5, JSON estruturado)
                                            ├─ LastFmClient (track/artist tags) + cache
                                            └─ Preference Negotiation Engine (scoring, fairness, sequencer)
```

Backend em camadas: `api/` (rotas finas) → `services/` (orquestração) → `engine/` (motor puro, testável sem I/O) → `clients/` (Spotify/LLM/Last.fm) → `db/`. O `engine/` recebe dados já buscados e retorna scores/ordem — **sem** chamadas de rede, para ser 100% testável.

**Segurança de tokens:** `spotify_tokens.access_token/refresh_token` criptografados em repouso (Fernet, chave em env). Refresh centralizado no `SpotifyClient` (access token expira em 1h). O **refresh token pode expirar após meses** → se o refresh falhar (ou `reauth_required_at` no passado), marcar reauth necessária e **redirecionar o usuário para novo login Spotify**. Sessão do app via cookie httpOnly (`session_token_hash`).

## 5. Modelo de dados

Legenda: **[MVP]** essencial · **[FUT]** previsto p/ crescimento.

**[MVP] users**: id · spotify_id · display_name · image_url · created_at · updated_at
**[MVP] spotify_tokens**: user_id(PK/FK) · access_token(enc) · refresh_token(enc) · token_expires_at · **refresh_token_expires_at** · **reauth_required_at** · scopes · updated_at
**[MVP] app_sessions**: id · user_id · session_token_hash · expires_at · created_at
**[MVP] music_sessions**: id · code(uniq) · host_user_id · occasion · description · mode · status(open/**generating**/completed) · spotify_playlist_id · spotify_playlist_url · created_at · expires_at(**24h**)
**[MVP] music_session_members**: session_id · user_id · role(host/member) · joined_at — PK(session_id,user_id) evita duplicidade
**[MVP] user_music_snapshots**: id · user_id · time_range · top_tracks_json · top_artists_json · fetched_at
**[MVP] playlist_runs**: id · music_session_id · status(**running/completed/failed**) · compatibility_score · fairness_score · spotify_playlist_id · spotify_playlist_url · llm_context_json · explanation_json · error_message · created_at
**[MVP] playlist_run_tracks**: id · playlist_run_id · spotify_track_id · spotify_uri · track_name · artist_name · score · reason · position · source · **match_confidence** · **discard_reason**(nullable: not_found/unavailable_in_market/low_match/no_uri/artist_cap)
**[MVP] vibe_check_answers**: id · session_id · user_id · answers_json · derived_preferences_json · created_at
**[MVP] track_context_cache**: id · spotify_track_id · track_name · artist_name · lastfm_track_tags_json · lastfm_artist_tags_json · spotify_artist_genres_json · context_scores_json · confidence · fetched_at
**[FUT] lyrics_analysis_cache**: id · spotify_track_id · track_name · artist_name · lyrics_hash · party_score · sadness_score · romance_score · explicitness_score · aggressiveness_score · motivational_score · confidence · method · analyzed_at
**[MVP-estrutura/FUT-uso] member_track_feedback**: id · user_id · playlist_run_id · spotify_track_id · liked · disliked · more_like_this · never_again · created_at
**[MVP-estrutura/FUT-uso] playlist_feedback**: id · user_id · playlist_run_id · representation_score · satisfaction_score · comments · created_at

## 6. Rotas

**Auth:** `GET /auth/login` · `GET /auth/callback` · `POST /auth/logout` · `GET /auth/me`
**Rooms:** `POST /rooms` · `POST /rooms/{code}/join` · `GET /rooms/{code}` · `PUT /rooms/{code}/context` · `PUT /rooms/{code}/mode` · `POST /rooms/{code}/generate` · `GET /rooms/{code}/result`
**Vibe Check:** `GET /rooms/{code}/vibe-check` · `POST /rooms/{code}/vibe-check`
**Music data:** `GET /me/top` · `POST /me/refresh-music-snapshot`
**Feedback:** `POST /playlist-runs/{id}/tracks/{track_id}/feedback` · `POST /playlist-runs/{id}/feedback`
**Debug [opcional]:** `GET /rooms/{code}/debug/scoring`

Guardas: `generate` exige **host**; todas as rotas de sala exigem **membro** (senão 403). `generate` retorna **409** se `status = generating`.

**Atualização da sala (MVP):** o frontend faz **polling a cada 3–5s** em `GET /rooms/{code}` para lista de membros, estado do Vibe Check e status de geração. WebSocket/SSE ficam como evolução futura.

## 7. Pipeline de recomendação (`POST /rooms/{code}/generate`)

0. **Generation Lock / idempotência:** validar que `music_sessions.status != generating`; senão retornar 409 (geração em andamento). Marcar `status = generating` e criar `playlist_run(status=running)` numa transação. Ao final: `completed`/`failed`; **retry controlado** permitido se `failed`. Isso evita playlists duplicadas por cliques repetidos no "Gerar".
1. Validar que o usuário é membro; que é host p/ gerar.
2. Buscar membros da sessão.
3. Buscar/atualizar `user_music_snapshots` dos membros.
4. LLM interpreta ocasião/descrição → JSON estruturado (Context Layer).
5. Agregar `derived_preferences_json` do Vibe Check (média/união entre membros).
6. Montar **pool de candidatas**: top tracks dos membros + top tracks de artistas fortes + (se usado) sugestões contextuais do LLM resolvidas via Spotify Search + (FUT) faixas-ponte entre subgrupos.
7. **Enriquecer** cada candidata: tags Last.fm da faixa → do artista → gêneros Spotify → popularidade → (opcional) letras. Gravar em `track_context_cache` com `context_score` + `confidence`.
8. Score **individual** por usuário.
9. Score de **grupo**.
10. Aplicar `rejection_penalty`.
11. Aplicar **fairness constraints** (representação mínima por membro).
12. Selecionar faixas finais.
13. **Playlist Experience Sequencer**.
14. **Resolver faixas via Spotify Search com o token do HOST** (garante market do host); checar **disponibilidade no mercado**; descartar sem URI válida/indisponível/low_match, gravando `discard_reason`. Aplicar cap de 2/artista.
15. Criar playlist **privada** no Spotify do host + add tracks.
16. Salvar `playlist_runs` + `playlist_run_tracks` (com `reason`, `source`, `position`, `match_confidence`, `discard_reason`).
17. Marcar `run.completed`, `session.status = completed`; retornar resultado com explicações.

**Track Matching (Spotify Search):** normalizar título/artista; tratar variantes (`remastered`, `live`, `acoustic`, `sped up`, `deluxe`, `radio edit`); exigir **confiança mínima de match**; em ambiguidade preferir o **mais popular**; salvar `match_confidence` + `source`.

Robustez: LLM inválido/ausente → fallback só consenso+afinidade+popularidade. Last.fm vazio → cascata. Search não acha / indisponível → descarta com motivo, nunca crasha. 429 → cache + retry/backoff.

## 8. Algoritmo de ranking

**Etapa 1 — score individual** `user_track_score(u,t)`:
`0.40*track_affinity + 0.30*artist_affinity + 0.15*genre_or_tag_affinity + 0.10*popularity_fit + 0.05*novelty_fit`

**Etapa 2 — score de grupo** `group_track_score(t)`:
`0.35*avg_user_score + 0.20*min_user_score + 0.15*member_coverage + 0.15*context_match_score + 0.10*diversity_contribution + 0.05*popularity_fit − rejection_penalty`

**Fórmula alternativa com letras** (quando disponível):
`0.30*group_acceptance + 0.25*member_affinity + 0.20*context_tag + 0.10*popularity + 0.05*diversity + 0.10*lyrics_theme`

Métricas calculadas: `group_satisfaction_avg`, `group_satisfaction_min`, `satisfaction_std`, `member_coverage`, `rejection_penalty`, `fairness_score`. **Pesos são iniciais e ajustáveis** (config central `engine/weights.py`). O uso de `min_user_score` (least misery) evita playlists que a média esconde como injustas.

## 9. Vibe Check

Mini-questionário **opcional**, 3–5 perguntas, linguagem divertida, situações sociais. Se pular, o sistema segue com Spotify + contexto do host + motor. Captura o **humor do momento** (não preferência permanente).

Exemplo: *"A festa começou e alguém colocou uma música que ninguém conhece. Você: A) Dá chance se a vibe for boa. B) Pede logo um hit. C) Adora descobrir. D) Finge que curtiu mas já quer pular."* → mapeia `novelty_preference`, `familiarity_preference`, `skip_risk_tolerance`.

Variáveis derivadas (`derived_preferences_json`): `energy_preference`, `dance_preference`, `sadness_tolerance`, `explicitness_tolerance`, `veto_strength`, `fairness_preference`, `nostalgia_preference`, `discovery_preference`, `popularity_preference`, `novelty_preference`, `familiarity_preference`, `skip_risk_tolerance` (0..1).

Influência no ranking: prefere hits → ↑popularidade; aceita descoberta → ↑novidade; evita tristeza → penaliza tags tristes; veto forte → ↑rejection_penalty; valoriza justiça → ↑representação mínima. MVP: perguntas fixas (ou simples por ocasião). **[FUT]** adaptativo por ocasião (festa/estudo/viagem/academia/churrasco).

## 10. Mood & Context Scoring Layer

O LLM transforma o pedido humano em **critérios estruturados** — não decide humor de música sozinho. Saída esperada:
```json
{ "occasion":"festa", "target_mood":["happy","upbeat","party"], "energy_level":"high",
  "familiarity":"medium_high", "positive_tags":["party","dance","pop","funk","summer","upbeat"],
  "negative_tags":["sad","slow","melancholic","ambient","sleep"],
  "avoid":["músicas muito lentas","músicas tristes","clima introspectivo"] }
```
Fontes (ordem): Last.fm tags da faixa → tags do artista → gêneros/artistas Spotify → Vibe Check → letras (opcional) → regras simples → fallback por consenso do grupo. Cada faixa recebe `context_score` + `confidence` + `source`.

## 11. Last.fm Tag Layer

Fonte **auxiliar**, não dependência absoluta. Cascata: (1) tags da faixa (artist+track) → (2) tags do artista → (3) gêneros Spotify + outros sinais → (4) consenso+afinidade+popularidade. Positivas p/ festa: party, dance, happy, upbeat, pop, funk, summer, electronic. Negativas: sad, acoustic, melancholic, ambient, sleep, depressive, slow. Cache obrigatório em `track_context_cache` com `confidence` (`lastfm_track_tags` > `lastfm_artist_tags_fallback` > `spotify_genres`).

## 12. Lyrics Theme Classifier (opcional / extra acadêmico)

**Sincero:** letra serve p/ **tema/tom textual**, **não** para prever danceability/energy/valence (dependem de áudio). Classifica: festa, tristeza, romance, agressividade, explícito, motivacional, relaxante, nostalgia, verão/praia, dança. Abordagem: (1) baseline por regras/dicionários → (2) evolução TF-IDF + LogReg/SVM → (3) LLM só fallback ambíguo, offline, nunca principal em tempo real → (4) cache obrigatório (`lyrics_analysis_cache`). **Peso baixo/médio** no ranking; nunca decide sozinho.

## 13. Fair Group Optimization

Não usar média simples (ex.: A=10,B=10,C=1 → média 7 mas C odeia). Otimização com restrições:
- Tela de resultado mostra **representação por membro** (ex.: Micael 82%, Ana 76%, Pedro 71%, Lucas 79%).
- Cada membro contemplado por ≥ X faixas quando possível.
- Nenhum membro muito abaixo da média sem justificativa.
- Maioria não esmaga minoria (least misery + coverage).
Se alguém ficou muito baixo → correção na seleção final (troca marginal por faixa que sobe o mínimo sem derrubar o grupo).

**Rejeições explícitas** (Vibe Check ou campo simples): evitar tristes/explícitas/lentas, gêneros/artistas específicos, muito desconhecidas → geram `blocked_genres`, `blocked_artists`, `negative_tags`, `veto_strength`, `rejection_penalty`. Regra: alta rejeição por alguém derruba muito a faixa mesmo agradando outros.

**[FUT] Group Taste Clustering:** detectar subgrupos (pop/funk × rock/indie × eletrônico) e alternar consenso geral / faixas por subgrupo / faixas-ponte. Se sobrar tempo, versão simples por similaridade entre usuários.

## 14. Modos de consenso

1. **Democrático** — todos iguais. **[MVP]**
2. **Festa Segura** — conhecidas, alta aceitação, baixa rejeição. **[MVP]**
3. **Descoberta** — consenso + novas/nicho. **[MVP se der tempo]**
4. Host + Grupo — leve prioridade ao host. **[FUT]**
5. Menor Rejeição — minimiza faixas que alguém odiaria. **[FUT]**
6. Ponte Musical — grupos divergentes, faixas intermediárias. **[FUT]**

Modo = perfil de pesos/restrições aplicado sobre o mesmo pipeline.

**Controle de popularidade/descoberta** (do Vibe Check ou host): só conhecidas / mistura / descobrir. Festa grande ↑popularity; viagem equilíbrio; estudo sem hit; descoberta ↑novelty; Festa Segura ↓obscuras. Evitar popularity bias: popularidade é variável ajustável + `diversity_score`.

## 15. Playlist Experience Sequencer

Não basta o top-N: precisa de fluxo. Festa: aquecimento → subida → pico → manutenção → respiro → fechamento. Regras MVP: sem 2 faixas do mesmo artista seguidas; começar por alta aceitação; faixas arriscadas no meio; alternar estilos próximos; populares nos picos; evitar blocos longos do mesmo gênero.

## 16. Feedback e evolução futura

**Feedback pós-playlist:** like / dislike / more_like_this / never_again por faixa + representação 0–5 + satisfação. MVP coleta e persiste (`member_track_feedback`, `playlist_feedback`); uso no ranking é futuro.

**Roadmap:** (1) aprendizado com feedback (pesos personalizados) · (2) Learning to Rank · (3) bandits contextuais · (4) perfis persistentes opcionais · (5) grupos persistentes · (6) integrações (link/QR/histórico/export) · (7) sequenciamento avançado por energia · (8) avaliação offline (com/sem Vibe Check, Last.fm, fairness).

## 17. Plano de implementação (4 semanas)

**Semana 1 — Fundação + Auth + Spike técnico:** setup FastAPI + React + Docker Compose (Postgres) + SQLAlchemy/Alembic; app no Spotify Dashboard; OAuth completo (com `state`); salvar user + tokens (criptografados); refresh central + tratamento de reauth; `/auth/me`; tela de login; buscar top tracks/artists.
**Spike técnico (antes do motor):** validar no app recém-criado — top tracks/artists, Search, criar playlist, add playlist items, e o **limite de 5 usuários**. **Documentar resultados no README** antes de seguir.

**Semana 2 — Salas + Vibe Check básico:** criar/entrar por código; anti-duplicidade; membros; papéis host/member; telas Home e Room; ocasião + descrição; Vibe Check opcional (perguntas fixas) → `derived_preferences_json`.

**Semana 3 — Motor determinístico + playlist real:** cache de tops; compatibilidade; Individual Taste Modeling; score individual + grupo; fairness_score inicial; rejection_penalty; modos Democrático e Festa Segura; criar playlist real + add tracks; tela de resultado; justificativas simples. **Marco: funciona sem IA.**

**Semana 4 — IA + contexto + Last.fm + polimento:** LLM → JSON de contexto; Last.fm track/artist tags; `context_tag_score`; fallback em cascata; `track_context_cache`; Sequencer simples; feedback pós-playlist; testes automatizados; README final; roteiro de demo.

**Extra:** Lyrics Classifier (regras → TF-IDF/LogReg) + `lyrics_analysis_cache`; Group Taste Clustering; Modo Ponte; base p/ Learning to Rank.

## 18. Testes (pytest)

Motor puro (sem rede): Jaccard; compatibilidade com listas vazias; grupo de 1 membro; `group_track_score`; `rejection_penalty`; `fairness_score`; seleção com representação mínima; limite por artista; remoção de duplicadas; Vibe Check derivando preferências. Clients/fallbacks (mockados): parsing do JSON do LLM; fallback LLM inválido; fallback Last.fm vazio; fallback Search não acha; refresh token. API: não-membro → 403; entrada duplicada em sala; **`generate` concorrente → 409 (Generation Lock)**; **refresh falho → reauth_required + redirect**; **track matching** (normalização de variantes remastered/live/sped up, confiança mínima, desempate por popularidade); **faixa indisponível no mercado → descartada com `discard_reason`**; cap de 2/artista.

## 19. Riscos e mitigações

1. Spotify restringir endpoints → não depender de Recommendations/Audio Features/Analysis.
2. Access token expira (1h) → refresh central no SpotifyClient. **Refresh token pode expirar (meses)** → detectar falha de refresh, marcar `reauth_required_at` e redirecionar a novo login.
11. **Limite de 5 usuários (Development Mode) + exigência de Premium** → pré-cadastrar contas Premium na demo; planejar salas de 1–5 membros; **solicitar Extended Quota Mode** para escalar (aprovação depende do Spotify — iniciar cedo).
12. **Faixas indisponíveis por mercado / match errado** → resolver com token do host, checar disponibilidade, exigir `match_confidence` mínima, descartar com `discard_reason`.
13. **Cliques repetidos em "Gerar"** → Generation Lock (`status=generating`, 409) + `playlist_run` idempotente com retry.
3. Last.fm sem tags → cascata (artista → gêneros → letras → consenso).
4. LLM alucinar música → tudo resolvido via Search; ignora o que não achar.
5. LLM JSON inválido → schema/structured output + validação + fallback.
6. Letras difíceis de obter/licenciar → Lyrics Classifier opcional/offline/acadêmico.
7. Análise de letras pesada → TF-IDF + LogReg/SVM + regras + cache; LLM só fallback.
8. Questionário chato → Vibe Check opcional, curto, divertido.
9. Grupo divergente → least misery + fairness + modos + faixas-ponte.
10. Só hits óbvios → controle popularidade/descoberta + `diversity_score`.

## 20. Arquivos/pastas a criar

```
backend/
  app/
    main.py
    config.py            # settings, chaves (env), pesos default
    db/                  # session, base, models.py
    api/                 # auth.py, rooms.py, vibe_check.py, music.py, feedback.py, debug.py
    services/            # room_service, generation_service (orquestra o pipeline)
    engine/              # taste.py, scoring.py, fairness.py, sequencer.py, weights.py  (puro/testável)
    clients/             # spotify_client.py, llm_client.py, lastfm_client.py, crypto.py
    schemas/             # pydantic (context JSON, vibe check, requests/responses)
  alembic/
  tests/
  pyproject.toml
frontend/                # Vite React: Login, Home, Room (contexto+VibeCheck), Result; apiClient
docker-compose.yml       # Postgres
.env.example             # SPOTIFY_CLIENT_ID/SECRET, REDIRECT_URI, DATABASE_URL, ANTHROPIC_API_KEY, LASTFM_API_KEY, FERNET_KEY
README.md                # atualizar
```

## Verificação (end-to-end)

- **Auth:** login abre consent oficial; tokens salvos **criptografados**; tops no front batem com o app oficial; forçar expiração → refresh automático; token nunca chega ao frontend.
- **Salas:** entrar por código; entrar 2× bloqueado; sala alheia via URL → 403; só host gera.
- **Vibe Check:** pular → geração segue; responder → `derived_preferences_json` correto e influencia o ranking (ex.: baixa `sadness_tolerance` derruba faixas com tag `sad`).
- **Motor:** grupo sem interseção → 0% sem crash; fairness mostra representação por membro; veto forte derruba faixa mesmo popular.
- **Playlist:** aparece **de fato** no Spotify do host; faixas inexistentes ignoradas; Sequencer não repete artista seguido.
- **IA/contexto:** "festa muito alegre" vs "estudo relaxante" muda tags/candidatas; LLM inválido → fallback sem quebrar; Last.fm vazio → cascata registra `confidence` menor.
- **Testes:** `pytest` verde para engine (fairness/rejection/coverage), fallbacks e guardas de API.

---

## Execução local — Fundação técnica (PB-01)

Esta seção cobre **apenas** a fundação técnica (PB-01): frontend Vite, backend
FastAPI, PostgreSQL e migrações. Auth Spotify, salas, motor, LLM e Last.fm são
histórias posteriores.

### Pré-requisitos

| Ferramenta | Versão de referência (validada) |
|---|---|
| Python | 3.11.9 (use `python3`) |
| Docker + Compose | 29.6.1 / Compose v5.2.0 |
| Node.js + npm | ≥ 18 (necessário para o frontend) |

### 1. Variáveis de ambiente

```bash
cp .env.example .env
```

O `.env` é ignorado pelo Git. Os **defaults locais já funcionam** para banco e cache
(`DATABASE_URL`, `MUSIC_SNAPSHOT_TTL_DAYS=7` e `SPOTIFY_TOP_ITEMS_LIMIT=50`). As chaves de Spotify /
Anthropic / Last.fm ficam **vazias no exemplo** e só devem ser preenchidas no `.env` local quando a
integração correspondente for exercitada. Nunca comite segredos.

No PB-08, `GET /me/top` reutiliza o snapshot fresco e
`POST /me/refresh-music-snapshot` força uma nova coleta. Ambos aceitam `time_range` como
`short_term`, `medium_term` (padrão) ou `long_term`. Em rate limit, o último snapshot disponível é
reutilizado; sem cache, a API devolve 429 com `Retry-After`.

### 2. Aplicação completa com Docker Compose

```bash
docker compose up --build        # sobe banco, backend e frontend
docker compose ps                # os três serviços devem ficar "healthy"
```

- Frontend: <http://localhost:5173>
- API: <http://localhost:8000>
- Docs (Swagger): <http://localhost:8000/docs>

O backend espera o PostgreSQL ficar saudável e aplica `alembic upgrade head` antes de iniciar. O
frontend, por sua vez, espera a API responder. Os diretórios de código são montados nos containers,
portanto Vite e Uvicorn recarregam alterações durante o desenvolvimento.

Para subir somente a infraestrutura e executar as aplicações diretamente no host, use
`docker compose up -d db` e siga as seções abaixo.

### 3. Backend no host (opcional)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head             # aplica a migração inicial (tabela users)
uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000> · Docs (Swagger): <http://localhost:8000/docs>

### 4. Frontend no host (opcional)

```bash
cd frontend
npm install
npm run dev                      # sobe em http://localhost:5173
```

A tela inicial mostra o status de conectividade Frontend → Backend → Banco.

### Verificação

```bash
# Saúde do backend (liveness) e conexão com o Postgres (readiness)
curl http://localhost:8000/health      # {"status":"ok",...}
curl http://localhost:8000/health/db   # {"status":"ok","database":"ok"}

# Ciclo de migração do Alembic (a partir de backend/, com a venv ativa)
alembic upgrade head     # cria a tabela users
alembic downgrade base   # reverte (remove a tabela users)
alembic upgrade head     # reaplica

# Testes automatizados do backend (não dependem do Postgres)
pytest
```

### Encerramento

```bash
# backend/frontend: Ctrl+C nos respectivos terminais
docker compose down       # para os serviços (mantém banco e node_modules nos volumes)
docker compose down -v    # para os serviços e APAGA os volumes locais
```
