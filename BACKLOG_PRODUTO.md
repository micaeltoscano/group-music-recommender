# BACKLOG DO PRODUTO

## Vibe Check — Group Music Recommender

**Disciplina:** Engenharia de Software  
**Professor:** Gledson Elias  
**Instituição:** [INFORMAÇÃO A DEFINIR]  
**Integrantes da equipe:**

- [INTEGRANTE 1]
- [INTEGRANTE 2]
- [INTEGRANTE 3]
- [DEMAIS INTEGRANTES]

**Local:** [INFORMAÇÃO A DEFINIR]  
**Ano:** 2026

---

## 1. Identificação do documento

| Campo | Informação |
|---|---|
| Título | Backlog do Produto — Vibe Check |
| Projeto | Group Music Recommender — Vibe Check |
| Tipo de documento | Especificação acadêmica do Backlog do Produto |
| Disciplina | Engenharia de Software |
| Professor | Gledson Elias |
| Instituição | [INFORMAÇÃO A DEFINIR] |
| Equipe | [INFORMAÇÃO A DEFINIR] |
| Versão | 1.0 |
| Data | 10 de julho de 2026 |
| Status | Proposta inicial para validação |

Este documento apresenta a visão, os épicos, as histórias de usuário, os critérios de aceitação, as prioridades, as estimativas e a proposta de planejamento incremental do produto Vibe Check. O conteúdo foi elaborado com base no escopo do MVP definido no `README.md` e nos conceitos apresentados nos materiais de Desenvolvimento Ágil e Engenharia de Requisitos da disciplina.

## 2. Visão geral do produto

O Vibe Check é uma aplicação web de recomendação musical em grupo. Um usuário, denominado host, cria uma sala efêmera e compartilha um código curto. Os demais integrantes entram na sala, autenticam-se por meio do Spotify e permitem que o sistema consulte seus principais artistas e músicas.

O produto não se limita a combinar históricos musicais. Seu elemento central é o **Preference Negotiation Engine (PNE)**, ou Motor de Negociação de Preferências, responsável por equilibrar afinidade musical, contexto do encontro, rejeições, diversidade e representação dos integrantes. O resultado é uma playlist real criada na conta Spotify do host.

O MVP utiliza Spotify OAuth para autenticação, salas temporárias com até cinco integrantes, contexto informado pelo host, Vibe Check opcional, modos de consenso, cálculo de compatibilidade, seleção justa de músicas, sequenciamento e explicações sobre o resultado.

## 3. Problema que o produto busca resolver

Escolher músicas para um grupo é uma atividade sujeita a conflitos. Playlists baseadas apenas na média das preferências tendem a favorecer a maioria e podem ignorar participantes com gostos diferentes. Além disso, o histórico musical não representa necessariamente o humor ou a ocasião atual.

As soluções existentes normalmente misturam preferências passadas, mas oferecem pouco controle sobre contexto, rejeições, grau de descoberta e justiça. Como consequência, um integrante pode ter baixa representação mesmo quando a playlist apresenta uma boa aceitação média.

O Vibe Check busca resolver esse problema por meio de uma negociação computacional de preferências. O sistema considera a satisfação média, a menor satisfação individual, a cobertura dos integrantes, as rejeições e o contexto atual antes de criar a playlist.

## 4. Objetivo geral

Desenvolver uma aplicação web capaz de gerar playlists coletivas no Spotify que representem os integrantes de um grupo, considerando gostos musicais, contexto, rejeições e critérios de justiça.

## 5. Objetivos específicos

- Autenticar usuários exclusivamente por meio do Spotify OAuth.
- Permitir a criação e o ingresso em salas efêmeras por código curto.
- Obter automaticamente os principais artistas e músicas dos integrantes.
- Capturar a ocasião e o humor atual do grupo.
- Calcular a compatibilidade musical entre os participantes.
- Gerar e pontuar um conjunto de músicas candidatas.
- Evitar que a preferência da maioria elimine a representação das minorias.
- Oferecer os modos de consenso Democrático e Festa Segura.
- Criar uma playlist privada de 20 a 30 músicas na conta do host.
- Apresentar explicações compreensíveis e compatíveis com a privacidade.
- Coletar feedback para apoiar futuras evoluções do produto.

## 6. Público-alvo

O público-alvo é formado por grupos pequenos, de uma a cinco pessoas, que desejam criar uma playlist conjunta para situações como festas, viagens, estudos, academias ou encontros sociais. O MVP é direcionado a usuários do Spotify previamente autorizados no aplicativo em Development Mode e com as condições de conta exigidas pela plataforma para a demonstração.

Também são partes interessadas a equipe de desenvolvimento, o professor da disciplina e avaliadores acadêmicos, responsáveis por verificar a adequação do processo de Engenharia de Software e a qualidade do incremento entregue.

## 7. Personas

### 7.1 Persona 1 — Marina, a anfitriã

- **Idade:** 24 anos.
- **Ocupação/contexto:** estudante universitária que organiza encontros com amigos.
- **Objetivo:** criar rapidamente uma playlist que funcione para todos durante uma festa.
- **Necessidade:** transformar a ocasião e os gostos do grupo em uma playlist pronta no Spotify.
- **Dificuldade:** perde tempo negociando músicas e costuma receber reclamações quando escolhe apenas seus próprios hits.
- **Uso do produto:** cria a sala, informa o contexto, escolhe o modo de consenso, acompanha a entrada dos convidados e solicita a geração da playlist.

