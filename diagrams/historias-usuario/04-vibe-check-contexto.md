# 04 — Contexto, modo de consenso e Vibe Check

![Contexto, modo de consenso e Vibe Check](04-vibe-check-contexto.png)

```mermaid
sequenceDiagram
    actor Host
    actor Convidado
    participant API as API (rooms.py / vibe_check.py)
    participant RoomSvc as room_service
    participant DB as Banco (MusicSession, VibeCheckAnswer)

    Host->>API: PUT /rooms/{code}/context {occasion, description}
    API->>RoomSvc: update_room_context(db, code, host_id, occasion, description)
    alt usuário autenticado não é o host
        RoomSvc-->>API: RoomHostRequiredError
        API-->>Host: 403
    else host confirmado
        RoomSvc->>DB: UPDATE MusicSession.occasion/description
        RoomSvc-->>API: MusicSession atualizada
        API-->>Host: 200 RoomResponse
    end

    Host->>API: PUT /rooms/{code}/mode {mode}
    API->>RoomSvc: update_room_mode(db, code, host_id, mode)
    alt modo fora do conjunto habilitado na configuração
        RoomSvc-->>API: RoomModeUnavailableError
        API-->>Host: 422
    else modo válido (Democrático | Festa Segura | Descoberta*)
        RoomSvc->>DB: UPDATE MusicSession.mode
        RoomSvc-->>API: MusicSession atualizada
        API-->>Host: 200 RoomResponse
    end

    Note right of Host: * Descoberta só aparece quando habilitada na config do produto (RF-10)

    Convidado->>API: GET /rooms/{code}/vibe-check
    API->>DB: busca VibeCheckAnswer(session_id, user_id)
    API-->>Convidado: perguntas fixas (energia, valência, popularidade) + status atual

    alt Convidado responde ao questionário
        Convidado->>API: POST /rooms/{code}/vibe-check {energy, valence, popularity}
        API->>DB: upsert VibeCheckAnswer(status="answered")
        API-->>Convidado: 200 "Vibe Check salvo"
    else Convidado opta por pular
        Convidado->>API: POST /rooms/{code}/vibe-check/skip
        API->>DB: upsert VibeCheckAnswer(status="skipped", energy/valence/popularity=null)
        API-->>Convidado: 200 "pulado, nenhuma preferência foi aplicada"
    end

    loop polling da sala (qualquer integrante)
        Host->>API: GET /rooms/{code}
        API->>DB: agrega vibe_status de todos os membros
        API-->>Host: RoomResponse.vibe_summary{total, pending, answered, skipped}
    end

    Note over API,DB: Na geração (diagrama 03), load_vibe_preferences agrega só as respostas<br/>"answered" em um VibePreferences para influenciar o ranqueamento
```

Este fluxo cobre RF-03 e foi escolhido por ser o único ponto do sistema em que host e convidado atuam
lado a lado sobre a mesma sala com autorizações opostas: `update_room_context`/`update_room_mode`
exigem `RoomHostRequiredError` para qualquer não-host, enquanto o Vibe Check é aberto a qualquer
integrante autenticado. Optamos por unir contexto/modo e Vibe Check no mesmo diagrama porque, no
código, ambos alimentam a mesma etapa futura de geração (contexto → `ContextCriteria`/LLM; Vibe Check
→ `VibePreferences`) e acontecem na mesma janela de tempo do lobby, antes do host disparar a geração.
O segundo `alt` (responder vs. pular) reproduz a exigência do backlog de que pular o questionário não
deve "fabricar preferências neutras" — no código isso aparece literalmente como
`energy/valence/popularity = None` em vez de um valor padrão como 0.5. A nota final aponta a costura
com o diagrama 03, deixando explícito que este fluxo é sempre anterior e opcional em relação à
geração, nunca bloqueante (RNF-06).
