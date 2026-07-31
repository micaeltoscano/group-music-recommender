# Sprint 7 — Biblioteca musical ampliada e eficiente

> **Finalidade deste arquivo:** plano operacional isolado da Sprint 7. Ele consolida o contrato de
> produto, a ordem dos PBs, decisões técnicas, testes e handoffs esperados. Não substitui o campo
> `Status` do [`PLANO_EXECUCAO.md`](PLANO_EXECUCAO.md), que continua sendo a fonte lida pelo
> orquestrador.

## 1. Estado e portão de entrada

- **Estado deste plano:** PRONTO PARA EXECUÇÃO.
- **Estado da implementação:** PB-30..34 VALIDADO; Sprint 7 pronta para validação integrada.
- **Data do refinamento:** 2026-07-31.
- **Branch atual no momento da criação:** `feat/SPRINT06/stabilization`.
- **Liberação:** Product Owner removeu as dependências formais de todas as Sprints anteriores e
  promoveu a Sprint 7 no documento oficial em 2026-07-31.
- **Regra interna:** executar exatamente um PB por vez; cada PB deve terminar em `AGUARDANDO-QA` e
  receber `VALIDADO` independente antes do próximo.

Este arquivo não autoriza reescrever o histórico da Sprint 6, antecipar migrações de PBs futuros ou
marcar qualquer item como `VALIDADO`.

## 2. Objetivo

Ampliar o repertório de cada integrante para além do Top 50, combinando Tops de três faixas temporais
e músicas de playlists elegíveis em uma biblioteca temporária, deduplicada e limitada a **500 faixas
Spotify únicas por pessoa**.

O incremento deve melhorar cobertura sem:

- tratar toda música de playlist como preferência forte;
- permitir crescimento ilimitado do banco;
- realizar uma chamada Spotify por faixa;
- buscar novamente dados frescos antes de sete dias;
- permitir que uma biblioteca grande domine uma pequena;
- bloquear a geração quando existir um snapshot Top utilizável;
- expor nomes de playlists, tokens ou perfis individuais.

## 3. Contrato fechado da biblioteca

### 3.1. Limites

| Limite | Valor | Regra |
|---|---:|---|
| Biblioteca persistida por usuário | 500 faixas únicas | Tops e playlists contam juntos |
| Tops por faixa temporal | 50 | `short_term`, `medium_term` e `long_term` |
| Tops potenciais antes do dedupe | 150 | Sempre ocupam as primeiras vagas |
| Candidatas ativas por usuário/geração | 250 | Limite antes do dedupe global |
| Alvo de Tops no pool ativo | até 150 | Mantém prioridade de preferência forte |
| Alvo de playlists no pool ativo | até 100 | Capacidade ociosa pode ser redistribuída |
| TTL default | 7 dias | Biblioteca fresca faz zero chamada Spotify |
| Paginação Spotify | até 50 itens/página | Nunca presumir página única |
| Concorrência externa inicial | 1 | Configurável, mas conservadora por default |

Top artists são sinais auxiliares e não consomem vagas de faixas.

### 3.2. Playlists elegíveis

- Inventariar playlists retornadas para o usuário atual com paginação completa.
- Sincronizar itens apenas de playlists próprias ou colaborativas cujo conteúdo a API permita ler.
- Tratar playlist seguida/inacessível e `403` como conteúdo inelegível, sem contorno.
- Ignorar itens nulos, episódios, arquivos locais e faixas sem Spotify ID utilizável.
- Quando as playlists excederem a capacidade restante, preencher por round-robin determinístico para
  impedir que uma playlist longa elimine as demais.

### 3.3. Dedupe e proveniência

- Chave lógica pessoal: `(user_id, spotify_track_id)`.
- Uma faixa repetida em Tops ou playlists ocupa uma única vaga.
- Todas as origens, ranks, faixas temporais e recorrências necessárias ao peso devem ser preservadas.
- Nenhum payload bruto do Spotify deve ser persistido.

### 3.4. Pesos default

| Origem | Peso |
|---|---:|
| Top `short_term` | 1,00 |
| Top `medium_term` | 0,85 |
| Top `long_term` | 0,65 |
| Playlist própria | 0,45 |
| Playlist colaborativa | 0,35 |

Evidências múltiplas podem reforçar o sinal com bônus limitado, mas o peso final nunca ultrapassa
`1,00`. Pesos devem ficar centralizados e testáveis, não espalhados por serviços.

### 3.5. Cache e falhas

