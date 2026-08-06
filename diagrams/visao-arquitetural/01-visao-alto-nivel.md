# 01 — Visão de alto nível da arquitetura

![Visão de alto nível da arquitetura](01-visao-alto-nivel.png)

```mermaid
flowchart LR
    subgraph CLIENTE["CLIENTE"]
        direction TB
        SPA("<b>Frontend React + Vite</b><br/>Single Page Application<br/>navegador do usuário")
    end

    subgraph COMM["INFRAESTRUTURA DE COMUNICAÇÃO"]
        direction TB
        REST("<b>REST / JSON sobre HTTP</b><br/>RNF-12<br/>sessão por cookie httpOnly<br/>(vibe_session)")
    end

    subgraph DOCKER["Docker Compose — serviços vibe_backend + vibe_db"]
        direction TB
        subgraph SERVIDOR["SERVIDOR — Backend FastAPI (camadas)"]
            direction TB
            L1("<b>Interface</b> — app/api<br/>auth · rooms · vibe_check<br/>music · feedback · health")
            L2("<b>Aplicação</b> — app/services<br/>generation · room · result<br/>feedback · library · privacy")
            L3("<b>Domínio: Motor PNE</b> — app/engine<br/>scoring · fairness · clustering<br/>bridge · sequencer · weights<br/><i>puro e determinístico, sem I/O</i>")
            L4("<b>Integração</b> — app/clients<br/>spotify_client · lastfm_client<br/>llm_client · crypto")
            L5("<b>Dados</b> — app/db<br/>models · session (SQLAlchemy)")
        end
        BD[("<b>PostgreSQL</b> (produção)<br/><b>SQLite</b> (testes) — RNF-11<br/>migrações via Alembic")]
    end

    subgraph EXT["SISTEMAS EXTERNOS"]
        direction TB
        SPOT("Spotify Web API")
        LFM("Last.fm API")
        OLL("Ollama — LLM local")
    end

    SPA <==> REST
    REST <==> L1

    L1 --> L2
    L2 --> L3
    L2 --> L4
    L2 --> L5
    L5 --> BD

    L4 --> SPOT
    L4 --> LFM
    L4 --> OLL

    L1 -. "atalho real: get_db + models" .-> L5
    L1 -. "atalho real: OAuth em auth.py" .-> L4
    L4 -. "lateral real: lê SpotifyToken" .-> L5

    classDef cliente fill:#e8f0fe,stroke:#3b5bdb,color:#1a2a6c
    classDef comunica fill:#f3f0ff,stroke:#7048e8,color:#3b2a6c
    classDef camada fill:#f8f9fa,stroke:#495057,color:#212529
    classDef motor fill:#fff4e6,stroke:#e8590c,stroke-width:3px,color:#7f2d00
    classDef dados fill:#e6fcf5,stroke:#0ca678,color:#0b4f3f
    classDef externo fill:#fff0f6,stroke:#c2255c,color:#6c1030

    class SPA cliente
    class REST comunica
    class L1,L2,L4,L5 camada
    class L3 motor
    class BD dados
    class SPOT,LFM,OLL externo
```

Este diagrama combina os dois estilos arquiteturais do slide 06 (Projeto Arquitetural) que o sistema
de fato implementa: **Cliente-Servidor** no eixo horizontal — o Frontend React é o cliente que
acessa, através de uma infraestrutura de comunicação REST/JSON sobre HTTP (RNF-12), o servidor
FastAPI, que por sua vez atua ele próprio como cliente dos servidores externos Spotify, Last.fm e
Ollama — e **Camadas** dentro do container do servidor, onde `app/api` → `app/services` → `app/engine`
formam a pilha principal e `app/clients` e `app/db` são as camadas de suporte que isolam,
respectivamente, o mundo externo e a persistência. A decisão de modelagem mais relevante foi
**destacar `app/engine` como camada própria e mostrá-la sem nenhuma seta de saída**: uma verificação
dos imports confirma que o motor PNE importa apenas a biblioteca padrão do Python e outros módulos do
próprio `app/engine`, sem tocar em banco, HTTP ou serviços — é essa pureza que sustenta o
determinismo e a testabilidade exigidos pelos RNF-03/RNF-04, e desenhá-la como folha da hierarquia
é o que torna a garantia visível em vez de apenas afirmada. Por honestidade com o código, as três
dependências que **violam** a regra "cada camada só depende da inferior" aparecem como setas
tracejadas em vez de omitidas: `app/api` alcança `app/db` diretamente (injeção de `get_db` e consultas
a *models* em `auth.py`, `rooms.py` e `vibe_check.py`) e `app/clients` diretamente (fluxo OAuth em
`auth.py` e `music.py`), pulando a camada de serviços, e `app/clients/spotify_client.py` lê o modelo
`SpotifyToken` de `app/db` para renovar tokens, criando uma dependência lateral entre duas camadas
irmãs. O agrupamento `Docker Compose` no diagrama cobre apenas os dois serviços do lado servidor
(`vibe_backend` e `vibe_db`); o `docker-compose.yml` declara ainda um terceiro serviço,
`vibe_frontend`, que apenas hospeda/serve o *bundle* da SPA — o cliente que efetivamente executa é o
navegador do usuário, e por isso ele aparece fora de qualquer container, do lado esquerdo da
fronteira Cliente-Servidor.
