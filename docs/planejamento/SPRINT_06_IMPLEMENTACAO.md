# Sprint 6 — Estabilização e evolução contextual

> **Finalidade deste arquivo:** handoff técnico para a pessoa responsável pela documentação e pelo
> planejamento oficial do projeto. Ele registra o que foi implementado, por que cada mudança ocorreu,
> quais decisões foram tomadas, como verificar o comportamento e o que ainda não está resolvido.
> As marcações `CONCLUÍDO TECNICAMENTE` e `AGUARDANDO-QA` são evidências do implementador, não
> aprovação independente nem autorização para reescrever o histórico das Sprints 1–5.

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

| Ordem | Classificação | Item | Objetivo | Estado do implementador |
|---:|---|---|---|---|
| 1 | Evolução | PB-25 | Resiliência e eficiência da integração Spotify | CONCLUÍDO TECNICAMENTE |
| 2 | Evolução | PB-26 | Pool contextual híbrido | CONCLUÍDO TECNICAMENTE |
| 3 | Evolução | PB-27 | Acompanhamento compartilhado da geração | CONCLUÍDO TECNICAMENTE |
| 4 | Evolução | PB-28 | Conformidade visual do Login/Landing | CONCLUÍDO TECNICAMENTE |
| 5 | Evolução | PB-29 | Estado compartilhado e privado do Vibe Check | CONCLUÍDO TECNICAMENTE |
| 6 | Compatibilidade | Sprint 6 | Preservar payloads históricos de criação/edição de sala | CONCLUÍDO TECNICAMENTE |
| 7 | Correção | PB-26 | Fazer tags específicas e metadados próprios afetarem o contexto | AGUARDANDO-QA |
| 8 | Correção | PB-16/PB-21 | Retorno ao lobby, tela de resultado e Descoberta visível | AGUARDANDO-QA |
| 9 | Correção | PB-26/PB-16 | Priorizar intenção explícita e explicar âncoras habituais | AGUARDANDO-QA |

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

- Estado final após evoluções e correções: `405 passed, 6 skipped, 12 warnings` em `12.72s`. Os seis
  casos pulados já são marcados como exploratórios/dependentes de ambiente; os avisos são de APIs
  depreciadas em testes históricos e não representam falha funcional.
- O checkpoint de `395 passed` citado durante a implementação corresponde ao término inicial dos
  PBs 25–29. Os totais `400`, `402` e `405` das seções seguintes mostram a adição progressiva das
  regressões; não são resultados contraditórios.
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

| Ordem | Commit | Conteúdo |
|---:|---|---|
| 1 | `5d38e83 feat(PB-25): tornar matching Spotify resiliente` | Reuso de ID/URI e interrupção em 429 |
| 2 | `53c59f3 feat(PB-26): adicionar pool contextual hibrido` | Last.fm por tag/similar e composição com Tops |
| 3 | `5504680 feat(PB-27): compartilhar progresso da geracao` | Progresso persistido e tela comum para a sala |
| 4 | `c57179c feat(PB-28): alinhar login ao design` | Reconstrução visual do Login/Landing |
| 5 | `46df4a9 feat(PB-29): compartilhar status do vibe check` | Estados pending/answered/skipped e privacidade |
| 6 | `4513a8c fix(sprint-6): preservar contratos de sala` | Compatibilidade dos payloads históricos |
| 7 | `cfcec7f fix(PB-26): corrigir aderencia ao contexto` | Tags específicas, enriquecimento e energia |
| 8 | `52527ec fix(PB-16): corrigir resultado e retorno ao lobby` | Resultado, métrica de descoberta e retorno |
| 9 | `06eef11 docs(sprint-06): registrar correcoes de lobby e resultado` | Registro documental da correção anterior |
| 10 | `1af62fe fix(PB-26): priorizar intencao explicita no ranking` | Peso de contexto, oferta específica e explicação |
| 11 | `13af508 docs(sprint-06): registrar prioridade do contexto` | Registro documental do ajuste de ranking |

O commit que concluir este handoff deve ser lido como atualização documental, sem mudança de código.

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

## 14. Correção de intenção explícita — contexto antes do Top no modo Descoberta

### Estado

`AGUARDANDO-QA` — correção implementada e verificada tecnicamente pelo Agente Implementador em
2026-07-18; uma playlist existente não é modificada retroativamente.

### Caso reproduzido

