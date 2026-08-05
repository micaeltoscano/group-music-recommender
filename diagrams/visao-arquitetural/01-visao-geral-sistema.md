# 01 — Visão Geral do Sistema (Nível Container)

![Visão Geral do Sistema](01-visao-geral-sistema.png)

```mermaid
graph TD
    %% Estilos de nós e subgrafos
    classDef client fill:#e0f7fa,stroke:#006064,stroke-width:2px,color:#000
    classDef app fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000
    classDef engine fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000,stroke-dasharray: 5 5
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef external fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#000
    
    subgraph ClientLayer [💻 Camada Cliente]
        Browser[Navegador Web]
        SPA[React SPA Vite<br/>Modo Escuro / Glassmorphism<br/>Porta 5173] ::: client
        Browser -->|Interage| SPA
    end

    subgraph Infra [🐳 Infraestrutura Docker Compose]
        subgraph AppLayer [⚙️ Camada de Aplicação FastAPI - Porta 8000]
            Router[API Router Layer<br/>app/api/*<br/>auth, rooms, vibe_check, etc.] ::: app
            Services[Services Layer<br/>app/services/*<br/>music_service, generation_service, etc.] ::: app
            Clients[Clients Layer<br/>app/clients/*<br/>spotify_client, lastfm_client, llm_client] ::: app
            
            subgraph EngineLayer [🧠 Engine / PNE Layer]
                Engine[Pura, determinística, sem I/O<br/>app/engine/*<br/>taste, candidates, scoring, fairness, etc.] ::: engine
            end
            
            Router -->|HTTPS/REST| Services
            Services -->|Importa e executa| Engine
            Services -->|Requisições| Clients
        end
        
        subgraph DataLayer [🗄️ Camada de Dados]
            Postgres[(PostgreSQL 16 Alpine<br/>16 Tabelas ORM<br/>Volume: vibe_pgdata)] ::: data
        end
    end

    subgraph ExternalSystems [🌐 Sistemas Externos]
        Spotify[Spotify Web API<br/>OAuth 2.0, Catálogo, Playlists] ::: external
        LastFM[Last.fm API<br/>Enriquecimento de Tags] ::: external
        Ollama[Ollama LLM Local<br/>Interpretação de Contexto] ::: external
    end

    %% Protocolos e Comunicação
    SPA <-->|HTTPS/REST<br/>HTTP-only cookies| Router
    Services <-->|SQLAlchemy ORM<br/>psycopg2| Postgres
    Clients <-->|HTTPS/REST OAuth 2.0| Spotify
    Clients <-->|HTTPS/REST API Key| LastFM
    Clients <-->|HTTP/REST Local| Ollama
    
    %% Configurações e Segurança
    Crypto((🔐 crypto.py<br/>Fernet)) -.-> Clients
```

Este diagrama de contêiner (nível 2 do modelo C4) representa a arquitetura técnica de alto nível do Vibe Check. O sistema utiliza **Docker Compose** para orquestrar os contêineres do backend, frontend e banco de dados, simplificando a infraestrutura e garantindo ambientes reproduzíveis.

1. **Isolamento de Camadas:** A arquitetura segue um fluxo de dependência estrito. O frontend apenas interage com a **API Router Layer**, não tendo acesso direto ao banco de dados ou aos serviços externos. A comunicação frontend-backend é feita via HTTPS/REST, e o gerenciamento de sessão utiliza cookies HTTP-only (vibe_session), garantindo isolamento e segurança.
2. **Pureza do PNE (Engine Layer):** Como exigido pelos requisitos **RNF-03** e **RNF-04**, a camada de domínio (`app/engine/*`) é mantida estritamente pura, determinística e livre de I/O. A **Services Layer** atua como um escudo, gerenciando as operações de banco de dados e as chamadas de API, para então passar estruturas de dados em memória para as funções do PNE.
3. **Resiliência e Fallbacks:** O sistema foi projetado para tolerar falhas em serviços externos secundários. O LLM Local (Ollama) possui um *fallback* determinístico caso esteja indisponível, conforme o **PB-17**. Da mesma forma, falhas na API do Last.fm são absorvidas silenciosamente sem interromper a geração da playlist, atendendo ao **RNF-08**. A renovação de tokens do Spotify ocorre automaticamente, garantindo a estabilidade das credenciais dos usuários.
4. **Modelo de Segurança:** Atendendo ao requisito **RNF-01**, tokens críticos (como o `access_token` e o `refresh_token` do Spotify) nunca deixam o backend. Eles são mantidos cifrados em repouso no banco de dados utilizando a biblioteca `cryptography` (Fernet) via `crypto.py`. O navegador apenas recebe o hash de sessão por meio de um cookie seguro, acompanhado de parâmetros de estado (state) para mitigar ataques CSRF.
5. **Feature Flags:** Para suportar a evolução pós-MVP, a aplicação emprega sinalizadores de recursos (feature flags) em `config.py` como `discovery_mode_enabled`, `bridge_tracks_enabled` e `subgroup_balancing_enabled`, que permitem controlar o comportamento da Engine dinamicamente sem alterar regras estritas de arquitetura.