### 7.2 Persona 2 — Rafael, o convidado com gosto minoritário

- **Idade:** 27 anos.
- **Ocupação/contexto:** desenvolvedor de software que participa de viagens e reuniões com amigos.
- **Objetivo:** sentir que seu gosto musical foi considerado sem precisar controlar a playlist.
- **Necessidade:** ter alguma representação e evitar músicas pelas quais possui forte rejeição.
- **Dificuldade:** seus gêneros favoritos diferem dos da maioria e normalmente desaparecem de playlists coletivas.
- **Uso do produto:** entra pelo código da sala, autentica-se, responde ao Vibe Check e consulta a explicação de justiça do resultado.

### 7.3 Persona 3 — Lucas, o participante casual

- **Idade:** 21 anos.
- **Ocupação/contexto:** estudante que usa o Spotify diariamente, mas não deseja preencher formulários longos.
- **Objetivo:** participar da criação da playlist com o menor esforço possível.
- **Necessidade:** permitir que o sistema obtenha suas preferências automaticamente.
- **Dificuldade:** abandona aplicações que exigem cadastros adicionais ou questionários extensos.
- **Uso do produto:** autentica-se pelo Spotify, entra na sala, pula ou responde rapidamente ao Vibe Check e acessa a playlist final.

## 8. Estrutura utilizada nos itens do backlog

Cada item do backlog contém:

- identificador único no padrão `PB-XX`;
- nome da funcionalidade;
- épico relacionado;
- história no formato “Como [...], quero [...], para [...]”;
- descrição funcional;
- entre três e seis critérios de aceitação verificáveis;
- prioridade Alta, Média ou Baixa;
- estimativa relativa em pontos de história;
- dependências;
- sprint sugerida;
- status inicial.

As estimativas utilizam a sequência de Fibonacci: 1, 2, 3, 5, 8, 13 e 21. Os pontos representam esforço relativo, complexidade e incerteza; não correspondem diretamente a horas. Adotou-se como premissa uma capacidade aproximada de **25 pontos por sprint de duas semanas**, pois a velocidade histórica da equipe não foi informada.

## 9. Épicos do produto

| ID | Épico | Descrição |
|---|---|---|
| EP-01 | Fundação e qualidade | Estrutura técnica, banco de dados, migrações, testes e documentação necessários ao desenvolvimento sustentável. |
| EP-02 | Autenticação e privacidade | Identidade por Spotify OAuth, sessão segura, logout e remoção de dados. |
| EP-03 | Salas e colaboração | Criação de salas efêmeras, entrada por código, papéis e acompanhamento dos integrantes. |
| EP-04 | Contexto e preferências | Contexto informado pelo host, Vibe Check e snapshots musicais. |
| EP-05 | Negociação e recomendação | Modelagem de gosto, pool de candidatas, scoring, rejeição, justiça e modos de consenso. |
| EP-06 | Integrações e geração | Integrações com Spotify, LLM e Last.fm, controle da geração e criação da playlist. |
| EP-07 | Experiência e explicabilidade | Sequenciamento, tela de resultado, explicações e feedback. |
| EP-08 | Evolução do produto | Funcionalidades previstas para versões posteriores, como descoberta e agrupamento de gostos. |

## 10. Backlog detalhado

### PB-01 — Fundação técnica do produto

- **Épico:** EP-01 — Fundação e qualidade.
- **História:** Como membro da equipe de desenvolvimento, quero uma estrutura integrada de frontend, backend e banco de dados, para implementar as funcionalidades do produto de forma incremental.
- **Descrição:** Preparar os projetos React/Vite e FastAPI, banco PostgreSQL, SQLAlchemy, Alembic e configuração local do ambiente.
- **Critérios de aceitação:**
  1. O frontend e o backend devem iniciar no ambiente local conforme instruções documentadas.
  2. O backend deve estabelecer conexão com o PostgreSQL.
  3. Uma migração inicial do Alembic deve ser executada e revertida sem erro.
  4. Configurações sensíveis devem ser obtidas por variáveis de ambiente e não versionadas.
- **Prioridade:** Alta.
- **Estimativa:** 2 pontos.
- **Dependências:** Nenhuma.
- **Sprint sugerida:** Sprint 1.
- **Status inicial:** A fazer.

### PB-02 — Autenticação com Spotify

- **Épico:** EP-02 — Autenticação e privacidade.
- **História:** Como usuário, quero entrar com minha conta Spotify, para participar das salas sem criar uma nova senha.
- **Descrição:** Implementar o fluxo Spotify OAuth, persistência segura dos tokens e sessão da aplicação por cookie.
- **Critérios de aceitação:**
  1. O sistema deve redirecionar o usuário para a autorização oficial do Spotify.
  2. O callback deve rejeitar uma resposta com parâmetro `state` ausente ou inválido.
  3. Uma autorização válida deve criar ou atualizar o usuário e iniciar uma sessão da aplicação.
  4. Access token e refresh token não devem ser enviados ao frontend nem registrados em logs.
  5. Os tokens armazenados devem estar criptografados em repouso.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-01.
- **Sprint sugerida:** Sprint 1.
- **Status inicial:** A fazer.

### PB-03 — Logout e remoção de dados