Para `festa punk bem pesadona`, o LLM interpretou energia alta e a tag `punk`. Uma execução selecionou
21 âncoras do Top e apenas seis faixas Last.fm em 27; quatro descobertas eram punk e duas passaram por
sinais amplos de energia/rock. Uma execução posterior chegou a 14 descobertas em 29 faixas, mas ainda
incluiu Tops incompatíveis com o pedido, como ANAVITÓRIA. A sala tinha um único participante e
`subgroup_balancing_applied=false`; portanto, a diluição não foi causada pelo balanceamento entre
membros, e sim pela composição fixa com Tops e pelo peso insuficiente do contexto.

### Causa e decisão de produto

- `punk`, `energética` e `animada` consumiam igualmente o limite de três consultas, embora as duas
  últimas sejam descritores de energia, não gêneros específicos.
- A consulta direta de cada tag trazia somente quatro músicas; logo, `punk` podia oferecer no máximo
  quatro candidatas diretas antes do ranking.
- No modo Descoberta, contexto representava 10% do score coletivo. A afinidade com um Top pessoal
  podia superar uma faixa nova muito mais aderente à descrição.
- O Top continua útil como âncora de familiaridade. O contexto passa a ter peso maior no ranking,
  especialmente dentro de cada origem, enquanto afinidade, justiça, veto e diversidade continuam
  decidindo. Isso melhora a ordem, mas não transforma a descrição em filtro obrigatório.

### Correções implementadas

- O motor separa tags musicais específicas de adjetivos de energia. O caso reproduzido consulta
  `punk`, `party` e `dance`, em vez de `punk`, `energetica` e `animada`.
- A primeira tag específica recebe até o dobro da oferta configurada (oito com o default atual), sem
  aumentar consultas genéricas nem ultrapassar o teto de dez por chamada e 32 candidatas externas.
- No modo Descoberta, o peso do contexto passou de 10% para 30%. Os demais componentes foram
  rebalanceados mantendo soma 100%; rejeições e justiça continuam aplicados depois do score.
- “Por que essa playlist é justa?” agora mostra o percentual real de faixas vindas do repertório
  habitual e explica: elas são âncoras de familiaridade; a descrição prioriza o contexto, mas não
  substitui integralmente os gostos dos participantes.
- A explicação também é acrescentada ao consultar resultados antigos que ainda não a tenham no
  snapshot persistido, usando a origem real das faixas e sem migração.

### Evidências técnicas

- Regressão do caso: uma candidata punk aderente supera um Top pessoal conhecido de MPB/acústico no
  modo Descoberta.
- A intenção `punk, energética, animada` produz uma tag específica (`punk`) e limites de consulta
  `8, 4, 4` para `punk`, `party` e `dance`.
- Testes focados de PB-16/PB-21/PB-26: `23 passed / 0 failed`.
- Suíte backend completa: `405 passed / 6 skipped / 0 failed`, com 12 avisos históricos.
- Frontend: bundle de produção aprovado, com 46 módulos transformados.
- Nenhuma migração, segredo ou chamada externa foi adicionada aos testes.

### Arquivos da correção

- `backend/app/engine/context_scoring.py`
- `backend/app/engine/weights.py`
- `backend/app/services/contextual_pool_service.py`
- `backend/app/services/result_service.py`
- `backend/tests/test_pb16_resultado_qa.py`
- `backend/tests/test_pb26_contextual_pool.py`

### Limite deliberadamente não removido

O compositor híbrido ainda busca 50% de contexto e preserva pelo menos 40% de âncoras dos Tops quando
há material das duas origens. Portanto, aumentar o peso para 30% e ampliar a oferta específica reduz
o problema, mas não garante que todas as âncoras pessoais obedeçam literalmente à descrição. Se o
produto quiser uma garantia como “nenhuma MPB em uma solicitação estritamente punk”, isso deve virar
uma nova decisão planejada: piso mínimo de aderência também para Tops, participação de âncoras dinâmica
ou um modo de contexto estrito. Esta Sprint não introduziu filtro rígido para evitar falha de geração
quando Last.fm não fornece pelo menos 20 faixas válidas.

## 15. Guia de incorporação na documentação oficial

### 15.1. Como classificar estas mudanças

Este documento não decide em qual Sprint oficial cada alteração deve aparecer. A recomendação para
quem mantém o planejamento é separar **evolução funcional** de **correção descoberta por uso real**:

| Bloco | Classificação sugerida | Rastreabilidade recomendada |
|---|---|---|
| PB-25 a PB-29 | Histórias da Sprint 6 | Manter os números e critérios descritos nas seções 5–9 |
| Compatibilidade de sala | Correção transversal da Sprint 6 | Associar a PB-27/PB-29 sem alterar contratos históricos |
| Primeira correção contextual | Correção do PB-26 | Referenciar a evidência `festa punk rock pesada` |
| Resultado e retorno ao lobby | Correção de PB-16 com ativação do PB-21 | Registrar como dívida encontrada na Sprint 6 |
| Novo peso de contexto | Ajuste de produto do PB-26 | Registrar a mudança de 10% para 30% e seu limite residual |