- Biblioteca com idade inferior a sete dias é retornada sem rede.
- Após o TTL, reler inventário e comparar `snapshot_id` antes de baixar itens.
- Playlist inalterada não chama seu endpoint de itens novamente.
- Sync usa staging e promoção atômica; parcial nunca substitui o último snapshot pronto.
- `429` respeita `Retry-After`.
- `QUOTA_EXCEEDED` é distinguido de rate limit transitório.
- Cache pronto pode ser servido como stale com aviso sanitizado.
- Sem biblioteca anterior, falha não apaga o snapshot Top do PB-08.
- Duas sincronizações simultâneas convergem sem duplicidade ou HTTP 500.

### 3.6. Privacidade

- Persistir somente metadados necessários à recomendação.
- Tokens continuam sob o contrato seguro existente e nunca entram na biblioteca.
- Nenhuma lista de faixas ou nome de playlist de outro usuário entra no contrato coletivo.
- LLM não recebe biblioteca, nomes de playlists ou faixas pessoais.
- `DELETE /auth/me` remove inventário, vínculos, snapshots e sinais pessoais da Sprint 7.
- Logs e resultado usam apenas totais/proporções agregadas.

## 4. Ordem imutável da implementação

| Ordem | PB | Título | Pontos | Dependência imediata |
|---:|---|---|---:|---|
| 1 | PB-30 | Autorização e inventário de playlists | 3 | Nenhuma |
| 2 | PB-31 | Biblioteca musical limitada a 500 faixas | 5 | PB-30 `VALIDADO` |
| 3 | PB-32 | Sincronização incremental e resiliente | 5 | PB-31 `VALIDADO` |
| 4 | PB-33 | Perfil ponderado e seleção de candidatas | 8 | PB-32 `VALIDADO` |
| 5 | PB-34 | Integração e observabilidade | 3 | PB-33 `VALIDADO` |

**Total:** 24 pontos.

Não antecipar modelos, endpoints ou telas pertencentes ao PB seguinte. Migrações devem partir do
head real no momento de cada PB e permanecer lineares.

## 5. PB-30 — Autorização e inventário de playlists

### Objetivo

Solicitar o menor consentimento necessário e produzir um inventário paginado, mínimo e privado das
playlists elegíveis do usuário.

### Escopo de implementação

1. Acrescentar `playlist-read-private` ao contrato OAuth.
2. Detectar token antigo sem o novo escopo e devolver reautenticação acionável, sem loop.
3. Implementar paginação completa de `GET /me/playlists`.
4. Implementar o método paginado de itens necessário aos PBs seguintes, sem ainda compor a biblioteca.
5. Classificar acesso próprio, colaborativo ou inelegível.
6. Persistir apenas ID, tipo de acesso, total, `snapshot_id`, estado e data de verificação.
7. Diferenciar 401, 403, 429 e payload inválido com mensagens sanitizadas.

### Arquivos previstos

- `backend/app/clients/spotify_client.py`
- autenticação/scopes e configuração correspondente
- `backend/app/db/models.py`
- migração posterior a `0018_pb29_vibe_status`
- serviço/repositório de inventário
- `backend/tests/test_pb30_playlist_inventory.py`

### Critérios e testes obrigatórios

- `CT-PB30-01` — novo escopo e reconsentimento.
- `CT-PB30-02` — paginação integral do inventário.
- `CT-PB30-03` — somente conteúdo elegível segue para sync.
- `CT-PB30-04` — persistência mínima e privada.
- `CT-PB30-05` — 401/403/429 diferenciados.

### Fora do escopo

- Persistir as 500 faixas.
- Aplicar TTL de sete dias.
- Alterar o motor ou a geração.
- Criar tela nova.

### Saída obrigatória

Commit `feat(PB-30): ...`, status `AGUARDANDO-QA` e mensagem literal:

```text
PB-30 IMPLEMENTADO — INICIANDO VALIDAÇÃO
```

## 6. PB-31 — Biblioteca musical limitada a 500 faixas

### Objetivo

Compor e persistir a biblioteca pessoal normalizada com Tops prioritários, faixas de playlists nas
vagas restantes e limite absoluto de 500.

### Escopo de implementação

1. Modelar faixa normalizada, vínculo usuário/faixa, proveniência e snapshot pessoal.
2. Coletar até 50 Tops por cada faixa temporal.
3. Deduplicar Tops antes de calcular a capacidade restante.
4. Preencher playlists elegíveis em round-robin determinístico.
5. Preservar origens/ranks sem duplicar a faixa.
6. Impor unicidade e limite também na camada de serviço/transação.
7. Integrar remoção ao `DELETE /auth/me`.

