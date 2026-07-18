# Sprint 6 — Estabilização e evolução contextual

## 1. Registro da exceção processual

Em 2026-07-18, o proprietário do projeto autorizou explicitamente o Agente Implementador a executar
todos os PBs desta Sprint em sequência, sem o portão de validação independente entre histórias. Esta
autorização não transforma verificações do implementador em aprovação de QA e não altera os status,
critérios, relatórios ou evidências históricas das Sprints 1–5.

Este é o único documento de planejamento alterado pela Sprint 6. Os documentos anteriores permanecem
intactos para preservar a linha de base acadêmica e a rastreabilidade.

## 2. Evidências que motivaram a Sprint

- A geração real para a ocasião `Festa` usou somente o Top 50 dos integrantes como universo de
  candidatas; contexto e Vibe Check apenas reordenaram esse conjunto.
- O matching repetiu Spotify Search para faixas que já possuíam ID/URI e, após um `429`, continuou
  consultando as demais, convertendo 49 candidatas em descartes.
- O Vibe Check é consumido pelo ranking, mas o lobby não informa conclusão por integrante.
- A tela de Login funcional não reproduz o design obrigatório `01-login-landing.png`.
- Apenas o navegador do host entra na tela de geração; membros recebem `room.status=generating` pelo
  polling, mas permanecem no lobby.
- Autorização host-only já existe no backend e no frontend e deve permanecer como regressão.

## 3. Escopo e ordem

| Ordem | Item | Objetivo | Estado do implementador |
|---:|---|---|---|
| 1 | PB-25 | Resiliência e eficiência da integração Spotify | CONCLUÍDO TECNICAMENTE |
| 2 | PB-26 | Pool contextual híbrido | EM IMPLEMENTAÇÃO |
| 3 | PB-27 | Acompanhamento compartilhado da geração | A FAZER |
| 4 | PB-28 | Conformidade visual do Login/Landing | A FAZER |
| 5 | PB-29 | Estado compartilhado e privado do Vibe Check | A FAZER |

## 4. Restrições transversais

- Somente o host altera ocasião, descrição e modo e inicia/reinicia a geração.
- Cada integrante responde, pula ou edita apenas o próprio Vibe Check.
- O motor em `backend/app/engine/` permanece puro, determinístico e sem I/O.
- Tokens, respostas individuais e composição privada de subgrupos não são expostos.
- Serviços externos são mockados nos testes automatizados.
- Nenhum push ou merge faz parte desta execução.

## 5. PB-25 — Resiliência e eficiência da integração Spotify

### Objetivo

Reutilizar identificadores Spotify confiáveis já presentes nas candidatas e interromper a resolução
no primeiro rate limit, preservando uma nova tentativa controlada.

### Critérios

1. Candidata nativa com ID, URI e disponibilidade válida é correspondida sem Spotify Search.
2. Candidata externa ou incompleta continua usando busca e confiança de título/artista.
3. `SpotifyRateLimited` interrompe imediatamente o lote e preserva `retry_after`.
4. A API responde 429 de forma recuperável e a sala volta a `open`.
5. Erros isolados não relacionados a rate limit continuam registrados por candidata.

### Evidências e execução

- Candidatas vindas dos snapshots reutilizam o ID e a URI originais com confiança `1.0`, sem uma
  chamada redundante ao endpoint Search.
- Candidatas externas ou sem URI seguem usando a resolução textual e o limiar de confiança vigente.
- O primeiro `SpotifyRateLimited` encerra o lote, evita persistir descartes falsos e propaga o
  `retry_after` até a resposta HTTP 429.
- O fluxo de falha restaura a sala para `open` e marca a execução como `failed`, permitindo nova
  tentativa pelo host.
- Testes: `17 passed` na suíte focada dos PBs 13, 14, 15 e 25.
- Migrações: nenhuma.

## 6. PB-26 — Pool contextual híbrido

### Objetivo

Combinar os Tops dos integrantes, que continuam como âncoras pessoais, com descoberta contextual
da Last.fm por tags da ocasião e faixas similares. O conjunto final deve reservar espaço mensurável
para candidatas contextuais sem apagar representação individual, vetos ou fallbacks existentes.

### Evidências e execução

A preencher ao concluir o PB.

## 7. PB-27 — Acompanhamento compartilhado da geração

### Objetivo

A preencher antes da implementação.

### Evidências e execução

A preencher ao concluir o PB.

## 8. PB-28 — Conformidade visual do Login/Landing

### Objetivo

A preencher antes da implementação.

### Evidências e execução

A preencher ao concluir o PB.

## 9. PB-29 — Estado compartilhado e privado do Vibe Check

### Objetivo

A preencher antes da implementação.

### Evidências e execução

A preencher ao concluir o PB.

## 10. Validação técnica integrada da Sprint

A preencher ao fim da implementação.

## 11. Commits

- PB-25 — a registrar após o commit.