Se a equipe optar por mover uma correção para outra Sprint, deve manter uma referência cruzada para
este arquivo e para o commit original. Não se recomenda reescrever os critérios ou status históricos
das Sprints anteriores, nem declarar `VALIDADO` sem a atuação do responsável por QA.

### 15.2. Fluxo funcional resultante

1. O host cria a sala e continua sendo o único autorizado a editar ocasião, descrição e modo ou
   iniciar uma geração.
2. Cada membro entra na sala e responde, pula ou edita apenas o próprio Vibe Check. O lobby mostra
   somente `pending`, `answered` ou `skipped` e os totais agregados.
3. Ao gerar, todos os membros passam a observar a mesma execução e os mesmos estágios pelo polling;
   somente o host vê a ação de iniciar/repetir.
4. O Ollama recebe somente ocasião e descrição e produz contexto estruturado. Tops, respostas
   individuais, tokens e clusters nunca entram nesse prompt. Falha ou resposta inválida ativa o
   fallback determinístico.
5. Snapshots Spotify já armazenados formam as âncoras pessoais. Candidatas nativas reutilizam ID/URI
   e não fazem Search novamente. O cache de Top 50 `medium_term` por sete dias é uma dependência
   anterior preservada pela Sprint 6; por isso uma geração não pede novamente os Tops ainda válidos.
6. Quando Last.fm está configurado, tags contextuais e similares ampliam o pool. Cada faixa externa
   é enriquecida com metadados próprios; não herda gênero da semente.
7. O motor puro calcula afinidade, consenso, Vibe Check, contexto, novidade, diversidade, veto e
   justiça. No modo Descoberta, contexto vale 30% do score coletivo, mas a composição ainda preserva
   uma parcela de Tops.
8. Apenas candidatas externas passam por matching textual no Spotify. Um 429 interrompe o lote e
   devolve falha recuperável, em vez de transformar o restante em falsos descartes.
9. O sequenciador aplica limite de duas faixas por artista, seleciona de 20 a 30 faixas, organiza o
   fluxo e cria uma playlist privada na conta Spotify do host.
10. Todos os membros chegam ao mesmo resultado. O retorno ao lobby ignora somente o redirecionamento
    da execução que o usuário acabou de deixar; uma execução futura continua abrindo automaticamente.

### 15.3. Contratos HTTP relevantes

Todos os endpoints abaixo exigem autenticação. Rotas de sala também verificam associação do usuário à
sala quando aplicável.

| Endpoint | Mudança ou semântica após a Sprint 6 |
|---|---|
| `GET /rooms/consensus-modes` | Lista modos habilitados; `Descoberta` só aparece com a feature flag ativa |
| `GET /rooms/{code}` | Inclui `generation`, `members[].vibe_status` e `vibe_summary` para polling coletivo |
| `POST /rooms` | Mantém o payload histórico, excluindo os metadados novos por compatibilidade |
| `PUT /rooms/{code}/context` | Host-only; mantém o payload histórico por compatibilidade |
| `PUT /rooms/{code}/mode` | Host-only; rejeita modos desabilitados e mantém o payload histórico |
| `POST /rooms/{code}/generate` | Host-only; inicia execução assíncrona e responde `202` |
| `GET /rooms/{code}/vibe-check` | Retorna perguntas, status e somente a resposta do próprio usuário |
| `POST /rooms/{code}/vibe-check` | Faz upsert de uma resposta `answered` |
| `POST /rooms/{code}/vibe-check/skip` | Registra `skipped` com valores privados nulos |
| `GET /rooms/{code}/result` | Acrescenta `discovery_percentage` e explicações agregadas de familiaridade |

O objeto agregado `generation` contém `run_id`, `status`, `stage`, `progress_percent`, erro sanitizado,
URL da playlist e data de atualização. O resumo do Vibe Check contém apenas `total`, `pending`,
`answered` e `skipped`. Nenhum desses contratos expõe os valores individuais dos demais membros.

### 15.4. Persistência e migrações

- `0017_pb27_generation_progress` adiciona `playlist_runs.progress_stage` e
  `playlist_runs.progress_percent`, ambos não nulos e retrocompatíveis.
- `0018_pb29_vibe_status` adiciona `vibe_check_answers.status` com default histórico `answered` e
  torna `energy`, `valence` e `popularity` anuláveis para representar `skipped` sem inventar valores.
