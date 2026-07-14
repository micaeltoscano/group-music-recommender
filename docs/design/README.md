# Handoff: Vibe Check — Group Music Recommender

## Overview
UI for "Vibe Check," a group music-recommendation web app (Spotify OAuth login → create/join an ephemeral room by short code → set occasion + consensus mode → optional Vibe Check quiz → a "Preference Negotiation Engine" generates a real Spotify playlist → fairness-explained result screen → post-playlist feedback).

## About the Design Files
The bundled file, `vibe-check-prototype.html`, is a **design reference** — an interactive HTML/JS prototype built to show layout, states, and flow. It is not production code. The task is to **recreate this design in the target codebase's actual stack** (per the project's `README.md` / `docs/`: FastAPI backend + React/Vite frontend), using React components, real routing, and real API calls — not by embedding or copying this HTML file directly.

To view all states, open the file in a browser: a floating pill nav at the bottom (LOGIN / HOME / SALA / VIBE / GERANDO / RESULTADO / FEEDBACK) jumps between every screen. The "SALA" screen has a secondary A/B/C switcher (top-right of that screen) for three lobby layout variants.

## Fidelity
**High-fidelity.** Colors, type, spacing, and copy are final-intent; recreate pixel-close using the target codebase's component library/CSS approach (Tailwind, CSS modules, styled-components, whatever the frontend already uses).

## Design Tokens

**Colors**
- Background (base): `#14130d`
- Surface/card: `#1e1c13`
- Surface border: `#35331f` (secondary border `#3a382a`)
- Accent (primary, "signal orange"): `#ff5b1c` / hover `#ff7a45`
- Accent secondary (olive, "safe/positive"): `#a8ae6d`
- Text primary: `#f2ecdb`
- Text muted: `#a8a48c` / `#8b8871` / dimmest `#5b5945`
- Member avatar palette (rotating): `#ff5b1c`, `#a8ae6d`, `#e0b84a`, `#c96f4a`, `#8fae8a`

**Typography**
- Display/headings: `Chakra Petch`, weights 600–700, tight letter-spacing (~0.01–0.06em), used for all titles/numbers
- Body/UI/mono labels: `IBM Plex Mono`, weights 400–600
- Both loaded from Google Fonts
- Eyebrow/label text: 10–11px, uppercase, letter-spacing 0.14–0.22em, color `#5b5945` or `#8b8871`

**Shape & elevation**
- Card radius: 16–20px; buttons/pills: 12px or fully round (999px) for chips/avatars
- Cards: 1px solid border in `#35331f`, no shadow (flat); the orange hero/login card uses `box-shadow: 0 24px 80px rgba(255,91,28,0.18)`
- Thin 1px hairline separators (`#2b2919`) between header and content, and above the footer CTA band

**Motif**
- A 4-bar equalizer glyph (bars of varying height, `animation: eq` scaleY loop) is the brand mark, reused in the header logo and inside the orange login/hero card
- Subtle fixed full-screen scanline overlay (repeating 1px lines, 4.5% opacity) for retrofuturist texture — toggleable, off by default in print/export contexts
- Terminal-style bracket labels above section headers, e.g. `[ VC-01 · LOGIN MODULE ]`, `[ VC-01 · ROOM MODULE ]`

## Screens / Views

### 1. Login / Landing
Combined marketing landing + Spotify OAuth entry point.
- **Hero**: two-column, left = eyebrow label + big headline "A playlist que **representa** o grupo inteiro." (accent word in orange) + subhead paragraph + primary button "ENTRAR COM SPOTIFY ▶" + inline lock-icon reassurance text about token encryption. Right = orange preview card mocking a live room (code, occasion, member count, mode, a satisfaction bar at 87%).
- **Credibility strip**: row of 4 uppercase bullet claims (justiça, todo mundo ouvido, zero drama, feito para grupos).
- **"Como funciona"**: centered eyebrow + heading, then a 4-column grid of numbered steps (01 Crie a sala, 02 Grupo entra, 03 Motor negocia, 04 Playlist real), each a card with big orange number, title, description.
- **Feature grid**: 3 cards (⚖ Justiça não média, 🎯 Contexto de verdade, 🛡 Vetos respeitados), icon + title + description.
- **Final CTA band**: full-width darker section (`#1a1810`, top border), centered headline + Spotify CTA button repeated.

### 2. Home
Post-login dashboard.
- Greeting row: circular avatar with initials + "Bom te ver, Luiza." + sync status subtext.
- Two side-by-side cards (400px each): "01 · CRIAR SALA" (host flow, solid orange CTA) and "02 · ENTRAR COM CÓDIGO" (code input + outlined olive CTA).