- **Épico:** EP-02 — Autenticação e privacidade.
- **História:** Como usuário, quero encerrar minha sessão e remover meus dados, para manter controle sobre minha privacidade.
- **Descrição:** Disponibilizar encerramento da sessão e fluxo de exclusão ou anonimização dos dados mantidos pelo sistema.
- **Critérios de aceitação:**
  1. O logout deve invalidar a sessão da aplicação no backend.
  2. Após o logout, rotas autenticadas devem responder como não autorizadas.
  3. A solicitação de remoção deve excluir ou anonimizar os dados pessoais previstos pela política do produto.
  4. A operação não deve expor tokens ou informações de outros integrantes.
- **Prioridade:** Média.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-02.
- **Sprint sugerida:** Sprint 4.
- **Status inicial:** A fazer.

### PB-04 — Criação de sala efêmera

- **Épico:** EP-03 — Salas e colaboração.
- **História:** Como host, quero criar uma sala com um código curto, para convidar outras pessoas a participar da negociação musical.
- **Descrição:** Criar uma sala temporária, associar o criador como host e gerar um código compartilhável.
- **Critérios de aceitação:**
  1. Apenas um usuário autenticado deve poder criar uma sala.
  2. Cada sala deve receber um código curto único.
  3. O criador deve ser registrado como host e primeiro integrante.
  4. A sala deve receber data de expiração de 24 horas após sua criação.
  5. O sistema deve retornar o código e os dados iniciais da sala.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-01 e PB-02.
- **Sprint sugerida:** Sprint 1.
- **Status inicial:** A fazer.

### PB-05 — Entrada e acompanhamento da sala

- **Épico:** EP-03 — Salas e colaboração.
- **História:** Como convidado, quero entrar em uma sala pelo código e visualizar seus integrantes, para saber quando o grupo está pronto.
- **Descrição:** Permitir entrada por código, impedir duplicidade e atualizar integrantes e estado da sala por polling.
- **Critérios de aceitação:**
  1. O sistema deve rejeitar código inexistente ou sala expirada.
  2. A sala deve aceitar no máximo cinco integrantes.
  3. O mesmo usuário não deve ser associado duas vezes à mesma sala.
  4. Apenas membros da sala devem consultar seus dados; os demais devem receber resposta 403.
  5. A interface deve atualizar integrantes e estado por polling a cada três a cinco segundos.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-02 e PB-04.
- **Sprint sugerida:** Sprint 1.
- **Status inicial:** A fazer.

### PB-06 — Contexto e modo de consenso

- **Épico:** EP-04 — Contexto e preferências.
- **História:** Como host, quero informar a ocasião, uma descrição e o modo de consenso, para adequar a playlist ao momento do grupo.
- **Descrição:** Armazenar o contexto livre e oferecer os modos Democrático e Festa Segura.
- **Critérios de aceitação:**
  1. Somente o host deve poder alterar o contexto e o modo da sala.
  2. O sistema deve aceitar ocasião, descrição livre ou ambos.
  3. O modo selecionado deve ser Democrático ou Festa Segura.
  4. As alterações devem ficar disponíveis para os integrantes na próxima atualização da sala.
- **Prioridade:** Alta.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-04.
- **Sprint sugerida:** Sprint 1.
- **Status inicial:** A fazer.

### PB-07 — Vibe Check opcional

- **Épico:** EP-04 — Contexto e preferências.
- **História:** Como integrante, quero responder ou pular um questionário curto, para expressar meu humor e minhas preferências do momento.
- **Descrição:** Apresentar de três a cinco perguntas gamificadas e converter as respostas em variáveis normalizadas para o motor.
- **Critérios de aceitação:**
  1. O questionário deve apresentar no mínimo três e no máximo cinco perguntas.
  2. O usuário deve poder pular o questionário sem bloquear a geração.
  3. As respostas devem ser armazenadas por usuário e sala.
  4. As preferências derivadas devem possuir valores entre 0 e 1.
  5. Uma nova resposta do mesmo usuário deve atualizar sua participação na geração seguinte.
- **Prioridade:** Média.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-05 e PB-06.
- **Sprint sugerida:** Sprint 3.
- **Status inicial:** A fazer.

### PB-08 — Coleta e cache de dados musicais

- **Épico:** EP-04 — Contexto e preferências.
- **História:** Como integrante, quero que meus principais artistas e músicas sejam obtidos automaticamente, para participar sem preencher preferências manualmente.
- **Descrição:** Consultar top artists e top tracks do Spotify e armazenar snapshots com validade configurável.
- **Critérios de aceitação:**
  1. O sistema deve consultar apenas os endpoints Spotify autorizados no escopo do MVP.
  2. Faixas e artistas obtidos devem ser associados ao usuário em um snapshot.
  3. Um snapshot com menos de sete dias deve ser reutilizado por padrão.
  4. Um snapshot vencido deve ser atualizado antes da geração.
  5. Falha de renovação do token deve marcar a necessidade de nova autenticação.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-02.
- **Sprint sugerida:** Sprint 1.
- **Status inicial:** A fazer.

### PB-09 — Modelagem de gosto e compatibilidade

- **Épico:** EP-05 — Negociação e recomendação.
- **História:** Como integrante, quero que o sistema modele meu gosto e calcule a compatibilidade do grupo, para representar as afinidades e diferenças existentes.
- **Descrição:** Construir perfis temporários com faixas, artistas, gêneros e medidas de similaridade entre os participantes.
- **Critérios de aceitação:**
  1. O modelo individual deve considerar faixas, artistas e gêneros disponíveis no snapshot.
  2. O cálculo deve tratar corretamente listas vazias e grupos com apenas um integrante.
  3. A compatibilidade deve resultar em valor normalizado e reproduzível para a mesma entrada.
  4. O motor não deve realizar chamadas de rede durante o cálculo.
