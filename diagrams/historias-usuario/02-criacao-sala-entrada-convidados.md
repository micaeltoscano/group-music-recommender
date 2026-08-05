# 02 — Criação de sala e entrada de convidados

![Criação de sala e entrada de convidados](02-criacao-sala-entrada-convidados.png)

```mermaid
%%{init: {'sequence': {'mirrorActors': false}}}%%
sequenceDiagram
    actor Host
    actor Membro as Membro da Sala
    participant API as API (rooms.py)
    participant RoomSvc as room_service
    participant DB as Banco (MusicSession, MusicSessionMember)

    Host->>API: 1: POST /rooms
    API->>RoomSvc: 1.1: create_room(db, host_id)
    loop até obter código único (máx. 10 tentativas)
        RoomSvc->>RoomSvc: 1.1.1: _generate_room_code()
        RoomSvc->>DB: 1.1.2: INSERT MusicSession + MusicSessionMember(role="host")
        alt colisão de código (IntegrityError)
            DB-->>RoomSvc: violação de unicidade
            RoomSvc->>RoomSvc: 1.1.3: rollback e tenta novo código
        end
    end
    RoomSvc-->>API: MusicSession criada (code, expires_at = +24h)
    API-->>Host: 201 RoomResponse{code, members:[host]}

    Note over Host,Membro: Host compartilha o código curto da sala

    Membro->>API: 2: POST /rooms/{code}/join
    API->>RoomSvc: 2.1: join_room(db, code, user_id)
    RoomSvc->>DB: 2.1.1: SELECT MusicSession WHERE code FOR UPDATE

    alt sala não encontrada
        RoomSvc-->>API: RoomNotFoundError
        API-->>Membro: 404
    else sala expirada (expires_at <= agora)
        RoomSvc-->>API: RoomExpiredError
        API-->>Membro: 410
    else usuário já é membro
        RoomSvc->>DB: 2.1.2: SELECT MusicSessionMember(session_id, user_id)
        RoomSvc-->>API: MusicSession (retorno idempotente)
        API-->>Membro: 200 RoomResponse
    else sala com 5 integrantes
        RoomSvc->>DB: 2.1.3: COUNT(MusicSessionMember) WHERE session_id
        RoomSvc-->>API: RoomFullError
        API-->>Membro: 409
    else entrada válida
        RoomSvc->>DB: 2.1.4: INSERT MusicSessionMember(role="member")
        RoomSvc-->>API: MusicSession atualizada
        API-->>Membro: 200 RoomResponse
    end

    loop polling a cada 4s (janela permitida: 3–5s)
        Membro->>API: 3: GET /rooms/{code}
        API->>RoomSvc: 3.1: get_room_for_member(db, code, user_id)
        alt usuário não é integrante
            RoomSvc-->>API: RoomAccessDeniedError
            API-->>Membro: 403 (sem dados da sala)
        else usuário é integrante
            API->>DB: 3.2: lista membros + última PlaylistRun + vibe_summary
            API-->>Membro: 200 RoomResponse{members, generation, vibe_summary}
        end
    end
```

Este fluxo cobre RF-02 (PB-04/PB-05) e foi escolhido por ser o único ponto do sistema em que
concorrência real é tratada explicitamente: o `SELECT ... FOR UPDATE` em `_room_for_join_statement`
serializa entradas simultâneas na mesma sala no PostgreSQL, e o teste de mutação registrado no
`PLANO_EXECUCAO.md` comprova que, sem esse lock, o limite de cinco integrantes é violado. O `alt` com
cinco ramos reproduz fielmente as exceções de `room_service.join_room` (sala inexistente, expirada,
já-membro idempotente, sala cheia, entrada válida), e o `loop` final documenta o mecanismo de
atualização por *polling* exigido pela RNF-03 (3–5 s), que substitui WebSockets no MVP. Optamos por
mostrar `Criar sala` e `Entrar em sala` no mesmo diagrama porque, no código, ambos compartilham o
mesmo módulo (`room_service.py`) e a mesma entidade (`MusicSession`/`MusicSessionMember`), tornando a
relação entre host e convidado mais clara em uma única sequência do que em dois diagramas separados.
