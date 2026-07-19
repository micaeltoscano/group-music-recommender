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
| 2 | PB-26 | Pool contextual híbrido | CORREÇÃO CONCLUÍDA TECNICAMENTE |
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

- Backend completo: `395 passed, 6 skipped, 12 warnings` em `12.87s`. Os seis casos pulados já são
  marcados como exploratórios/dependentes de ambiente; os avisos são de APIs depreciadas em testes
  históricos e não representam falha funcional.
- Frontend: `npm run build` concluído, 46 módulos transformados e bundle de produção emitido.
- Banco: cadeia Alembic linear, com um único head em `0018_pb29_vibe_status`.
- Compatibilidade: a primeira execução integral revelou contratos históricos que exigem payload
  exato ao criar/editar sala. Esses comandos mantiveram o formato antigo; os metadados novos ficam
  no polling autenticado, e `join`/`GET` compartilham o mesmo estado de membros.
- Segurança: integrações externas permaneceram mockadas; nenhum segredo, token ou resposta privada
  foi adicionado ao Git ou aos contratos coletivos.
- Estado do Git ao concluir: branch `feat/SPRINT06/stabilization`, sem push ou merge.
- Esta seção é evidência técnica do implementador, não aprovação independente de QA.

## 11. Commits

- PB-25 — `5d38e83 feat(PB-25): tornar matching Spotify resiliente`.
- PB-26 — `53c59f3 feat(PB-26): adicionar pool contextual hibrido`.
- PB-27 — `5504680 feat(PB-27): compartilhar progresso da geracao`.
- PB-28 — `c57179c feat(PB-28): alinhar login ao design`.
- PB-29 — `46df4a9 feat(PB-29): compartilhar status do vibe check`.
- Compatibilidade integrada — registrada no commit final deste documento.

## 12. Correção de regressão do PB-26 — aderência ao contexto específico

### Estado

`AGUARDANDO-QA` — correção implementada e verificada tecnicamente pelo Agente Implementador em
2026-07-18; a aprovação independente não foi presumida.

### Evidência de uso real

Uma geração com a descrição `um clima de festa punk bem rockzao pesado` comprovou que o Ollama
produziu `tags_positive=[punk, rock]`, energia alta e restrição a faixas suaves, mas o PB-26
converteu a busca somente para `party`, `dance` e `pop`. Das 30 faixas finais, 13 vieram dos Tops,
15 de similares e apenas duas da busca por tag. Similares herdavam tags da semente e rótulos amplos
como `rock` faziam faixas lentas parecerem energéticas.

### Causa e correção

- Tags positivas específicas agora ocupam primeiro o limite de busca. O caso reproduzido gera
  `punk`, `rock`, `party`; contextos genéricos continuam produzindo `party`, `dance`, `pop`.
- Candidatas `lastfm_similar` não herdam mais gêneros ou tags da semente. Cada uma passa pela cascata
  faixa → artista → gêneros → consenso do PB-18 antes do ranking.
- A tag usada em `tag.getTopTracks` permanece como evidência confiável mesmo se o enriquecimento
  adicional falhar; falhas externas continuam abertas e não interrompem a geração.
- O scoring separa rótulos completos de tokens: `post-punk` não satisfaz literalmente `punk` e
  `dream pop` não vira automaticamente música de festa.
- Energia alta passou a exigir sinais mais fortes (`hard rock`, `metal`, `hardcore`, `energetic`,
  `punk` isolado); `slow`, `dreamy`, `ethereal`, `melancholy`, `ballad` e equivalentes indicam baixa
  energia. Restrições como `suave` agora penalizam todo o tema calmo.
- Tops continuam como âncoras pessoais e o peso de contexto dos modos não foi aumentado; vetos,
  justiça, representação e fallbacks anteriores foram preservados.

### Evidências técnicas

- Regressão determinística: `The Pretender` obteve `context_score=0.7156`, `Go Slowly` obteve
  `0.1206` e `Evangeline` obteve `0.0` para o contexto reproduzido; o limiar contextual é `0.60`.
- Testes focados de PB-17/PB-18/PB-26: `41 passed / 0 failed`.
- Integração relacionada de LLM, Last.fm, matching e geração: `68 passed / 0 failed`.
- Suíte backend completa: `400 passed / 6 skipped / 0 failed`, com 12 avisos históricos.
- `compileall`, `pip check` e `git diff --check` aprovados; `ruff` não está instalado na venv.
- Migrações e contratos de API: nenhuma alteração.

