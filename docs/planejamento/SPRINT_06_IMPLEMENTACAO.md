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
| 2 | PB-26 | Pool contextual híbrido | CONCLUÍDO TECNICAMENTE |
| 3 | PB-27 | Acompanhamento compartilhado da geração | CONCLUÍDO TECNICAMENTE |
| 4 | PB-28 | Conformidade visual do Login/Landing | CONCLUÍDO TECNICAMENTE |
| 5 | PB-29 | Estado compartilhado e privado do Vibe Check | CONCLUÍDO TECNICAMENTE |

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

- A integração Last.fm passou a suportar `tag.getTopTracks` e `track.getSimilar`, com parsing
  defensivo, deduplicação e falha aberta.
- Até três tags estáveis são derivadas da ocasião; até cinco sementes pessoais cobrem integrantes
  distintos antes de repetir uma origem. Os limites de fontes e candidatas são configuráveis.
- A proveniência `spotify_top`, `lastfm_tag` ou `lastfm_similar` acompanha cada candidata. Similares
  preservam a referência da semente e os integrantes de origem; dados privados não saem da API.
- O motor puro intercala o prefixo em 50% de contexto e 50% de âncoras quando há material válido,
  preserva ao menos 40% de Tops e nunca promove uma candidata que atinja o limiar de veto.
- Se Last.fm estiver ausente, inválido ou indisponível, a ordem anterior baseada nos Tops permanece
  como fallback. A busca textual no Spotify fica restrita às candidatas externas pelo PB-25.
- Cenário adversarial automatizado: 50 Tops tristes para ocasião `Festa` resultaram em 15 Tops e 15
  descobertas de festa no primeiro bloco de 30.
- Testes: `41 passed` na suíte combinada de PB-17, PB-18, PB-25 e PB-26.
- Migrações: nenhuma.

## 7. PB-27 — Acompanhamento compartilhado da geração

### Objetivo

Persistir estágios reais da execução e expô-los a todos os integrantes da sala por meio do polling
já autenticado. Host e participantes devem compartilhar geração, sucesso e erro; somente o host
mantém a capacidade de iniciar ou repetir.

### Evidências e execução

- A execução persiste estágio e percentual monotônico em `playlist_runs`; a migração
  `0017_pb27_generation_progress` adiciona os dois campos com defaults retrocompatíveis.
- O pipeline publica oito marcos reais: interpretação, coleta, descoberta, ranking, matching,
  criação, finalização e conclusão. Falhas usam um estado próprio e mantêm o último percentual.
- `GET /rooms/{code}` entrega somente o estado agregado da última execução a integrantes da sala:
  ID, estágio, percentual, resultado/erro sanitizado e data. Tops, respostas, clusters e tokens não
  entram no payload.
- Host e participantes entram na mesma tela ao observar a execução em `running`; o progresso usa
  `progressbar` acessível, o resultado abre automaticamente e a falha volta ao lobby.
- A ação de iniciar/repetir continua renderizada apenas para o host e a autorização 403 do backend
  foi mantida na regressão.
- Testes: `14 passed` na suíte de progresso, geração e host-only; `npm run build` concluído.
- Migração: `0017_pb27_generation_progress.py`.

## 8. PB-28 — Conformidade visual do Login/Landing

### Objetivo

Reconstruir Login/Landing em React a partir do design obrigatório, usando os tokens visuais do
projeto, mantendo OAuth funcional, foco de teclado, estados de carregamento/erro e comportamento
responsivo.

### Evidências e execução

- `Login.jsx` foi reconstruído em React a partir de `01-login-landing.png` e do estado Login do
  protótipo: cabeçalho, hero, mock de satisfação, prova social, quatro passos, diferenciais e CTA.
- A implementação usa exclusivamente classes e tokens do `index.css`; não incorpora o HTML do
  protótipo e remove todos os estilos inline da tela.
- O botão continua iniciando o OAuth real em `/auth/login`, bloqueia duplo clique, indica
  redirecionamento e se recupera ao voltar pelo histórico. Erros via query string possuem `alert`.
- Controles têm foco visível; hierarquia semântica, descrição de segurança, responsividade em três
  faixas e `prefers-reduced-motion` foram incluídos.
- Verificação: `npm run build` concluído com 46 módulos transformados.
- Migrações: nenhuma.

## 9. PB-29 — Estado compartilhado e privado do Vibe Check

### Objetivo

Exibir no lobby o estado individual `pendente`, `respondido` ou `pulado` e o total agregado, sem
revelar respostas. Cada integrante poderá responder, pular e editar somente o próprio registro;
ausência/pulo continuará neutro para o motor.

### Evidências e execução

- `vibe_check_answers` agora diferencia `answered` e `skipped`; valores numéricos são anuláveis para
  que pular não fabrique uma resposta `0.5`. Registros históricos recebem `answered` por default.
- `GET /rooms/{code}` expõe somente o status por membro e contagens agregadas de pendentes,
  respondidos e pulados. Nenhum valor de energia, valência ou popularidade aparece nesse contrato.
- `GET /rooms/{code}/vibe-check` devolve os valores exclusivamente ao próprio integrante e permite
  pré-carregar/editar. `POST /skip` faz upsert do pulo; uma resposta posterior substitui o estado.
- O motor carrega exclusivamente linhas `answered`; pendentes e pulados participam como ausência
  neutra na agregação vigente.
- O lobby apresenta badges individuais, total agregado e CTA `EDITAR` após resposta, sem transferir
  controle de contexto/modo/geração aos participantes.
- Testes: `22 passed` na suíte de PB-07, Vibe scoring, PB-27 e PB-29; `npm run build` concluído.
- Migração: `0018_pb29_vibe_status.py`.

## 10. Validação técnica integrada da Sprint

A preencher ao fim da implementação.

## 11. Commits

- PB-25 — `5d38e83 feat(PB-25): tornar matching Spotify resiliente`.
- PB-26 — `53c59f3 feat(PB-26): adicionar pool contextual hibrido`.
- PB-27 — `5504680 feat(PB-27): compartilhar progresso da geracao`.
- PB-28 — `c57179c feat(PB-28): alinhar login ao design`.
- PB-29 — a registrar após o commit.