- A cadeia final permanece linear e o head é `0018_pb29_vibe_status`.
- Pool contextual, correções de ranking, nova métrica de descoberta e explicações do resultado são
  derivados de dados existentes; não exigiram novas tabelas ou colunas.
- Resultados antigos não são reordenados. A explicação de familiaridade pode ser acrescentada durante
  a leitura porque é calculada pela origem já persistida das faixas.

### 15.5. Semântica das métricas do resultado

| Métrica/tela | Origem real | Observação para documentação |
|---|---|---|
| Satisfação do grupo | `compatibility_score` | Percentual de faixas com dois ou mais contribuidores; em sala de uma pessoa tende a 0 por definição |
| Representação mínima | Menor percentual em `representation` | Mede presença individual, não aprovação emocional |
| Descobertas | `discovery_percentage` | Percentual final de faixas com proveniência persistida `lastfm:` |
| Justiça do grupo | `fairness_score` | Índice de Jain sobre a distribuição de contribuições |
| Repertório habitual | `100 - discovery_percentage` | Tops usados como âncoras pessoais; não significa que toda âncora atende literalmente à descrição |

O protótipo visual mostrava “rejeições evitadas”, mas o sistema não persiste um número auditável com
essa semântica. A implementação não fabricou essa métrica: o quarto cartão usa justiça real. A barra
de navegação de estados e o painel “Tweaks” vistos no protótipo são ferramentas de desenvolvimento e
não foram incluídos na interface do produto.

### 15.6. Configuração e dependências operacionais

| Variável/componente | Default versionado | Papel |
|---|---|---|
| `DISCOVERY_MODE_ENABLED` | `false` | Habilita o terceiro modo no contrato e no lobby |
| `LASTFM_API_KEY` | ausente | Habilita descoberta e enriquecimento; sem chave, mantém fallback nos Tops |
| `LASTFM_TIMEOUT_SECONDS` | `5` | Limite de espera por consulta Last.fm |
| `LASTFM_CACHE_TTL_DAYS` | `30` | Reutilização do enriquecimento contextual |
| `CONTEXTUAL_POOL_SHARE` | `0.50` | Participação-alvo de contexto, limitada a 60% |
| `CONTEXTUAL_POOL_TAG_COUNT` | `3` | Quantidade máxima de tags consultadas |
| `CONTEXTUAL_POOL_SEED_COUNT` | `5` | Quantidade de Tops usados como sementes de similares |
| `CONTEXTUAL_POOL_TRACKS_PER_SOURCE` | `4` | Oferta genérica; a primeira tag específica pode usar até `8` |
| `CONTEXTUAL_POOL_MAX_CANDIDATES` | `32` | Teto de candidatas externas por execução |
| `OLLAMA_MODEL` | `llama3.1:8b` | Modelo local que interpreta o texto do host |

No ambiente local usado na validação, o `.env` ignorado pelo Git possui a flag Descoberta ativa e as
credenciais necessárias, sem que seus valores sejam documentados ou versionados. O default do
repositório continua seguro e opt-in.

A integração Last.fm utilizada aqui é somente leitura e usa uma chave da aplicação, sem OAuth por
integrante. Os métodos relevantes são descoberta por tag/similaridade e enriquecimento por tags de
faixa/artista; a chave nunca entra nos contratos de API nem nos testes.

O `docker-compose.yml` contém `db`, `backend` e `frontend`; **não contém um container Ollama**. O
backend Docker usa `http://host.docker.internal:11434` para alcançar um Ollama iniciado no host. Se
o serviço local não estiver ativo ou o modelo não estiver instalado, o fallback assume. Portanto,
não se deve documentar que “Ollama sobe com o Docker” enquanto o Compose não for alterado.

O ngrok foi usado apenas como apoio operacional para OAuth durante desenvolvimento. O endereço é
efêmero e não faz parte do código: ao trocar o túnel, é necessário alinhar a URL cadastrada no Spotify
com `SPOTIFY_REDIRECT_URI`, `FRONTEND_URL`, CORS e a base usada pelo frontend. Nenhuma URL temporária,
chave, secret ou token deve entrar na documentação versionada.

### 15.7. Arquivos alterados por área

Entre a base da Sprint 5 (`dff685d`) e o código funcional final (`1af62fe`), foram alterados 31
arquivos, com aproximadamente 3 mil linhas adicionadas. Os pontos principais são:

- Integrações: `backend/app/clients/lastfm_client.py` e o cliente Spotify já existente consumido pelo
  serviço de geração.
- Motor puro: `backend/app/engine/candidates.py`, `context_scoring.py`, `contextual_pool.py` e
  `weights.py`.