### Testes obrigatórios

`CT-PB31-01..06`, incluindo fronteiras `0`, `499`, `500`, `501`, dedupe, justiça entre playlists,
privacidade e migração reversível.

### Fora do escopo

- TTL e atualização incremental.
- Pesos do motor.
- Integração da geração.

### Saída obrigatória

Commit `feat(PB-31): ...`, status `AGUARDANDO-QA` e parada no portão.

## 7. PB-32 — Sincronização incremental e resiliente

### Objetivo

Atualizar a biblioteca no máximo a cada sete dias, baixar somente playlists alteradas e preservar o
último snapshot pronto em qualquer falha parcial.

### Escopo de implementação

1. TTL default de sete dias configurável.
2. Zero chamadas Spotify para cache fresco.
3. Comparação de `snapshot_id` após expiração.
4. Paginação em lotes, sem `GET /tracks/{id}` e sem Search por faixa nativa.
5. Concorrência externa default 1.
6. Lock/upsert por usuário, staging e promoção atômica.
7. Tratamento distinto de 429 e `QUOTA_EXCEEDED`.
8. Fallback stale e preservação do Top do PB-08.
9. Encerramento de `DEF-PB08-01` no fluxo compartilhado.

### Testes obrigatórios

`CT-PB32-01..06`, com PostgreSQL para a prova de concorrência quando necessário.

### Saída obrigatória

Commit `feat(PB-32): ...`, status `AGUARDANDO-QA` e parada no portão.

## 8. PB-33 — Perfil ponderado e seleção limitada de candidatas

### Objetivo

Converter a biblioteca em sinais ponderados e selecionar no máximo 250 candidatas por pessoa sem
dar mais poder a quem possui mais músicas armazenadas.

### Escopo de implementação

1. Criar DTOs de sinais preparados pelo serviço.
2. Centralizar pesos `1.00/0.85/0.65/0.45/0.35` no motor.
3. Combinar origens com bônus limitado e peso final `<=1`.
4. Atualizar afinidade/compatibilidade para consumir pesos.
5. Selecionar pool contextual determinístico de até 250 por usuário.
6. Mirar até 150 Tops e 100 playlists, redistribuindo somente capacidade ociosa.
7. Preservar contribuidores no dedupe global.
8. Testar bibliotecas assimétricas, como 500 contra 50 faixas.

### Restrição arquitetural

Todo cálculo fica em `backend/app/engine/`, puro, determinístico, sem rede ou banco.

### Testes obrigatórios

`CT-PB33-01..06`, além de regressões de compatibilidade, veto, justiça e contexto.

### Saída obrigatória

Commit `feat(PB-33): ...`, status `AGUARDANDO-QA` e parada no portão.

## 9. PB-34 — Integração e observabilidade

### Objetivo

Usar a biblioteca ponderada no pipeline, expor estado de sincronização ao próprio usuário e manter o
fallback histórico de Tops.

### Escopo de implementação

1. `GET /me/music-library` com estado, contagem `0..500`, idade, stale e aviso sanitizado.
2. `POST /me/refresh-music-library` idempotente e com erros acionáveis.
3. Exibir quantidade/idade no componente existente da Home, seguindo o design oficial.
4. Carregar perfil ponderado no `generation_service` quando pronto.
5. Cair para PB-08 quando ausente ou indisponível.
6. Reutilizar ID/URI nativos conforme PB-25; Search somente para externas.
7. Explicar proporções agregadas de Top/playlist/contexto sem origem privada.

### Testes obrigatórios

`CT-PB34-01..06`, build frontend e regressão integral do pipeline.

### Saída obrigatória

Commit `feat(PB-34): ...`, status `AGUARDANDO-QA` e parada no portão.

## 10. Validação integrada da Sprint

Executar somente após PB-30..34 estarem individualmente `VALIDADO`:

1. `CT-S7-INT-01` — três usuários sincronizam e geram; biblioteca `<=500` e pool `<=250`.
2. `CT-S7-INT-02` — cache fresco e sync incremental reduzem chamadas.
3. `CT-S7-INT-03` — rate limit/quota preservam a demonstração via cache.
4. `CT-S7-INT-04` — isolamento, privacidade e remoção ponta a ponta.
5. `CT-S7-INT-05` — regressão completa, migrações e frontend.
6. `CT-S7-INT-06` — spike real sanitizado com as três contas autorizadas.

