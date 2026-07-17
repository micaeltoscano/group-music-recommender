# Começe aqui 👋 — como a gente vai trabalhar juntos

Bem-vindo ao **Vibe Check**! Este texto explica, **do zero**, como montamos o projeto pra nós dois
desenvolvermos em paralelo, cada um com sua IA, sem pisar no pé do outro. Leia até o fim uma vez —
depois é só consultar.

---

## 1. O que é o projeto

Vibe Check é um app onde um grupo entra numa sala, define o clima/ocasião, e um **motor de negociação**
gera uma **playlist real no Spotify** que representa o grupo todo (com justiça, vetos respeitados, etc.).
Stack: **FastAPI** (backend) + **React/Vite** (frontend) + **Postgres**.

## 2. A ideia central de como trabalhamos

O trabalho é dividido em **PBs** (Product Backlogs = pequenas histórias, ex.: "PB-04 — criar sala").
Cada PB é uma fatia completa: **código + testes**. A gente trabalha assim:

- **Cada um pega por exemplo 2 PBs por vez** e faz eles inteiros. Sem trilha fixa, sem ordem entre nós: quem
  está livre puxa o próximo PB que estiver **livre**.
- Nós dois nunca conversamos "direto" — a gente se coordena **pelo próprio repositório** (git + um
  documento de plano). O git é a fonte da verdade.
- Cada PB é validado por um **QA** (testes) antes de ser considerado pronto.

**Você usa o Gemini**; eu uso Codex + Claude. Cada ferramenta tem um arquivo-guia na raiz do repo que
ela lê sozinha (o seu é o **`GEMINI.md`**). Não precisa decorar nada — as regras estão lá.

## 3. Os conceitos que você precisa saber

- **PB** — uma história pequena. Você implementa **uma por vez**, com os testes dela.
- **Sprint** — um grupo de PBs. A gente trabalha só na **Sprint ativa**.
- **O plano** (`docs/planejamento/PLANO_EXECUCAO.md`) — a "memória" do projeto: lista os PBs, o
  **status** de cada um e as **dependências**. É a fonte da verdade do que fazer.
- **Status de um PB** — a primeira palavra do campo `Status` no plano diz em que pé está:

  | Status | Significado |
  |---|---|
  | `A-FAZER` | ninguém começou |
  | `EM-IMPLEMENTACAO` | alguém está fazendo (tem um dono `@nome`) |
  | `AGUARDANDO-QA` | implementado, falta validar |
  | `REPROVADO` | o QA achou defeito; precisa corrigir |
  | `VALIDADO` | pronto ✅ |
  | `BLOQUEADO` | travado por dependência/coisa externa |

- **Dependências** — alguns PBs só podem começar depois que outros estão `VALIDADO`. Ex.: o PB-05
  depende do PB-04. **Você não precisa decorar isso** — a ferramenta te avisa e não deixa começar
  cedo demais.

## 4. O que instalar (uma vez)

- **Docker**, **Python 3.11**, **Node 18+**.
- **Gemini CLI** (logado na sua conta).

## 5. Rodar a aplicação (pra ver funcionando)

Com Docker Compose (detalhes no `README.md`):

```bash
docker compose up --build
```

Isso sobe PostgreSQL, backend e frontend. Acesse o frontend em <http://localhost:5173> e a
documentação da API em <http://localhost:8000/docs>.

Se preferir executar backend e frontend diretamente no host, use 3 terminais:

```bash
# Terminal 1 — banco de dados
docker compose up -d db

# Terminal 2 — backend (dentro de backend/, com a venv)
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000     # http://localhost:8000/docs

# Terminal 3 — frontend (dentro de frontend/)
npm install
npm run dev                                    # http://localhost:5173
```

## 6. O dia a dia — como fazer um PB (o passo a passo principal)

```bash
# 1. Atualize e veja o que está livre
git checkout main && git pull
./scripts/orquestrar.sh --list --profile gemini
```

O `--list` mostra um painel: o que está **🟢 LIVRE**, **🛠 em implementação** (com dono), **✅ feito**
e **🔒 esperando** dependência.

```bash
# 2. Escolha 1–2 PBs 🟢 LIVRE e AVISE no nosso chat quais pegou
#    (ex.: "peguei o PB-08")

# 3. Crie uma branch e rode o orquestrador mirando o PB
git checkout -b feat/SPRINT-01/PB08
./scripts/orquestrar.sh --pb PB-08 --profile gemini
```

O que o `--pb` faz: **reivindica o PB no seu nome** (pra eu não pegar o mesmo), confere as
dependências, aí o Gemini **implementa** e depois faz um **passe de QA** (testa e tenta quebrar).
No fim ele marca o status (`VALIDADO` ou `REPROVADO`) e **para** — ele **não** avança pro próximo
sozinho (isso é de propósito, pra não colidir comigo).

```bash
# 4. Deu VALIDADO? Abra um Pull Request pra main. Depois volte ao passo 1 e pegue o próximo livre.
```

💡 Quer testar o fluxo sem chamar a IA e sem alterar nada? Use `--dry-run`:
`./scripts/orquestrar.sh --pb PB-08 --profile gemini --dry-run`

## 7. As regras de ouro (pra não dar problema)

1. **Um PB por vez.** Não adiante PBs futuros.
2. **Não pegue um PB que mexe no mesmo arquivo que o meu** ao mesmo tempo — a tabela de "qual PB
   toca qual arquivo" está em `docs/planejamento/MAPA_TRABALHO.md` §2. Na dúvida, me pergunta.
3. **Antes de criar uma migração Alembic, me avisa** — se nós dois criarmos ao mesmo tempo, dá
   conflito ("dois heads"). A gente encadeia uma na outra.
4. **Frontend sai do design.** Toda tela é recriada a partir de `docs/design/` (screenshots +
   protótipo). Os estilos base (cores, fontes) já estão em `frontend/src/index.css` — use
   `var(--accent)` etc. Mapa de qual tela é de qual PB: `docs/design/development_guide.md`.
5. **Nunca** suba tokens/senhas/segredos no git.
6. **Não** marque nada como `VALIDADO` na mão nem enfraqueça um teste pra ele passar — quem aprova
   é o passe de QA, com testes de verdade.
7. **Não** faça merge direto na `main` sem PR.

## 8. Onde ler mais (mapa da documentação)

- **`GEMINI.md`** (na raiz) — seu guia; o Gemini lê ele sozinho. **Comece por ele.**
- `docs/README.md` — índice de toda a documentação.
- `docs/planejamento/MAPA_TRABALHO.md` — como a gente divide o trabalho + tabela de arquivos.
- `docs/planejamento/PLANO_EXECUCAO.md` — a Sprint ativa, os PBs e o status de cada um.
- `docs/planejamento/PLANO_TESTES.md` — como cada PB deve ser testado.
- `docs/produto/BACKLOG_PRODUTO.md` — o que cada PB precisa entregar (critérios de aceitação).
- `docs/design/` — o visual do frontend (README + `development_guide.md` + screenshots).

---

**TL;DR:** `git pull` → `--list` pra ver o que está livre → avisa qual PB pegou → cria branch →
`--pb PBxx --profile gemini` → o Gemini faz e testa → PR pra main → pega o próximo. Uma dúvida?
Me chama. 🚀
