# Mapa de Trabalho — Divisão dinâmica por Sprint (Vibe Check)

**Modelo adotado:** sem trilhas fixas. A equipe segue o plano da Sprint ativa e identifica os PBs
livres (dependências satisfeitas e sem dono). Para os agentes de implementação, vale o portão do
`AGENTS.md`: **um PB por vez**, seguido de QA antes do próximo. 🅰 = você (Codex+Claude) · 🅱 =
colega (Gemini).

Fontes: [`../produto/BACKLOG_PRODUTO.md`](../produto/BACKLOG_PRODUTO.md) · [`PLANO_EXECUCAO.md`](PLANO_EXECUCAO.md).

> **Numeração atualizada (backlog v2):** o antigo PB-14 foi dividido em **PB-14 (correspondência)** +
> **PB-15 (criação da playlist)**, e os demais desceram uma posição (Resultado = PB-16, … Feedback =
> PB-20). "Qualidade/robustez/documentação" deixou de ser PB e virou a **Definition of Done** (aplica
> a todos os PBs). PB-21–24 são expansão pós-MVP (Sprint 5), PB-25–29 formam a Sprint 6 e
> PB-30–34 planejam a biblioteca musical ampliada da Sprint 7.

## 1. Fluxo de coordenação (o de todo dia)

```bash
git checkout main && git pull
./scripts/orquestrar.sh --list          # vê o que está 🟢 LIVRE, 🛠 em impl, ✅ feito, 🔒 esperando
```

1. Escolha um PB 🟢 LIVRE que o outro ainda não pegou.
2. Avise no chat: *"peguei o PB-30"* (o `--pb` já carimba seu nome como dono).
3. Branch por PB → `./scripts/orquestrar.sh --pb PByy --profile <seu-perfil>` → implementa+testa → QA → PR.
4. Terminou? Volta ao `--list`.

## 2. Regra de ouro pra não colidir nos arquivos

Antes de pegar, **evitem escolher dois PBs que tocam o mesmo módulo** ao mesmo tempo:

| PBs | Tocam principalmente |
|---|---|
| PB-04, PB-05, PB-06 | `api/rooms.py`, `services/room_service.py`, `frontend/` (Sala) |
| PB-08 | `api/music.py`, `clients/spotify_client.py` |
| PB-09, PB-10, PB-11, PB-12 | `backend/app/engine/*` (motor puro) |
| PB-13, PB-14, PB-15 | `services/generation_service.py`, `clients/spotify_client.py` |
| PB-17, PB-18 | `clients/{llm_client,lastfm_client}.py` |
| PB-19 | `backend/app/engine/*` (sequenciamento) |
| PB-07, PB-16, PB-20 | `frontend/` + `api/` (Vibe Check / Resultado / Feedback) |
| PB-25, PB-30, PB-32 | `clients/spotify_client.py`, autenticação e `services/music_service.py` |
| PB-31 | modelos, repositórios e migrações da biblioteca musical pessoal |
| PB-26, PB-33 | `backend/app/engine/*` (pool, perfil ponderado e pontuação) |
| PB-27, PB-34 | geração, API de música e estados exibidos no frontend |

⚠️ **Migrações Alembic:** vários PBs criam tabelas. Quem for criar migração **avisa antes** e
encadeia na revisão mais recente (`down_revision`) — senão dá dois *heads* no merge.

## 3. Dependências — o que libera o quê

```
PB-01 ─ PB-02 ─┬─ PB-03
               ├─ PB-04 ─┬─ PB-05 ─┬─ PB-07
               │         ├─ PB-06 ─┤
               │         │         ├─ PB-10 ← (tb. PB-09)
               │         │         ├─ PB-13 ← (tb. PB-05, PB-11)
               │         │         └─ PB-17 ← (tb. PB-10)
               └─ PB-08 ─── PB-09 ─── PB-10 ─ PB-11 ─┬─ PB-12 ─┬─ PB-14 ← (PB-02,13) ─ PB-15
                                                     └─ PB-13 ─┘        │
PB-14 ─ PB-15 ─┬─ PB-16 ← (tb. PB-13) ─ PB-20                           │
               └─ PB-19 ← (tb. PB-12)                                   │
PB-10 ─ PB-17 ─ PB-18                                 DoD (qualidade): aplica a todos os PBs

PB-30 ─ PB-31 ─ PB-32 ─ PB-33 ─ PB-34
```

O `--list` mostra em tempo real o que está 🟢 LIVRE. A Sprint 7 é majoritariamente serial porque
cada etapa firma o contrato consumido pela seguinte; atividades paralelas não autorizam começar
outro PB antes do portão de QA.

## 4. Sprints (referência de escopo — a divisão é dinâmica)

| Sprint | PBs | Pts |
|---|---|---:|
| 1 | PB-01, PB-02, PB-04, PB-05, PB-06, PB-08 | 25 |
| 2 | PB-09, PB-10, PB-11, PB-12, PB-13 | 24 |
| 3 | PB-07, PB-14, PB-15, PB-16, PB-17 | 23 |
| 4 | PB-03, PB-18, PB-19, PB-20 | 14 |
| 5 (pós-MVP) | PB-21, PB-22, PB-23, PB-24 | 18 |
| 6 (em QA) | PB-25, PB-26, PB-27, PB-28, PB-29 | 24 |
| 7 (em andamento) | PB-30, PB-31, PB-32, PB-33, PB-34 | 24 |

Não precisa fechar 50/50 exato por Sprint. Cada pessoa puxa o próximo PB livre depois do QA do seu
PB atual. A Sprint 6 segue em QA paralelo por decisão do Product Owner; a ordem da Sprint 7 é
`PB-30 → PB-31 → PB-32 → PB-33 → PB-34`.
