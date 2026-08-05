# 01 — Diagrama de Estados: MusicSession

![Diagrama de Estados: MusicSession](01-estados-musicsession.png)

```mermaid
stateDiagram-v2
    [*] --> open : create_room()\nroom_service.py:107

    open --> generating : start_generation()\ngeneration_service.py:115\n[guard: host && status != generating]
    generating --> open : complete_generation()\ngeneration_service.py:162\n[sucesso]
    generating --> open : fail_generation()\ngeneration_service.py:175\n[erro]

    open --> [*] : expiração temporal (expires_at)\nsala efêmera

    state open {
        [*] --> AguardandoMembros
        AguardandoMembros --> ContextoDefinido : Host define\nocasião/modo (PB-06)
        ContextoDefinido --> AguardandoMembros : Host altera/limpa\ncontexto
        AguardandoMembros --> AguardandoMembros : Membro entra\n(PB-05, máx 5)
        ContextoDefinido --> VibeCheckAberto : Membros preenchem\nVibe Check (PB-07)
        VibeCheckAberto --> ProntaParaGerar : Membros prontos ou\nhost decide gerar
    }

    state generating {
        [*] --> starting
        starting --> interpreting_context : 0% → 8%
        interpreting_context --> collecting_tastes : 8% → 20%
        collecting_tastes --> discovering_context : 20% → 40%
        discovering_context --> ranking : 40% → 55%
        ranking --> matching_spotify : 55% → 70%
        matching_spotify --> creating_playlist : 70% → 90%
        creating_playlist --> finalizing : 90% → 97%
        finalizing --> completed : 97% → 100%
    }
```

Este diagrama modela o ciclo de vida dinâmico da entidade `MusicSession` (sala de recomendação colaborativa), conforme implementado no modelo SQLAlchemy `backend/app/db/models.py:146-179` e gerenciado pelos serviços `app/services/room_service.py` e `app/services/generation_service.py`.

### Racional de Arquitetura e Decisões de Estado

1. **Dois Estados Persistentes em Banco:**
   A coluna `MusicSession.status` (`String(32)`, default `"open"`) armazena estritamente dois valores em banco: `"open"` e `"generating"`. Os subestados comportamentais de `open` (Aguardando Membros, Contexto Definido, Vibe Check Aberto, Pronta para Gerar) são inferidos dinamicamente na aplicação e na API pelo estado dos relacionamentos (presença de membros, definição de `occasion`/`mode` e submissões em `vibe_check_answers`). Essa abstração simplifica o schema relacional mantendo a rica navegação do lobby no React frontend.

2. **Mecanismo de Lock e Guardas de Segurança (PB-13):**
   A transição de `"open"` para `"generating"` acionada por `start_generation()` executa um **lock pessimista de linha no PostgreSQL** via `.with_for_update()`. O código valida duas guardas críticas:
   - `room.host_user_id != host_id`: Lança `RoomHostRequiredError` impedindo que convidados iniciem a geração.
   - `room.status == "generating"`: Lança `GenerationConflictError` evitando execuções concorrentes simultâneas na mesma sala.

3. **Ciclo de Vida do Pipeline e Resiliência (PB-13, PB-17):**
   Enquanto em `"generating"`, a sala é blindada contra edições de membros. Ambas as saídas do pipeline — sucesso (`complete_generation`) e erro (`fail_generation`) — transicionam a sala **de volta para `"open"`**, liberando-a para novas gerações sem destruir o histórico de membros ou a sala. A expiração temporal (`expires_at`) garante a limpeza da sala efêmera.