- **Prioridade:** Alta.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-05 e PB-08.
- **Sprint sugerida:** Sprint 2.
- **Status inicial:** A fazer.

### PB-10 — Geração do conjunto de candidatas

- **Épico:** EP-05 — Negociação e recomendação.
- **História:** Como grupo, queremos que o sistema reúna músicas relacionadas aos nossos gostos, para formar uma base equilibrada de possíveis escolhas.
- **Descrição:** Construir o pool de candidatas a partir das músicas e artistas fortes dos integrantes e de fontes contextuais permitidas.
- **Critérios de aceitação:**
  1. O conjunto deve incluir contribuições dos diferentes integrantes quando houver dados disponíveis.
  2. Uma mesma música não deve aparecer mais de uma vez no conjunto.
  3. A origem de cada candidata deve ser registrada.
  4. Candidatas sem identificação suficiente para busca posterior devem ser descartadas com motivo.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-06 e PB-09.
- **Sprint sugerida:** Sprint 2.
- **Status inicial:** A fazer.

### PB-11 — Pontuação individual e coletiva

- **Épico:** EP-05 — Negociação e recomendação.
- **História:** Como grupo, queremos que cada candidata seja avaliada individual e coletivamente, para selecionar músicas adequadas ao conjunto de participantes.
- **Descrição:** Implementar as fórmulas configuráveis de afinidade individual e score de grupo definidas para o PNE.
- **Critérios de aceitação:**
  1. O score individual deve considerar afinidade de faixa, artista, gênero ou tag, popularidade e novidade disponíveis.
  2. O score de grupo deve considerar média, menor score individual, cobertura, contexto e diversidade.
  3. Os pesos devem permanecer centralizados e configuráveis.
  4. A mesma entrada e configuração devem produzir o mesmo resultado.
  5. Os cálculos principais devem possuir testes automatizados com valores esperados.
- **Prioridade:** Alta.
- **Estimativa:** 8 pontos.
- **Dependências:** PB-09 e PB-10.
- **Sprint sugerida:** Sprint 2.
- **Status inicial:** A fazer.

### PB-12 — Rejeição, justiça e modos de consenso

- **Épico:** EP-05 — Negociação e recomendação.
- **História:** Como integrante, quero que minhas rejeições e preferências minoritárias sejam consideradas, para não ser ignorado pela preferência média do grupo.
- **Descrição:** Aplicar penalidades de rejeição, least misery, cobertura, representação mínima e perfis de peso dos modos de consenso.
- **Critérios de aceitação:**
  1. Uma rejeição forte deve reduzir o score da música mesmo quando ela agradar à maioria.
  2. O sistema deve calcular satisfação média, menor satisfação, cobertura e fairness score.
  3. O modo Democrático deve atribuir o mesmo peso aos integrantes.
  4. O modo Festa Segura deve favorecer familiaridade e baixa rejeição.
  5. A seleção deve tentar elevar o integrante menos representado sem reduzir excessivamente a satisfação do grupo.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-11. Quando PB-07 estiver disponível, suas respostas serão usadas como entrada opcional, sem bloquear esta história.
- **Sprint sugerida:** Sprint 2.
- **Status inicial:** A fazer.

### PB-13 — Controle e histórico da geração

- **Épico:** EP-06 — Integrações e geração.
- **História:** Como host, quero solicitar a geração de forma segura, para que cliques repetidos não criem playlists duplicadas.
- **Descrição:** Criar uma execução de playlist por solicitação, controlar estados e impedir concorrência na mesma sala.
- **Critérios de aceitação:**
  1. A primeira solicitação válida deve criar uma execução com estado `running`.
  2. Uma solicitação concorrente na mesma sala deve retornar resposta 409.
  3. Uma execução concluída deve receber estado `completed` e uma falha deve receber estado `failed`.
  4. Após uma falha, o host deve poder iniciar uma nova execução controlada.
  5. Cada nova geração concluída deve possuir registro independente.
- **Prioridade:** Alta.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-05, PB-06 e PB-11.
- **Sprint sugerida:** Sprint 2.
- **Status inicial:** A fazer.

### PB-14 — Correspondência e criação da playlist no Spotify

- **Épico:** EP-06 — Integrações e geração.
- **História:** Como host, quero receber uma playlist real com músicas válidas na minha conta Spotify, para utilizá-la imediatamente.
- **Descrição:** Resolver candidatas pelo Spotify Search com o token do host, validar disponibilidade e criar a playlist privada.
- **Critérios de aceitação:**
  1. A busca deve usar o mercado associado ao token do host quando disponível.
  2. Título e artista devem ser normalizados para tratar variações como live, remastered e acoustic.
  3. Resultados abaixo da confiança mínima ou indisponíveis devem ser descartados com motivo registrado.
  4. A seleção final deve conter de 20 a 30 músicas e no máximo duas músicas por artista.
  5. A playlist deve ser privada por padrão e criada na conta do host.
  6. O identificador e a URL da playlist devem ser armazenados na execução correspondente.