### Critérios de encerramento

- [ ] PB-30..34 `VALIDADO` individualmente.
- [ ] Nenhum usuário possui mais de 500 faixas únicas.
- [ ] Nenhuma geração recebe mais de 250 candidatas por usuário.
- [ ] Cache fresco produz zero chamada Spotify.
- [ ] Sync incremental não baixa playlists inalteradas.
- [ ] Não existe N+1 por faixa.
- [ ] 401/403/429/quota e concorrência mantêm o estado consistente.
- [ ] Falha parcial não promove snapshot incompleto.
- [ ] Remoção da conta apaga os dados pessoais da Sprint 7.
- [ ] Motor continua puro e justo para bibliotecas assimétricas.
- [ ] Regressão, migrações, build e spike real estão documentados.

Somente o QA pode emitir:

```text
SPRINT 7 CONCLUÍDA — INCREMENTO VALIDADO
```

## 11. Estratégia de demonstração com três usuários

Antes da apresentação:

1. Confirmar que as três contas estão autorizadas no app Spotify.
2. Fazer o novo consentimento OAuth antecipadamente.
3. Sincronizar cada biblioteca enquanto a API está disponível.
4. Confirmar estado `ready`, contagem `<=500` e idade inferior a sete dias.
5. Não forçar refresh no dia da demonstração se o cache estiver fresco.
6. Manter fallback de Tops verificado para cada pessoa.
7. Ensaiar uma geração com contexto específico e uma falha Spotify simulada.
8. Não registrar tokens, nomes de playlists ou listas pessoais nas evidências.

## 12. Comandos mínimos de verificação

Adequar nomes focados ao PB em execução:

```bash
cd backend
APP_ENV=test .venv/bin/pytest tests/test_pbXX_*.py -o addopts='' -q
APP_ENV=test .venv/bin/pytest tests -o addopts='' -q
.venv/bin/alembic upgrade head
.venv/bin/alembic downgrade -1
.venv/bin/alembic upgrade head
cd ../frontend
npm run build
cd ..
git diff --check
./scripts/orquestrar.sh --list --no-pull
```

Chamadas Spotify reais não fazem parte da suíte automatizada e exigem autorização explícita,
ambiente controlado e evidência sanitizada.

## 13. Registro de execução

Atualizar esta tabela apenas quando o documento oficial liberar a Sprint e cada portão for cumprido:

| PB | Início | Commit | Testes do Dev | Veredito QA | Relatório |
|---|---|---|---|---|---|
| PB-30 | 2026-07-31 | `efb8625`, `be45742` | 11 focados; 419/6 regressão | Validado — QA: 12 focados; 420/6 regressão | `docs/relatorios-testes/PB-30.md` |
| PB-31 | 2026-07-31 | `04ac876` | 11 focados; 32 relacionados; 431/6 regressão | Validado — QA: 14 focados; 434/6 regressão | `docs/relatorios-testes/PB-31.md` |
| PB-32 | — | — | — | — | `docs/relatorios-testes/PB-32.md` |
| PB-33 | — | — | — | — | `docs/relatorios-testes/PB-33.md` |
| PB-34 | — | — | — | — | `docs/relatorios-testes/PB-34.md` |

## 14. Decisões que não podem ser alteradas silenciosamente

- O limite de 500 inclui Tops e playlists juntos.
- Tops sempre têm prioridade de armazenamento e peso.
- Playlists são sinal mais fraco, não preferência binária equivalente.
- O pool de geração é menor do que a biblioteca persistida.
- TTL é sete dias por default.
- `snapshot_id` evita baixar itens inalterados.
- Sincronização parcial nunca substitui cache pronto.
- Sem biblioteca, geração tenta o fallback Top.
- Nomes de playlists e faixas pessoais não aparecem no contrato coletivo.
- Mudança nesses pontos exige atualizar backlog, execução, testes e este arquivo antes do código.

## 15. Ponto exato de retomada

- **Próximo passo:** iniciar validação integrada da Sprint 7 em fase separada.
- **Evidência QA:** `49 passed`; `CT-PB34-01..06` aprovados e `DEF-PB34-01` revalidado.
- **Dependências:** PB-30 e PB-31 `VALIDADO` em 2026-07-31.
- **Portão seguinte:** PB-32 termina em `AGUARDANDO-QA` e exige validação independente.
- **Proibido na retomada:** antecipar PB-33 ou posteriores.
