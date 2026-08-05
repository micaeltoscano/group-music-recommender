# 01 — Visão Geral do Sistema (Nível Container)

![Visão Geral do Sistema](01-visao-geral-sistema.png)

```mermaid
graph TD
    subgraph ClientLayer ["💻 Camada Cliente"]
        Browser["Navegador Web"]
        SPA["React SPA Vite<br/>Modo Escuro / Glassmorphism<br/>Porta 5173"]
        Browser -->|Interage| SPA
    end

    subgraph Infra ["🐳 Infraestrutura Docker Compose"]
        subgraph AppLayer ["⚙️ Camada de Aplicação FastAPI - Porta 8000"]
            Router["API Router Layer<br/>app/api/*<br/>auth, rooms, vibe_check, etc."]
            Services["Services Layer<br/>app/services/*<br/>music_service, generation_service, etc."]
            Clients["Clients Layer<br/>app/clients/*<br/>spotify_client, lastfm_client, llm_client"]

            subgraph EngineLayer ["🧠 Engine / PNE Layer"]
                Engine["Pura, determinística, sem I/O<br/>app/engine/*<br/>taste, candidates, scoring, fairness, etc."]
            end

            Router -->|HTTPS/REST| Services
            Services -->|Importa e executa| Engine
            Services -->|Requisições| Clients
        end

        subgraph DataLayer ["🗄️ Camada de Dados"]
            Postgres[("PostgreSQL 16 Alpine<br/>16 Tabelas ORM<br/>Volume: vibe_pgdata")]
        end
    end

    subgraph ExternalSystems ["🌐 Sistemas Externos"]
        Spotify["Spotify Web API<br/>OAuth 2.0, Catálogo, Playlists"]
        LastFM["Last.fm API<br/>Enriquecimento de Tags"]
        Ollama["Ollama LLM Local<br/>Interpretação de Contexto"]
    end

    SPA <-->|"HTTPS/REST<br/>HTTP-only cookies"| Router
    Services <-->|"SQLAlchemy ORM<br/>psycopg2"| Postgres
    Clients <-->|HTTPS/REST OAuth 2.0| Spotify
    Clients <-->|HTTPS/REST API Key| LastFM
    Clients <-->|HTTP/REST Local| Ollama

    Crypto(("🔐 crypto.py<br/>Fernet")) -.-> Clients

    classDef client fill:#e0f7fa,stroke:#006064,stroke-width:2px,color:#000
    classDef app fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000
    classDef engine fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000,stroke-dasharray:5 5
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef external fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#000

    class Browser,SPA client
    class Router,Services,Clients app
    class Engine engine
    class Postgres data
    class Spotify,LastFM,Ollama external
```

Este diagrama de contêineres (Modelo C4 Nível 2) detalha a arquitetura de alto nível do **Vibe Check**, estruturada para garantir desacoplamento, resiliência a falhas de serviços externos e estrita separação entre I/O e a inteligência pura de recomendação.

### Racional Arquitetural e Princípios de Design

1. **Isolamento e Segurança da Camada Cliente (RNF-01):**
   O frontend React (Vite) consome unicamente a camada de **API Routers** (`app/api/*`) via chamadas HTTPS/REST. Nenhuma credencial do Spotify atinge o navegador: a autenticação utiliza cookies seguros `HTTP-only` (`vibe_session`), e os tokens OAuth do Spotify permanecem mantidos no backend, cifrados em repouso com o algoritmo Fernet (`crypto.py`).

2. **Pureza do PNE (Engine Layer) (RNF-03, RNF-04):**
   A camada de domínio (`app/engine/*`) é **totalmente pura, síncrona/determinística e isenta de I/O**. Ela opera exclusivamente sobre `dataclasses` em memória (`UserTasteProfile`, `CandidateTrack`, `ContextCriteria`). A **Services Layer** (`app/services/*`) atua como a única orquestradora de I/O, responsabilizando-se por buscar dados no banco PostgreSQL e clientes externos antes de invocá-la.

3. **Estratégias de Resiliência a Serviços Externos (RNF-08, PB-17):**
   - **LLM Local (Ollama):** Interpreta o contexto da sala (`occasion`/`description`). Caso o Ollama esteja indisponível, o sistema aciona automaticamente o *fallback determinístico*, garantindo a geração da playlist.
   - **API Last.fm:** Enriquece candidatas com tags musicais. Falhas ou rate limits na API Last.fm são silenciados para não comprometer a execução principal.
   - **Spotify Client:** Gerencia renovação automática de tokens expirados e aplica exponenciação de tempo de retentativa em respostas HTTP 429.

4. **Infraestrutura em Docker Compose:**
   Orquestra os três contêineres principais (`frontend`, `backend` e `db` PostgreSQL 16 Alpine com volume persistente `vibe_pgdata`), garantindo reprodutibilidade idêntica entre ambiente local de desenvolvimento e produção.