- **Prioridade:** Alta.
- **Estimativa:** 8 pontos.
- **Dependências:** PB-02, PB-11, PB-12 e PB-13.
- **Sprint sugerida:** Sprint 3.
- **Status inicial:** A fazer.

### PB-15 — Resultado e explicabilidade

- **Épico:** EP-07 — Experiência e explicabilidade.
- **História:** Como integrante, quero visualizar o resultado e entender sua justiça, para avaliar se o grupo foi representado.
- **Descrição:** Exibir playlist, compatibilidade, métricas de justiça, representação e justificativas legíveis.
- **Critérios de aceitação:**
  1. A tela deve apresentar o link da playlist criada no Spotify.
  2. O resultado deve apresentar compatibilidade e fairness score da execução.
  3. A representação dos integrantes deve ser exibida em formato compreensível.
  4. Cada música selecionada deve possuir uma justificativa resumida.
  5. As explicações não devem identificar rejeições ou dados sensíveis de outro integrante.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-13 e PB-14.
- **Sprint sugerida:** Sprint 3.
- **Status inicial:** A fazer.

### PB-16 — Interpretação estruturada do contexto

- **Épico:** EP-06 — Integrações e geração.
- **História:** Como host, quero que minha descrição livre seja interpretada, para transformar a intenção do encontro em critérios musicais estruturados.
- **Descrição:** Integrar o LLM exclusivamente para interpretação de contexto, com schema validado e fallback determinístico.
- **Critérios de aceitação:**
  1. A saída deve seguir um schema JSON com ocasião, humor, energia, tags positivas, tags negativas e itens a evitar.
  2. Uma resposta inválida deve ser rejeitada sem interromper a geração.
  3. Na indisponibilidade do LLM, o sistema deve continuar usando consenso, afinidade e popularidade.
  4. Dados brutos de top tracks e top artists não devem ser enviados ao LLM.
  5. O LLM não deve decidir diretamente quais músicas compõem a playlist.
- **Prioridade:** Média.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-06 e PB-10.
- **Sprint sugerida:** Sprint 3.
- **Status inicial:** A fazer.

### PB-17 — Enriquecimento de contexto com Last.fm

- **Épico:** EP-06 — Integrações e geração.
- **História:** Como grupo, queremos que o contexto das candidatas seja avaliado, para que a playlist combine melhor com a ocasião.
- **Descrição:** Consultar tags do Last.fm, combinar gêneros do Spotify e armazenar resultados em cache com indicação de confiança.
- **Critérios de aceitação:**
  1. O sistema deve tentar tags da faixa antes das tags do artista.
  2. Na ausência de tags do Last.fm, deve utilizar gêneros do Spotify e os demais sinais disponíveis.
  3. Cada resultado deve registrar fonte e nível de confiança.
  4. Consultas repetidas devem reutilizar o cache enquanto válido.
  5. Resposta vazia ou erro do Last.fm não deve interromper a geração.
- **Prioridade:** Média.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-10 e PB-16.
- **Sprint sugerida:** Sprint 4.
- **Status inicial:** A fazer.

### PB-18 — Sequenciamento da experiência musical

- **Épico:** EP-07 — Experiência e explicabilidade.
- **História:** Como ouvinte, quero uma playlist com fluxo coerente, para evitar uma sequência desorganizada de músicas bem pontuadas.
- **Descrição:** Ordenar a seleção final com regras simples de abertura, risco, alternância e repetição de artistas.
- **Critérios de aceitação:**
  1. Duas músicas do mesmo artista não devem ficar consecutivas.
  2. A playlist deve começar com uma música de alta aceitação.
  3. Músicas de maior risco devem ser posicionadas preferencialmente na parte intermediária.
  4. O sequenciador deve respeitar o limite máximo de duas músicas por artista.
- **Prioridade:** Média.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-12 e PB-14.
- **Sprint sugerida:** Sprint 4.
- **Status inicial:** A fazer.

### PB-19 — Feedback pós-playlist

- **Épico:** EP-07 — Experiência e explicabilidade.
- **História:** Como integrante, quero avaliar faixas e a playlist, para registrar minha satisfação e meu nível de representação.
- **Descrição:** Coletar feedback por música e notas gerais, sem utilizar os dados no ranqueamento do MVP.
- **Critérios de aceitação:**
  1. O integrante deve poder marcar like, dislike, more like this ou never again por faixa.
  2. O integrante deve poder informar satisfação e representação da playlist.
  3. O feedback deve ser associado ao usuário e à execução correta.
  4. Um usuário não deve registrar feedback em uma execução de sala da qual não participa.
  5. O sistema deve deixar explícito que o feedback será utilizado em evoluções futuras.
- **Prioridade:** Média.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-15.
- **Sprint sugerida:** Sprint 4.
- **Status inicial:** A fazer.

### PB-20 — Qualidade, robustez e documentação

- **Épico:** EP-01 — Fundação e qualidade.
- **História:** Como equipe de desenvolvimento, queremos validar o produto e documentar seu uso, para entregar um incremento verificável e passível de manutenção.
- **Descrição:** Consolidar testes automatizados, fallbacks, proteção de dados, documentação técnica e roteiro de demonstração.
- **Critérios de aceitação:**
  1. O motor deve possuir testes para scoring, justiça, rejeição, duplicidade e limite por artista.
  2. A API deve possuir testes para autorização, entrada duplicada e Generation Lock.
  3. Clientes externos devem possuir testes mockados para token expirado, resposta 429, JSON inválido e busca sem resultado.
  4. Nenhum teste ou log deve expor tokens reais.
  5. O README deve conter instruções atualizadas de configuração e execução.
  6. Um roteiro de demonstração do fluxo principal deve ser documentado.