- Serviços: `context_enrichment_service.py`, `contextual_pool_service.py`, `generation_service.py` e
  `result_service.py`.
- API/contratos: `backend/app/api/rooms.py`, `api/vibe_check.py`, `schemas/rooms.py` e
  `schemas/vibe_check.py`.
- Banco: `backend/app/db/models.py` e migrações `0017`/`0018`.
- Frontend: `Login.jsx`, `Room.jsx`, `VibeCheck.jsx`, `Result.jsx`, `apiClient.js` e `index.css`.
- Regressões novas: testes dos PBs 25, 26, 27 e 29, além de resultado/navegação da Sprint 6.

### 15.8. Decisões que devem permanecer explícitas

- Host-only é regra de autorização no backend, não apenas ocultação visual.
- Resposta de Vibe Check é privada; somente estado e totais são coletivos.
- O LLM interpreta texto, mas não escolhe a playlist e não recebe perfis musicais.
- Last.fm amplia o pool; Spotify continua sendo a fonte de disponibilidade e o destino da playlist.
- Falha de Last.fm ou Ollama é aberta; falha/rate limit do Spotify pode impedir aquela execução.
- A descrição influencia o ranking, mas atualmente não é filtro absoluto.
- Descoberta, faixa-ponte e balanceamento de subgrupos possuem flags independentes. No ambiente
  validado, apenas Descoberta foi explicitamente ativada.
- A playlist é privada e criada na conta do host.
- Nenhum resultado existente é recalculado quando pesos ou regras mudam; é preciso gerar novamente.

### 15.9. Limitações e possíveis histórias futuras

1. **Aderência estrita opcional:** decidir se Tops fora do contexto devem ser excluídos quando há uma
   tag específica, com fallback seguro se não restarem 20 faixas.
2. **Participação dinâmica de Tops:** substituir o piso fixo por uma proporção baseada na confiança e
   na quantidade de candidatas aderentes.
3. **Métrica de rejeições evitadas:** só exibir após definir e persistir uma fórmula auditável e
   compatível com privacidade.
4. **Ollama no Compose:** adicionar serviço, volume do modelo e healthcheck se a equipe quiser startup
   realmente conjunto; hoje ele é dependência do host.
5. **Teste E2E real:** validar OAuth, Last.fm, Ollama e criação Spotify em ambiente controlado, pois os
   testes automatizados usam mocks deliberadamente.
6. **Calibração com múltiplos membros:** repetir contextos específicos com perfis divergentes para
   avaliar representação, veto e aderência simultaneamente.
7. **Satisfação de sala individual:** decidir se `compatibility_score=0` para uma pessoa deve continuar
   sendo exibido como satisfação, já que a fórmula mede gosto compartilhado.

### 15.10. Roteiro de validação para QA ou documentação

1. Aplicar migrações e confirmar head `0018_pb29_vibe_status`.
2. Subir banco, backend e frontend; confirmar healthchecks.
3. Ativar Descoberta, autenticar e confirmar os três modos no lobby.
4. Entrar com host e membro; verificar que somente o host edita contexto/modo e gera.
5. Responder e pular Vibe Check em usuários diferentes; confirmar badges sem expor respostas.
6. Gerar e observar ambos os navegadores mudarem para progresso e resultado.
7. Conferir retorno ao lobby sem redirecionamento imediato ao resultado antigo.
8. Repetir `festa punk bem pesadona`; inspecionar contexto estruturado, proveniência e seleção. Não
   assumir aderência absoluta enquanto o piso de Tops existir.
9. Desligar Last.fm e Ollama separadamente; confirmar fallbacks e ausência de vazamento de dados.
10. Simular Spotify 429; confirmar interrupção do lote, erro recuperável e sala novamente aberta.
11. Executar `(cd backend && DISCOVERY_MODE_ENABLED=false APP_ENV=test .venv/bin/pytest -o addopts='' -q)`.
12. Executar `(cd frontend && npm run build)` e `git diff --check` na raiz.

### 15.11. Estado de entrega deste handoff

- Branch: `feat/SPRINT06/stabilization`.
- Base anterior: `dff685d`, término integrado da Sprint 5.
- Último commit funcional da Sprint 6: `1af62fe`.
- Não houve push ou merge como parte da implementação registrada neste documento.
- Estado final verificado antes deste handoff: `405 passed`, `6 skipped`, zero falhas; frontend com 46
  módulos transformados; Docker local com banco, backend e frontend saudáveis.
- Correções das seções 12–14 permanecem `AGUARDANDO-QA` até validação independente.