### Arquivos da correção

- `backend/app/services/contextual_pool_service.py`
- `backend/app/services/context_enrichment_service.py`
- `backend/app/services/generation_service.py`
- `backend/app/engine/context_scoring.py`
- `backend/tests/test_pb26_contextual_pool.py`
- `backend/tests/test_pb26_context_regression.py`

### Risco residual e validação esperada

O primeiro uso de uma faixa similar pode realizar consultas adicionais ao Last.fm; execuções
seguintes reutilizam `track_context_cache`, e falhas mantêm o fallback. O QA deve repetir o caso
`festa punk rock pesada`, confirmar a prioridade `punk/rock`, a ausência de herança em similares e
a regressão completa. Uma playlist já criada não é recalculada retroativamente; é necessário gerar
uma nova execução.

## 13. Correções de lobby e resultado — retorno, Descoberta e aderência visual

### Estado

`AGUARDANDO-QA` — correções implementadas e verificadas tecnicamente pelo Agente Implementador em
2026-07-18; este registro não altera os planejamentos históricos nem presume aprovação independente.

### Problemas reproduzidos e causas

- O botão de voltar do resultado navegava para a sala, mas o polling encontrava a última execução
  concluída e redirecionava imediatamente para o resultado. A rota mudava duas vezes, dando a
  impressão de que o botão não funcionava.
- O modo Descoberta já existia sob feature flag, porém `DISCOVERY_MODE_ENABLED` não estava definido
  no ambiente Docker local e o valor seguro padrão é `false`; por isso o contrato do lobby omitia o
  terceiro modo.
- A tela de resultado usava uma composição simplificada com estilos inline e não reproduzia a
  hierarquia da referência de design: cabeçalho do produto, hero, métricas, playlist por fases,
  representação lateral e explicabilidade.

### Correções implementadas

- O resultado envia para a sala o identificador da execução que o usuário escolheu deixar. A sala
  ignora o redirecionamento apenas para essa execução concluída; uma geração futura, com outro
  `run_id`, continua abrindo o novo resultado automaticamente.
- O ambiente Docker local foi configurado com `DISCOVERY_MODE_ENABLED=true`, sem versionar segredos
  ou remover o opt-in do produto. Em execução, o backend confirmou os modos `Democrático`,
  `Festa Segura` e `Descoberta`.
- A tela foi recomposta com os tokens existentes e classes responsivas, seguindo a referência oficial
  sem incluir a barra de navegação e o painel de tweaks exclusivos do protótipo de desenvolvimento.
- O cartão “Descobertas” usa dado real: percentual das faixas finais cujo identificador persistido tem
  origem `lastfm:`. A métrica é derivada das faixas já salvas, sem migração e sem nova chamada externa.
- Não foi exibido um contador fictício de “rejeições evitadas”, pois o pipeline atual não persiste uma
  métrica auditável equivalente. O quarto cartão apresenta a justiça real já calculada pelo motor.

### Evidências técnicas

- Testes focados de resultado, Descoberta e regressões de interface: `11 passed / 0 failed`.
- Suíte backend completa com a flag desligada para preservar o contrato histórico do MVP:
  `402 passed / 6 skipped / 0 failed`, com 12 avisos históricos.
- O comportamento com a flag ligada permanece coberto pelos testes do PB-21 e foi confirmado no
  container: `discovery_mode_enabled=True` e três modos disponíveis.
- Frontend: `npm run build` concluído, 46 módulos transformados e bundle de produção emitido.
- `git diff --check` aprovado após a implementação; nenhuma migração de banco foi necessária.

### Arquivos da correção

- `frontend/src/Result.jsx`
- `frontend/src/Room.jsx`
- `frontend/src/index.css`
- `backend/app/schemas/rooms.py`
- `backend/app/services/result_service.py`
- `backend/tests/test_pb16_resultado_qa.py`
- `backend/tests/test_s6_result_ui_regressions.py`

### Configuração local não versionada

O `.env` local recebeu `DISCOVERY_MODE_ENABLED=true` e `APP_ENV=production`. O arquivo permanece
ignorado pelo Git. O default versionado continua `false`, preservando o rollout controlado definido
no PB-21.