- **Prioridade:** Alta.
- **Estimativa:** 8 pontos.
- **Dependências:** PB-02 a PB-19, sendo executado continuamente durante todas as sprints.
- **Sprint sugerida:** Sprint 4 para consolidação.
- **Status inicial:** A fazer.

### PB-21 — Modo Descoberta

- **Épico:** EP-08 — Evolução do produto.
- **História:** Como grupo, queremos um modo que favoreça músicas novas, para descobrir faixas sem abandonar completamente o consenso.
- **Descrição:** Criar um perfil de pesos que aumente novidade e diversidade, mantendo limites de rejeição e justiça.
- **Critérios de aceitação:**
  1. O modo deve ser selecionável apenas quando estiver habilitado na configuração do produto.
  2. A novidade deve possuir peso superior ao utilizado no modo Democrático.
  3. Rejeições fortes e representação mínima devem continuar sendo consideradas.
  4. O resultado deve explicar que o modo favoreceu descoberta musical.
- **Prioridade:** Baixa.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-11, PB-12 e PB-15.
- **Sprint sugerida:** Versão futura.
- **Status inicial:** A fazer.

### PB-22 — Agrupamento de gostos e faixas-ponte

- **Épico:** EP-08 — Evolução do produto.
- **História:** Como grupo com gostos divergentes, queremos que o sistema identifique subgrupos e músicas intermediárias, para reduzir a distância entre preferências muito diferentes.
- **Descrição:** Agrupar perfis semelhantes e alternar consenso geral, representações dos subgrupos e possíveis faixas-ponte.
- **Critérios de aceitação:**
  1. O agrupamento deve utilizar somente dados musicais autorizados e temporários.
  2. O sistema deve identificar quando não há evidência suficiente para formar subgrupos.
  3. A seleção deve limitar a predominância de um único subgrupo.
  4. A explicação deve indicar, de forma agregada, quando uma faixa atua como ponte musical.
  5. A funcionalidade não deve alterar o comportamento dos modos existentes quando estiver desabilitada.
- **Prioridade:** Baixa.
- **Estimativa:** 13 pontos.
- **Dependências:** PB-09, PB-11, PB-12 e PB-15.
- **Sprint sugerida:** Versão futura.
- **Status inicial:** A fazer.

## 11. Backlog resumido e priorizado

| Ordem | ID | Épico | Item | Prioridade | Pontos | Dependências | Sprint | Status |
|---:|---|---|---|---|---:|---|---|---|
| 1 | PB-01 | EP-01 | Fundação técnica | Alta | 2 | Nenhuma | Sprint 1 | A fazer |
| 2 | PB-02 | EP-02 | Autenticação Spotify | Alta | 5 | PB-01 | Sprint 1 | A fazer |
| 3 | PB-04 | EP-03 | Criação de sala | Alta | 5 | PB-01, PB-02 | Sprint 1 | A fazer |
| 4 | PB-05 | EP-03 | Entrada e acompanhamento | Alta | 5 | PB-02, PB-04 | Sprint 1 | A fazer |
| 5 | PB-06 | EP-04 | Contexto e consenso | Alta | 3 | PB-04 | Sprint 1 | A fazer |
| 6 | PB-08 | EP-04 | Dados musicais | Alta | 5 | PB-02 | Sprint 1 | A fazer |
| 7 | PB-09 | EP-05 | Modelagem e compatibilidade | Alta | 3 | PB-05, PB-08 | Sprint 2 | A fazer |
| 8 | PB-10 | EP-05 | Pool de candidatas | Alta | 5 | PB-06, PB-09 | Sprint 2 | A fazer |
| 9 | PB-11 | EP-05 | Pontuação | Alta | 8 | PB-09, PB-10 | Sprint 2 | A fazer |
| 10 | PB-12 | EP-05 | Rejeição e justiça | Alta | 5 | PB-11 | Sprint 2 | A fazer |
| 11 | PB-13 | EP-06 | Controle da geração | Alta | 3 | PB-05, PB-06, PB-11 | Sprint 2 | A fazer |
| 12 | PB-07 | EP-04 | Vibe Check | Média | 5 | PB-05, PB-06 | Sprint 3 | A fazer |
| 13 | PB-14 | EP-06 | Playlist no Spotify | Alta | 8 | PB-02, PB-11, PB-12, PB-13 | Sprint 3 | A fazer |
| 14 | PB-15 | EP-07 | Resultado e explicabilidade | Alta | 5 | PB-13, PB-14 | Sprint 3 | A fazer |
| 15 | PB-16 | EP-06 | Contexto por LLM | Média | 5 | PB-06, PB-10 | Sprint 3 | A fazer |
| 16 | PB-03 | EP-02 | Logout e remoção | Média | 3 | PB-02 | Sprint 4 | A fazer |
| 17 | PB-17 | EP-06 | Contexto Last.fm | Média | 5 | PB-10, PB-16 | Sprint 4 | A fazer |
| 18 | PB-18 | EP-07 | Sequenciamento | Média | 3 | PB-12, PB-14 | Sprint 4 | A fazer |
| 19 | PB-19 | EP-07 | Feedback | Média | 3 | PB-15 | Sprint 4 | A fazer |
| 20 | PB-20 | EP-01 | Qualidade e documentação | Alta | 8 | PB-02 a PB-19 | Sprint 4 | A fazer |
| 21 | PB-21 | EP-08 | Modo Descoberta | Baixa | 5 | PB-11, PB-12, PB-15 | Futuro | A fazer |
| 22 | PB-22 | EP-08 | Agrupamento e faixas-ponte | Baixa | 13 | PB-09, PB-11, PB-12, PB-15 | Futuro | A fazer |

