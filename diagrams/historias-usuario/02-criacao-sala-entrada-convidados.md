# 02 — Criação de sala e entrada de convidados

![Criação de sala e entrada de convidados](02-criacao-sala-entrada-convidados.png)

```mermaid
sequenceDiagram
    actor Host
    actor Convidado
    participant API as API (rooms.py)
    participant RoomSvc as room_service
    participant DB as Banco (MusicSession, MusicSessionMember)

    Host->>API: POST /rooms
    API->>RoomSvc: create_room(db, host_id)
    loop até obter código único (máx. 10 tentativas)
        RoomSvc->>RoomSvc: _generate_room_code()
        RoomSvc->>DB: INSERT MusicSession + MusicSessionMember(role="host")
        alt colisão de código (IntegrityError)
            DB-->>RoomSvc: violação de unicidade
            RoomSvc->>RoomSvc: rollback e tenta novo código
        end
    end
    RoomSvc-->>API: MusicSession criada (code, expires_at = +24h)
    API-->>Host: 201 RoomResponse{code, members:[host]}

    Note over Host,Convidado: Host compartilha o código curto da sala

    Convidado->>API: POST /rooms/{code}/join
    API->>RoomSvc: join_room(db, code, user_id)
    RoomSvc->>DB: SELECT MusicSession WHERE code FOR UPDATE

    alt sala não encontrada
        RoomSvc-->>API: RoomNotFoundError
        API-->>Convidado: 404
    else sala expirada (expires_at <= agora)
        RoomSvc-->>API: RoomExpiredError
        API-->>Convidado: 410
    else usuário já é membro
        RoomSvc->>DB: SELECT MusicSessionMember(session_id, user_id)
        RoomSvc-->>API: MusicSession (retorno idempotente)
        API-->>Convidado: 200 RoomResponse
    else sala com 5 integrantes
        RoomSvc->>DB: COUNT(MusicSessionMember) WHERE session_id
        RoomSvc-->>API: RoomFullError
        API-->>Convidado: 409
    else entrada válida
        RoomSvc->>DB: INSERT MusicSessionMember(role="member")
        RoomSvc-->>API: MusicSession atualizada
        API-->>Convidado: 200 RoomResponse
    end

    loop polling a cada 4s (janela permitida: 3–5s)
        Convidado->>API: GET /rooms/{code}
        API->>RoomSvc: get_room_for_member(db, code, user_id)
        alt usuário não é integrante
            RoomSvc-->>API: RoomAccessDeniedError
            API-->>Convidado: 403 (sem dados da sala)
        else usuário é integrante
            API->>DB: lista membros + última PlaylistRun + vibe_summary
            API-->>Convidado: 200 RoomResponse{members, generation, vibe_summary}
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