### 3. Sala / Lobby (3 variants, switchable)
Shared header row: eyebrow label + a small A/B/C variant switcher (3 square buttons).
- **Variant A — Control panel**: 2-column grid. Left column: orange "room code" card with expiry timer + copy button, then a member list card (avatar, name, HOST badge, VIBE ✓ badge). Right column: occasion chip picker + free-text description input, consensus-mode 3-up card picker, a Vibe Check progress card (bar + status + CTA), and a full-width primary "GERAR PLAYLIST ▶▶" button.
- **Variant B — Hero minimal**: centered giant room code (96px), member avatar row below, a row of pill "stat" chips (occasion/mode/vibe %), then two CTA buttons (outlined Vibe Check + solid Generate).
- **Variant C — Mission control**: 3-column grid: left = compact member list, center = code card (bordered in orange) + Generate + Vibe Check buttons, right = "recent activity" log list with timestamps.

### 4. Vibe Check (quiz)
Centered card, max-width ~620px.
- Progress: "PERGUNTA n/3" label + 3 segmented dots (filled = answered).
- Question headline, then a vertical stack of 4 answer buttons, each with a lettered badge (A–D) + option text; hover state highlights border orange.
- Footer row: "pular o vibe check →" link (left) and a small note that answers feed the algorithm (right).

### 5. Gerando (generation in progress)
Centered card.
- Header: "Negociando a playlist…" + live percentage (large, orange).
- Progress bar (orange fill, animated width).
- A terminal-style log panel (dark, monospace, `$`-prefixed lines) that reveals pipeline steps one at a time (fetching top tracks → LLM context → candidate pool → scoring → rejection penalty → fairness → sequencing → creating playlist), with a blinking cursor block at the end.
- Footer note about the engine balancing taste/context/fairness/rejection.

### 6. Resultado (result)
Wide layout, max-width 1100px.
- Header row: big grade badge ("A−"), headline "ÓTIMO VIBE!" + subtext, spacer, and two actions (outlined "DAR FEEDBACK", solid "ABRIR NO SPOTIFY ▶").
- 4-up metric card row (satisfação do grupo, representação mínima, descobertas, rejeições evitadas) — label/value/note per card.
- 2-column layout: left = the playlist itself (track rows grouped by "phase" headers like AQUECIMENTO/PICO/FECHAMENTO, each row: position, artwork placeholder, name/artist/source, short reason text, "FAIR n%" badge). Right column = "representação por membro" card (name + % + colored progress bar per member), a collapsible "POR QUE ESSA PLAYLIST É JUSTA?" explainability card (bulleted plain-language fairness reasons), and a dashed "↻ REGENERAR PLAYLIST" button.

### 7. Feedback
Centered card.
- **Unsent state**: headline "Como foi a playlist?", per-track rows with CURTI/PULAR toggle buttons, a 0–5 "a playlist te representou?" numeric scale (6 buttons), an optional comment textarea, and a primary "ENVIAR FEEDBACK ▶" button.
- **Sent state**: confirmation card (green check, "Valeu, Luiza!", thank-you copy) with a button back to the result screen.

## Interactions & Behavior
- Bottom floating pill nav (prototype-only, remove in production) jumps between the 7 screens instantly.
- "GERAR PLAYLIST" starts a ~5s simulated generation: an interval reveals one log line roughly every 620ms, then auto-navigates to Resultado.
- Vibe Check: answering any option on question 3 marks the quiz done and returns to the lobby; "pular" skips straight to lobby.
- Occasion chips, consensus-mode cards, and the lobby A/B/C switcher are simple selected/unselected toggle state (single-select).
- Explainability card ("POR QUE...") is a collapsible disclosure, open by default.
- Feedback per-track like/dislike buttons are independent toggles per track; submitting flips the panel to a sent confirmation state.
- All transitions are instant (no page-level animation) except the equalizer bars (continuous CSS loop) and the generation log/progress bar.

## State Management (for real implementation)
Map cleanly to the PRD's actual backend: current screen ≈ route; room code/members/occasion/mode ≈ `GET /rooms/{code}` polling; Vibe Check answers ≈ `POST /rooms/{code}/vibe-check`; generation ≈ `POST /rooms/{code}/generate` (poll or stream status: running → completed/failed, matching the "Generation Lock" behavior in the spec — disable the button and show this loading screen while `status = generating`); result ≈ `GET /rooms/{code}/result`; feedback ≈ `POST /playlist-runs/{id}/tracks/{track_id}/feedback` and `POST /playlist-runs/{id}/feedback`.

## Assets
No external images — avatars are colored initials circles; track "artwork" is a generated diagonal-stripe placeholder (`repeating-linear-gradient`) in the member's/track's accent color, meant to be replaced with real Spotify album art. Icons are plain emoji/unicode glyphs (⚖ 🎯 🛡 🔒 ▶ ✓), no icon library used.

## Files
- `vibe-check-prototype.html` — full interactive prototype, all 7 screens + 3 lobby variants, in one file.
- `screenshots/` — static PNG of each screen (login/landing, home, sala/lobby variant A, vibe check, gerando, resultado, feedback) for quick reference without opening the HTML.