### 11.1 Totais

- **Total de histórias/itens:** 22.
- **Total geral:** 112 pontos.
- **Prioridade Alta:** 14 itens, totalizando 70 pontos.
- **Prioridade Média:** 6 itens, totalizando 24 pontos.
- **Prioridade Baixa:** 2 itens, totalizando 18 pontos.
- **Sprint 1:** 25 pontos.
- **Sprint 2:** 24 pontos.
- **Sprint 3:** 23 pontos.
- **Sprint 4:** 22 pontos.
- **Versões futuras:** 18 pontos.

## 12. Definição do Produto Mínimo Viável — MVP

O MVP é composto por `PB-01`, `PB-02`, `PB-04`, `PB-05`, `PB-06`, `PB-08`, `PB-09`, `PB-10`, `PB-11`, `PB-12`, `PB-13`, `PB-14` e `PB-15`, com apoio contínuo das práticas de qualidade de `PB-20`.

Esses itens permitem executar o fluxo principal:

1. autenticar os participantes;
2. criar e preencher uma sala;
3. informar o contexto e o modo;
4. obter os gostos musicais;
5. calcular compatibilidade e pontuações;
6. aplicar rejeição e justiça;
7. gerar uma playlist real no Spotify;
8. explicar o resultado.

A hipótese validada pelo MVP é: **um motor que considera contexto, menor satisfação individual e representação produz uma playlist coletiva percebida como mais justa do que uma simples mistura ou média dos históricos musicais**.

Vibe Check, interpretação pelo LLM, tags do Last.fm, sequenciamento avançado e feedback são importantes para o MVP completo descrito no README, mas não são indispensáveis para a primeira validação técnica da hipótese. Modo Descoberta e agrupamento de gostos permanecem em versões futuras.

O núcleo do MVP possui 67 pontos nominais, sem contar integralmente a consolidação de PB-20. Com capacidade assumida de 25 pontos por sprint, são necessárias aproximadamente três sprints de duas semanas. Portanto, o prazo original de cerca de um mês exige aumento comprovado de velocidade, paralelização segura ou redução adicional de escopo. Essa decisão deve ser tomada após a equipe medir sua velocidade na primeira sprint.

## 13. Critérios de priorização

Os itens foram priorizados pelos seguintes critérios:

1. **Valor para a hipótese do produto:** funções que demonstram negociação musical e justiça recebem prioridade superior.
2. **Dependência técnica:** infraestrutura, autenticação, salas e dados musicais antecedem o motor e a geração.
3. **Risco:** integrações com Spotify e regras centrais são antecipadas para revelar problemas cedo.
4. **Obrigatoriedade do fluxo:** itens sem os quais não existe uma playlist utilizável são classificados como Alta.
5. **Experiência complementar:** recursos que enriquecem, mas não desbloqueiam o fluxo principal, são classificados como Média.
6. **Evolução futura:** funcionalidades fora do prazo e do núcleo do MVP recebem prioridade Baixa.

## 14. Definition of Ready — DoR

Uma história está pronta para entrar em uma sprint quando:

- possui história de usuário, descrição e valor esperado compreensíveis;
- apresenta entre três e seis critérios de aceitação objetivos;
- tem dependências identificadas e concluídas ou planejadas antes dela;
- possui estimativa acordada pela equipe;
- não contém dúvidas de negócio que impeçam a implementação;
- integrações externas necessárias foram verificadas ou possuem estratégia de mock;
- dados, regras e exceções relevantes estão identificados;
- o item cabe em uma sprint ou foi dividido.

## 15. Definition of Done — DoD

Uma história é considerada concluída quando:

- todos os critérios de aceitação foram atendidos;
- o código foi revisado por pelo menos outro integrante;
- testes automatizados pertinentes foram criados e aprovados;
- testes regressivos existentes continuam aprovados;
- migrações e configurações necessárias foram documentadas;
- nenhum token ou segredo foi incluído no código ou nos logs;
- mensagens de erro e fallbacks relevantes foram verificados;
- a funcionalidade foi integrada ao incremento principal;
- a documentação afetada foi atualizada;
- o Product Owner ou representante acadêmico aceitou o resultado demonstrado.

## 16. Dependências entre funcionalidades

