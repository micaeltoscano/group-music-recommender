# Vibe Check

O **Vibe Check** é uma aplicação web que cria playlists coletivas no Spotify sem reduzir o grupo a uma média simples. O sistema combina o histórico musical dos participantes, o contexto do encontro, preferências momentâneas e regras de justiça para gerar uma playlist privada na conta do anfitrião.

> O Spotify conhece o histórico de cada pessoa. O Vibe Check negocia a trilha sonora do momento para o grupo inteiro.

## Principais recursos

- autenticação exclusiva por Spotify OAuth;
- salas efêmeras com código de convite e até cinco participantes;
- biblioteca musical pessoal com Tops e playlists autorizadas;
- contexto da ocasião e modos de consenso;
- Vibe Check opcional, com respostas individuais privadas;
- motor determinístico de afinidade, rejeição e representação;
- enriquecimento contextual com Last.fm e interpretação local com Ollama;
- geração de playlist privada com 20 a 30 faixas no Spotify;
- progresso compartilhado, métricas de justiça e explicações por faixa;
- feedback por música e avaliação geral da playlist.

## Arquitetura

```text
React + Vite
     │ HTTP/JSON + cookie httpOnly
     ▼
FastAPI ─────────────── PostgreSQL
     │
     ├── Spotify Web API
     ├── Last.fm API
     ├── Ollama local
     └── Preference Negotiation Engine
          ├── modelagem de gosto
          ├── contexto e Vibe Check
          ├── pontuação individual e coletiva
          ├── rejeição e justiça
          └── sequenciamento da playlist
```

O backend é dividido em rotas, serviços, clientes externos, persistência e um motor puro em `backend/app/engine`. O motor não acessa rede nem banco de dados diretamente, o que mantém os cálculos determinísticos e fáceis de testar.

![Visão do motor de recomendação](diagrams/arquitetura/02-motor-pne.png)

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | React 18, Vite 6, React Router |
| Backend | Python 3.11, FastAPI, Pydantic |
| Persistência | PostgreSQL, SQLAlchemy, Alembic |
| Integrações | Spotify Web API, Last.fm, Ollama |
| Infraestrutura | Docker, Docker Compose |
| Testes | Pytest |

## Pré-requisitos

Para executar toda a aplicação, você precisa de:

