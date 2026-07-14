# Guia de Desenvolvimento do Frontend — a partir do design

> **Regra central:** toda tela do frontend é construída **a partir do design** desta pasta, na stack
> real do projeto (React + Vite). **Recriar, não copiar** o protótipo. Vale para os modelos do
> Micael (Codex/Claude) e do colega (Gemini).

## Stack real (onde a tela vira código)

- **Frontend:** React + Vite em `frontend/src/` (sem Tailwind; CSS em `frontend/src/index.css`).
- **Backend:** FastAPI em `backend/app/` (a tela consome a API via `frontend/src/apiClient.js`).
- **Roteamento:** `react-router-dom`.

## A base visual já está no código

Os **tokens do design** (cores, fontes, formas do [`README.md`](README.md)) já estão em
[`../../frontend/src/index.css`](../../frontend/src/index.css) como **variáveis CSS** e classes base
(`.btn-primary`, `.btn-outline`, `.pill`, `.eyebrow`, `.card`…). **Use sempre `var(--accent)` etc.
em vez de cores fixas** — assim toda tela sai consistente, independente de quem (ou qual modelo) a fez.

Exemplos: `var(--accent)` (laranja), `var(--accent-2)` (olive), `var(--bg)`, `var(--surface)`,
`var(--text)`, `var(--muted)`, `var(--font-display)` (títulos/números), `var(--font-body)` (corpo/UI).

## Como usar o protótipo

1. Abra [`vibe-check-prototype.html`](vibe-check-prototype.html) no navegador. A barra flutuante
   embaixo (LOGIN / HOME / SALA / VIBE / GERANDO / RESULTADO / FEEDBACK) navega entre todas as telas.
2. Compare com o screenshot correspondente em [`screenshots/`](screenshots/).
3. Recrie a tela em React usando os tokens do `index.css`. **Não** embuta nem copie o HTML do protótipo.

## Mapa: tela do design → PB → arquivo

| Screenshot | Tela | PB | Componente (sugestão) |
|---|---|---|---|
| `01-login-landing.png` | Login / Landing | **PB-02** | `frontend/src/Login.jsx` (existe) |
| `02-home.png` | Home (criar / entrar por código) | **PB-04** | `frontend/src/Home.jsx` |
| `03-sala-lobby.png` | Sala / Lobby (membros, contexto, modo) | **PB-05, PB-06** | `frontend/src/Room.jsx` |
| `04-vibe-check.png` | Vibe Check (quiz) | **PB-07** | `frontend/src/VibeCheck.jsx` |
| `05-gerando.png` | Gerando (loading da geração) | **PB-14/PB-15** | estado da tela Room/Result |
| `06-resultado.png` | Resultado (playlist, fairness, explicação) | **PB-16** | `frontend/src/Result.jsx` |
| `07-feedback.png` | Feedback pós-playlist | **PB-20** | `frontend/src/Feedback.jsx` |

> Fidelidade **alta**: cores, tipografia, espaçamento e textos são intenção final — recrie
> pixel-próximo. Construa **só a tela do PB atual** (não antecipe telas de PBs futuros).

## Fidelidade e privacidade

- Siga os **estados** mostrados no protótipo (vazio, carregando, erro), não só o "happy path".
- A tela de Resultado **não** pode expor rejeições/dados sensíveis de outro integrante (ver PB-15).