| Funcionalidade | Depende de | Justificativa |
|---|---|---|
| Autenticação | Fundação | Requer backend, configuração e persistência. |
| Criação de sala | Fundação e autenticação | O host precisa estar identificado. |
| Entrada na sala | Autenticação e criação de sala | Exige usuário e sala existentes. |
| Contexto | Criação de sala | O contexto pertence a uma sala. |
| Dados musicais | Autenticação | Requer autorização Spotify válida. |
| Modelagem | Sala e dados musicais | Usa os integrantes e seus snapshots. |
| Pool de candidatas | Contexto e modelagem | Usa preferências e ocasião disponíveis. |
| Pontuação | Modelagem e candidatas | Avalia as músicas para cada perfil. |
| Justiça | Pontuação | Ajusta resultados individuais e coletivos. |
| Controle da geração | Sala e pontuação | Orquestra uma execução do motor. |
| Playlist Spotify | Pontuação, justiça e controle | Usa a seleção final e o token do host. |
| Resultado | Execução e playlist | Apresenta métricas e saída persistida. |
| LLM | Contexto e candidatas | Converte intenção em critérios auxiliares. |
| Last.fm | Candidatas e contexto estruturado | Enriquece as músicas com tags. |
| Sequenciamento | Seleção e playlist | Ordena o conjunto final já validado. |
| Feedback | Resultado | Avalia uma execução concluída. |

Fluxo principal de dependências:

`Fundação → Autenticação → Sala → Dados musicais → Modelagem → Candidatas → Pontuação → Justiça → Geração → Playlist → Resultado`

## 17. Riscos do projeto

| ID | Risco | Probabilidade | Impacto | Estratégia de mitigação |
|---|---|---|---|---|
| R-01 | Limite de cinco usuários autorizados no Spotify Development Mode | Alta | Alto | Pré-cadastrar contas da demonstração e iniciar cedo a avaliação de Extended Quota Mode. |
| R-02 | Endpoints Spotify indisponíveis ou restritos para novos aplicativos | Média | Alto | Realizar spike técnico e não depender de Recommendations, Audio Features ou Audio Analysis. |
| R-03 | Expiração ou falha de renovação do token | Média | Alto | Centralizar refresh, marcar reautenticação necessária e testar falhas do fluxo. |
| R-04 | Música indisponível no mercado do host | Alta | Médio | Buscar com o token do host, validar mercado e manter candidatas substitutas. |
| R-05 | Correspondência com versão incorreta da música | Média | Médio | Normalizar título e artista, exigir confiança mínima e registrar descarte. |
| R-06 | Resposta inválida ou indisponibilidade do LLM | Média | Médio | Validar schema e manter fallback determinístico sem IA. |
| R-07 | Ausência de tags no Last.fm | Alta | Baixo | Aplicar cascata para tags do artista, gêneros Spotify e sinais de consenso. |
| R-08 | Vazamento de tokens ou preferências pessoais | Baixa | Alto | Criptografia, cookies seguros, logs sanitizados e revisão de segurança. |
| R-09 | Gerações duplicadas por concorrência | Média | Alto | Generation Lock, estado transacional e resposta 409. |
| R-10 | Backlog incompatível com o prazo de um mês | Alta | Alto | Medir velocidade na primeira sprint, reduzir escopo ou renegociar prazo. |
| R-11 | Questionário causar abandono | Média | Médio | Limitar a cinco perguntas e permitir que o usuário pule. |
| R-12 | Maioria dominar a seleção | Média | Alto | Usar least misery, cobertura, rejeição e testes com grupos divergentes. |
| R-13 | Falta de dados musicais de um integrante | Média | Médio | Tratar listas vazias, informar limitação e utilizar os demais sinais disponíveis. |
| R-14 | Crescimento não controlado do escopo | Alta | Alto | Manter itens futuros fora do MVP e exigir refinamento antes de promoção. |

## 18. Regras para atualização e refinamento do backlog

- O Product Owner deve revisar prioridades antes de cada planejamento de sprint.
- Histórias podem ser detalhadas progressivamente, mas não devem entrar na sprint sem atender à DoR.
- Novas funcionalidades devem indicar valor, critérios de aceitação, dependências e impacto no MVP.
- Alterações de escopo devem atualizar histórias relacionadas, totais e dependências.
- Histórias acima de 13 pontos devem ser obrigatoriamente decompostas.
- A velocidade deve ser recalculada ao final de cada sprint usando apenas itens concluídos pela DoD.
- Itens não concluídos retornam ao backlog e devem ser reestimados quando necessário; a sprint não deve ser estendida.
- Critérios de aceitação não devem ser removidos apenas para declarar uma história concluída.
- Riscos e restrições de serviços externos devem ser revisados em cada refinamento.
- Itens de prioridade Baixa só devem ser promovidos quando o MVP estiver estável ou quando houver decisão explícita de escopo.

## 19. Considerações finais

O backlog organiza o desenvolvimento do Vibe Check de forma incremental e rastreável. As histórias iniciais estabelecem a infraestrutura, a autenticação, as salas e a coleta de dados. Em seguida, o motor determinístico implementa o diferencial acadêmico do produto: negociar preferências em vez de calcular apenas uma média.

A priorização preserva um caminho demonstrável até a criação de uma playlist real no Spotify. Recursos de contexto por LLM, tags do Last.fm, sequenciamento e feedback complementam a experiência, mas possuem fallbacks ou podem ser postergados durante a validação inicial.

As estimativas são relativas e devem ser refinadas com base na velocidade observada. A diferença entre o prazo aproximado de um mês e o esforço estimado do MVP representa um risco que deve ser tratado por negociação de escopo, não por extensão informal das sprints ou redução dos critérios de qualidade.

## 20. Referências utilizadas

- README do projeto Group Music Recommender — Vibe Check, seções anteriores ao tópico 4.
- ELIAS, Gledson. *Desenvolvimento Ágil*. Material da disciplina de Engenharia de Software.
- ELIAS, Gledson. *Engenharia de Requisitos*. Material da disciplina de Engenharia de Software.