- Docker e Docker Compose;
- uma aplicação cadastrada no [Spotify for Developers](https://developer.spotify.com/dashboard);
- uma chave Fernet para criptografar tokens;
- opcionalmente, uma chave da API do Last.fm;
- opcionalmente, Ollama com o modelo `llama3.1:8b`.

## Execução com Docker

1. Clone o repositório e entre na pasta do projeto:

   ```bash
   git clone https://github.com/micaeltoscano/group-music-recommender.git
   cd group-music-recommender
   ```

2. Crie o arquivo local de configuração:

   ```bash
   cp .env.example .env
   ```

3. Gere uma chave Fernet e copie o resultado para `FERNET_KEY` no `.env`:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. No painel do Spotify, configure a URI de redirecionamento:

   ```text
   http://localhost:8000/auth/callback
   ```

   Depois, preencha `SPOTIFY_CLIENT_ID` e `SPOTIFY_CLIENT_SECRET` no `.env`.

5. Se quiser usar a interpretação local de contexto, inicie o Ollama no host:

   ```bash
   ollama pull llama3.1:8b
   ollama serve
   ```

   O sistema possui fallback determinístico e continua funcionando se o Ollama estiver indisponível.

6. Suba a aplicação:

   ```bash
   docker compose up --build
   ```

Serviços disponíveis:

| Serviço | Endereço |
|---|---|
| Aplicação web | <http://localhost:5173> |
| API | <http://localhost:8000> |
| Swagger UI | <http://localhost:8000/docs> |
| Health check | <http://localhost:8000/health> |

As migrações são aplicadas automaticamente durante a inicialização do backend.

## Configuração

As principais variáveis estão documentadas em `.env.example`.

| Variável | Finalidade | Obrigatória |
|---|---|---|
| `DATABASE_URL` | Conexão SQLAlchemy com PostgreSQL | Sim |
| `SPOTIFY_CLIENT_ID` | Identificador da aplicação Spotify | Sim para login |
| `SPOTIFY_CLIENT_SECRET` | Segredo da aplicação Spotify | Sim para login |
| `SPOTIFY_REDIRECT_URI` | Callback cadastrado no Spotify | Sim para login |
| `FERNET_KEY` | Criptografia dos tokens em repouso | Sim fora de desenvolvimento/teste |
| `LASTFM_API_KEY` | Tags e descobertas contextuais | Não |
| `OLLAMA_BASE_URL` | Endpoint local do Ollama | Não |
| `OLLAMA_MODEL` | Modelo usado para interpretar o contexto | Não |
| `DISCOVERY_MODE_ENABLED` | Habilita o modo Descoberta | Não |
| `BRIDGE_TRACKS_ENABLED` | Identifica músicas-ponte | Não |
| `SUBGROUP_BALANCING_ENABLED` | Equilibra subgrupos no resultado | Não |

Nunca versione o arquivo `.env` nem credenciais reais.

## Desenvolvimento sem Docker

### Backend

Com PostgreSQL disponível e as variáveis configuradas:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

## Testes e build

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm ci
npm run build
```

Os testes usam SQLite e clientes externos simulados; credenciais reais do Spotify, Last.fm ou Ollama não são necessárias para a suíte automatizada.

## Fluxo principal

1. Os participantes autenticam suas contas Spotify.
2. O anfitrião cria uma sala e compartilha o código.
3. O grupo entra e, opcionalmente, responde ao Vibe Check.
4. O anfitrião define ocasião, descrição e modo de consenso.
5. O motor monta e pontua as músicas candidatas.
6. Regras de rejeição, representação e diversidade ajustam a seleção.
7. As faixas são sequenciadas e publicadas em uma playlist privada.
8. O resultado apresenta métricas, justificativas e opções de feedback.

## Estrutura do repositório

```text
.
├── backend/
│   ├── alembic/          # migrações do banco
│   ├── app/
│   │   ├── api/          # endpoints FastAPI
│   │   ├── clients/      # Spotify, Last.fm, Ollama e criptografia
│   │   ├── db/           # modelos e sessões SQLAlchemy
│   │   ├── engine/       # motor puro de recomendação
│   │   ├── schemas/      # contratos Pydantic
│   │   └── services/     # orquestração dos casos de uso
│   └── tests/            # testes automatizados
├── diagrams/             # diagramas de domínio, arquitetura e fluxos
├── frontend/             # interface React/Vite
├── .env.example          # modelo de configuração
└── docker-compose.yml    # ambiente local completo
```

## Segurança e privacidade

- senhas não são coletadas; a identidade é delegada ao Spotify;
- tokens do Spotify permanecem no backend e são criptografados em repouso;
- o frontend recebe apenas um cookie de sessão `httpOnly`;
- o parâmetro OAuth `state` protege o callback contra CSRF;
- respostas individuais do Vibe Check não são expostas aos demais membros;
- dados musicais brutos não são enviados ao Ollama;
- logout e remoção/anonimização de dados possuem fluxos separados;
- falhas de serviços auxiliares acionam fallbacks sem expor informações sensíveis.

## Restrições conhecidas

- aplicações novas no Spotify Development Mode possuem acesso limitado a usuários autorizados;
- salas suportam de um a cinco integrantes e expiram após 24 horas;
- cada playlist contém de 20 a 30 faixas, com no máximo duas por artista;
- Last.fm e Ollama enriquecem o contexto, mas não substituem o motor determinístico;
- a criação real da playlist exige credenciais e uma conta Spotify autorizada.

Os diagramas técnicos e de interação estão disponíveis em [`diagrams/`](diagrams/).
