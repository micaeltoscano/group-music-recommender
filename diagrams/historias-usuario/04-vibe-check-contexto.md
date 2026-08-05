# 04 — Contexto, modo de consenso e Vibe Check

![Contexto, modo de consenso e Vibe Check](04-vibe-check-contexto.png)

```mermaid
%%{init: {'sequence': {'mirrorActors': false}}}%%
sequenceDiagram
    actor Host
    actor Membro as Membro da Sala
    participant API as API (rooms.py / vibe_check.py)
    participant RoomSvc as room_service
    participant DB as Banco (MusicSession, VibeCheckAnswer)

    Host->>API: 1: PUT /rooms/{code}/context {occasion, description}
    API->>RoomSvc: 1.1: update_room_context(db, code, host_id, occasion, description)
    alt usuário autenticado não é o host
        RoomSvc-->>API: RoomHostRequiredError
        API-->>Host: 403
    else host confirmado
        RoomSvc->>DB: 1.1.1: UPDATE MusicSession.occasion/description
        RoomSvc-->>API: MusicSession atualizada
        API-->>Host: 200 RoomResponse
    end

    Host->>API: 2: PUT /rooms/{code}/mode {mode}
    API->>RoomSvc: 2.1: update_room_mode(db, code, host_id, mode)
    alt modo fora do conjunto habilitado na configuração
        RoomSvc-->>API: RoomModeUnavailableError
        API-->>Host: 422
    else modo válido (Democrático | Festa Segura | Descoberta*)
        RoomSvc->>DB: 2.1.1: UPDATE MusicSession.mode
        RoomSvc-->>API: MusicSession atualizada
        API-->>Host: 200 RoomResponse
    end

    Note right of Host: * Descoberta só aparece quando habilitada na config do produto (RF-10)

    Membro->>API: 3: GET /rooms/{code}/vibe-check
    API->>DB: 3.1: busca VibeCheckAnswer(session_id, user_id)
    API-->>Membro: perguntas fixas (energia, valência, popularidade) + status atual

    alt Membro da Sala responde ao questionário
        Membro->>API: 4: POST /rooms/{code}/vibe-check {energy, valence, popularity}
        API->>DB: 4.1: upsert VibeCheckAnswer(status="answered")
        API-->>Membro: 200 "Vibe Check salvo"
    else Membro da Sala opta por pular
        Membro->>API: 5: POST /rooms/{code}/vibe-check/skip
        API->>DB: 5.1: upsert VibeCheckAnswer(status="skipped", energy/valence/popularity=null)
        API-->>Membro: 200 "pulado, nenhuma preferência foi aplicada"
    end

    loop polling da sala (qualquer integrante)
        Host->>API: 6: GET /rooms/{code}
        API->>DB: 6.1: agrega vibe_status de todos os membros
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
