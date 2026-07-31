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
| Versão | 1.1 |
| Data | 31 de julho de 2026 |
| Status | Refinado até a Sprint 7 |

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
| EP-09 | Biblioteca musical ampliada | Sincroniza Tops e playlists elegíveis com cache limitado, resiliência de quota e sinais ponderados de gosto. |

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

### PB-14 — Correspondência das músicas no Spotify

- **Épico:** EP-06 — Integrações e geração.
- **História:** Como grupo, queremos que as músicas candidatas sejam corretamente identificadas no Spotify, para que apenas faixas válidas sejam utilizadas na playlist.
- **Descrição:** Resolver as músicas candidatas usando o Spotify Search, normalizando títulos e artistas, validando disponibilidade e descartando resultados ambíguos ou indisponíveis.
- **Critérios de aceitação:**
  1. A busca deve usar o mercado associado ao token do host quando disponível.
  2. Título e artista devem ser normalizados para tratar variações como live, remastered e acoustic.
  3. Resultados abaixo da confiança mínima devem ser descartados com o motivo registrado.
  4. Músicas indisponíveis para o mercado do host não devem ser selecionadas.
  5. Cada música válida deve possuir o identificador Spotify associado.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-02, PB-11, PB-12 e PB-13.
- **Sprint sugerida:** Sprint 3.
- **Status inicial:** A fazer.

### PB-15 — Criação da playlist no Spotify

- **Épico:** EP-06 — Integrações e geração.
- **História:** Como host, quero que a playlist seja criada automaticamente na minha conta Spotify, para utilizá-la imediatamente.
- **Descrição:** Criar uma playlist privada contendo as músicas selecionadas pelo motor de recomendação e registrar sua execução.
- **Critérios de aceitação:**
  1. A playlist deve conter entre 20 e 30 músicas.
  2. Deve haver no máximo duas músicas por artista.
  3. A playlist deve ser criada como privada por padrão.
  4. O identificador e a URL da playlist devem ser armazenados na execução correspondente.
  5. O host deve receber o link da playlist criada.
- **Prioridade:** Alta.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-14.
- **Sprint sugerida:** Sprint 3.
- **Status inicial:** A fazer.

### PB-16 — Resultado e explicabilidade

- **Épico:** EP-07 — Experiência e explicabilidade.
- **História:** Como integrante, quero visualizar o resultado e entender sua justiça, para avaliar se o grupo foi representado.
- **Descrição:** Exibir playlist, compatibilidade, métricas de justiça, representação e justificativas legíveis.
- **Critérios de aceitação:**
  1. A tela deve apresentar o link da playlist criada no Spotify.
  2. O resultado deve apresentar compatibilidade e fairness score da execução.
  3. A representação dos integrantes deve ser exibida em formato compreensível.
  4. Cada música selecionada deve possuir uma justificativa resumida.
  5. As explicações não devem identificar rejeições ou dados sensíveis de outro integrante.
- **Prioridade:** Média.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-13, PB-14 e PB-15.
- **Sprint sugerida:** Sprint 3.
- **Status inicial:** A fazer.

### PB-17 — Interpretação estruturada do contexto

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

### PB-18 — Enriquecimento de contexto com Last.fm

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
- **Dependências:** PB-10 e PB-17.
- **Sprint sugerida:** Sprint 4.
- **Status inicial:** A fazer.

### PB-19 — Sequenciamento da experiência musical

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
- **Dependências:** PB-12, PB-14 e PB-15.
- **Sprint sugerida:** Sprint 4.
- **Status inicial:** A fazer.

### PB-20 — Feedback pós-playlist

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
- **Dependências:** PB-16.
- **Sprint sugerida:** Sprint 4.
- **Status inicial:** A fazer.

> **Qualidade, robustez e documentação** deixou de ser um PB (antigo PB-20) e passou a ser a
> **Definition of Done** — testes de motor/API/clientes mockados, não exposição de tokens, README
> atualizado e roteiro de demonstração são requisitos de **todos** os PBs, verificados a cada entrega.

### PB-21 — Modo Descoberta *(pós-MVP)*

- **Épico:** EP-08 — Evolução do produto.
- **História:** Como grupo, queremos um modo que favoreça músicas novas, para descobrir faixas sem abandonar completamente o consenso.
- **Descrição:** Criar um perfil de pesos que aumente a novidade e diversidade, mantendo limites de rejeição e justiça.
- **Critérios de aceitação:**
  1. O modo deve ser selecionável apenas quando estiver habilitado na configuração do produto.
  2. A novidade deve possuir peso superior ao utilizado no modo Democrático.
  3. Rejeições fortes e representação mínima devem continuar sendo consideradas.
  4. O resultado deve explicar que o modo favoreceu a descoberta musical.
- **Prioridade:** Baixa.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-11, PB-12 e PB-16.
- **Sprint sugerida:** Sprint 5.
- **Status inicial:** A fazer.

### PB-22 — Agrupamento de perfis musicais *(pós-MVP)*

- **Épico:** EP-05 — Negociação e recomendação.
- **História:** Como grupo com gostos diferentes, queremos que o sistema identifique subgrupos de afinidade, para compreender melhor a diversidade de preferências.
- **Descrição:** Agrupar participantes com perfis musicais semelhantes utilizando apenas os dados autorizados pelo produto.
- **Critérios de aceitação:**
  1. O agrupamento deve utilizar apenas dados musicais temporários autorizados.
  2. O sistema deve identificar quando não houver evidências suficientes para formar subgrupos.
  3. O agrupamento deve produzir resultados determinísticos para a mesma entrada.
  4. Os subgrupos identificados devem ficar disponíveis para o motor de recomendação.
- **Prioridade:** Baixa.
- **Estimativa:** 4 pontos.
- **Dependências:** PB-09.
- **Sprint sugerida:** Sprint 5.
- **Status inicial:** A fazer.

### PB-23 — Identificação de músicas-ponte *(pós-MVP)*

- **Épico:** EP-05 — Negociação e recomendação.
- **História:** Como grupo, queremos que o sistema identifique músicas capazes de aproximar diferentes gostos musicais, para aumentar a aceitação coletiva.
- **Descrição:** Avaliar as músicas candidatas buscando aquelas que apresentam afinidade entre múltiplos subgrupos.
- **Critérios de aceitação:**
  1. O sistema deve identificar músicas com boa aceitação entre diferentes subgrupos.
  2. As músicas-ponte devem receber marcação específica durante o ranqueamento.
  3. O cálculo não deve alterar os modos existentes quando a funcionalidade estiver desabilitada.
  4. O resultado deve indicar quais músicas foram consideradas faixas-ponte.
- **Prioridade:** Baixa.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-11 e PB-22.
- **Sprint sugerida:** Sprint 5.
- **Status inicial:** A fazer.

### PB-24 — Balanceamento entre subgrupos *(pós-MVP)*

- **Épico:** EP-05 — Negociação e recomendação.
- **História:** Como grupo com preferências distintas, queremos que a seleção considere os diferentes subgrupos identificados, para evitar que apenas um deles domine a playlist.
- **Descrição:** Alternar músicas representativas dos subgrupos durante a seleção final, preservando os critérios de consenso e justiça.
- **Critérios de aceitação:**
  1. A seleção deve limitar a predominância de um único subgrupo.
  2. Os critérios de rejeição e justiça já existentes devem continuar sendo respeitados.
  3. A funcionalidade deve ser opcional e configurável.
  4. A explicação da playlist deve indicar quando o balanceamento entre subgrupos foi utilizado.
- **Prioridade:** Baixa.
- **Estimativa:** 4 pontos.
- **Dependências:** PB-12, PB-16, PB-22 e PB-23.
- **Sprint sugerida:** Sprint 5.
- **Status inicial:** A fazer.

### PB-25 — Resiliência e eficiência da integração Spotify *(pós-MVP)*

- **Épico:** EP-06 — Integrações e geração.
- **História:** Como grupo, queremos que faixas já identificadas no Spotify sejam reutilizadas, para
  reduzir chamadas redundantes e recuperar a geração corretamente quando houver rate limit.
- **Descrição:** Reutilizar ID/URI de candidatas nativas, manter Search apenas para fontes externas e
  interromper o lote no primeiro `429`, preservando `Retry-After`.
- **Critérios de aceitação:**
  1. Candidata nativa válida deve ser correspondida sem Spotify Search.
  2. Candidata externa ou incompleta deve continuar sujeita ao matching textual e à confiança mínima.
  3. O primeiro rate limit deve interromper o lote e retornar falha recuperável com `Retry-After`.
  4. Uma falha deve liberar a sala para nova tentativa sem transformar o restante em falsos descartes.
- **Prioridade:** Alta.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-13, PB-14 e PB-15.
- **Sprint sugerida:** Sprint 6.
- **Status inicial:** A fazer.

### PB-26 — Pool contextual híbrido *(pós-MVP)*

- **Épico:** EP-06 — Integrações e geração.
- **História:** Como grupo, queremos combinar repertório habitual com descobertas coerentes com a
  ocasião, para que o contexto influencie mais do que a simples reordenação dos Tops.
- **Descrição:** Ampliar as âncoras Spotify com faixas Last.fm por tag e similaridade, registrando
  proveniência e preservando fallback, veto, justiça e representação.
- **Critérios de aceitação:**
  1. O pool deve distinguir `spotify_top`, `lastfm_tag` e `lastfm_similar`.
  2. Intenções específicas devem afetar oferta, score e ordem de forma reproduzível.
  3. Falha ou ausência de Last.fm deve preservar o fluxo baseado em Tops.
  4. Descobertas não devem herdar metadados musicais da semente nem ultrapassar vetos.
  5. A composição deve manter uma parcela configurável de âncoras pessoais.
- **Prioridade:** Alta.
- **Estimativa:** 8 pontos.
- **Dependências:** PB-17, PB-18, PB-21 e PB-25.
- **Sprint sugerida:** Sprint 6.
- **Status inicial:** A fazer.

### PB-27 — Acompanhamento compartilhado da geração *(pós-MVP)*

- **Épico:** EP-07 — Experiência e explicabilidade.
- **História:** Como integrante, quero acompanhar a mesma geração do host, para saber seu progresso
  e chegar ao resultado sem permanecer parado no lobby.
- **Descrição:** Persistir estágios e percentual monotônico e compartilhá-los por polling, mantendo a
  ação de iniciar ou repetir exclusivamente com o host.
- **Critérios de aceitação:**
  1. A execução deve persistir estágio e percentual coerentes com o pipeline real.
  2. Todos os membros devem observar progresso, conclusão e erro sanitizado.
  3. Apenas o host deve iniciar ou repetir uma geração.
  4. O payload coletivo não deve expor Tops, respostas, clusters ou tokens.
- **Prioridade:** Média.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-13 e PB-16.
- **Sprint sugerida:** Sprint 6.
- **Status inicial:** A fazer.

### PB-28 — Conformidade visual do Login/Landing *(pós-MVP)*

- **Épico:** EP-07 — Experiência e explicabilidade.
- **História:** Como visitante, quero uma entrada coerente com o design do produto, para entender a
  proposta e iniciar o OAuth com confiança.
- **Descrição:** Reconstruir Login/Landing em React a partir do design oficial, preservando OAuth,
  acessibilidade, responsividade e estados de erro/carregamento.
- **Critérios de aceitação:**
  1. A tela deve reproduzir a hierarquia e os tokens do design oficial sem embutir o protótipo HTML.
  2. O CTA deve iniciar o OAuth real e impedir duplo clique.
  3. Foco, erro, responsividade e movimento reduzido devem ser tratados.
- **Prioridade:** Média.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-02.
- **Sprint sugerida:** Sprint 6.
- **Status inicial:** A fazer.

### PB-29 — Estado compartilhado e privado do Vibe Check *(pós-MVP)*

- **Épico:** EP-04 — Contexto e preferências.
- **História:** Como integrante, quero ver quem respondeu ou pulou o Vibe Check sem ver respostas
  privadas, para o grupo saber quando está pronto.
- **Descrição:** Distinguir `pending`, `answered` e `skipped`, expor apenas estados e totais agregados
  e permitir que cada pessoa edite somente a própria resposta.
- **Critérios de aceitação:**
  1. O lobby deve mostrar estado individual e resumo agregado sem valores privados.
  2. Responder, pular e editar devem afetar somente o registro do próprio usuário.
  3. Pular não deve fabricar valores neutros persistidos nem alterar o ranking.
  4. Uma resposta posterior deve substituir corretamente o estado pulado.
- **Prioridade:** Média.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-07 e PB-27.
- **Sprint sugerida:** Sprint 6.
- **Status inicial:** A fazer.

### PB-30 — Autorização e inventário de playlists *(pós-MVP)*

- **Épico:** EP-09 — Biblioteca musical ampliada.
- **História:** Como integrante, quero autorizar a leitura das minhas playlists elegíveis, para que
  o sistema conheça um repertório maior do que somente o Top 50.
- **Descrição:** Adicionar o escopo `playlist-read-private`, detectar consentimento antigo
  insuficiente e inventariar, com paginação, playlists próprias ou colaborativas cujo conteúdo seja
  permitido pela API vigente do Spotify.
- **Critérios de aceitação:**
  1. O OAuth deve solicitar somente os escopos necessários e exigir novo consentimento quando faltar
     `playlist-read-private`.
  2. O inventário deve paginar `GET /me/playlists` até o fim, sem assumir uma única página.
  3. Apenas playlists cujo conteúdo seja legível para o usuário atual devem seguir para sincronização;
     playlists apenas seguidas e inacessíveis não devem provocar erro nem tentativa de contorno.
  4. ID, propriedade/colaboração, quantidade, `snapshot_id` e data de verificação devem ser
     persistidos sem tokens, imagens ou descrições desnecessárias.
  5. Respostas 401, 403 e 429 devem ser diferenciadas e sanitizadas.
- **Prioridade:** Alta.
- **Estimativa:** 3 pontos.
- **Dependências:** nenhuma.
- **Sprint sugerida:** Sprint 7.
- **Status inicial:** A fazer.

### PB-31 — Biblioteca musical limitada a 500 faixas *(pós-MVP)*

- **Épico:** EP-09 — Biblioteca musical ampliada.
- **História:** Como integrante, quero que Tops e playlists formem uma biblioteca limitada e
  deduplicada, para ampliar minha representação sem crescimento descontrolado do banco.
- **Descrição:** Persistir um catálogo mínimo normalizado e sinais por usuário, com limite absoluto
  de **500 faixas Spotify únicas por pessoa**, incluindo todas as origens.
- **Critérios de aceitação:**
  1. A biblioteca deve priorizar até 150 Tops únicos: 50 `short_term`, 50 `medium_term` e 50
     `long_term`; top artists continuam como metadado auxiliar e não contam no limite de faixas.
  2. Faixas das playlists elegíveis devem preencher a capacidade restante até, nunca acima de, 500
     faixas únicas por usuário.
  3. A mesma faixa em Tops e/ou em várias playlists deve ocupar uma vaga e preservar todas as origens,
     ranks e referências necessárias ao peso posterior.
  4. Quando houver mais faixas do que vagas, o preenchimento de playlists deve ser determinístico e
     distribuído entre elas, evitando que uma única playlist longa consuma todo o limite.
  5. A persistência deve guardar somente metadados necessários à recomendação e ser removida no
     `DELETE /auth/me`.
  6. A migração deve ser reversível e impor unicidade por usuário/faixa.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-30.
- **Sprint sugerida:** Sprint 7.
- **Status inicial:** A fazer.

### PB-32 — Sincronização incremental e resiliente *(pós-MVP)*

- **Épico:** EP-09 — Biblioteca musical ampliada.
- **História:** Como integrante, quero reutilizar minha biblioteca por sete dias e atualizar somente
  o que mudou, para evitar rate limit e continuar usando o produto em falhas temporárias.
- **Descrição:** Aplicar TTL, `snapshot_id`, controle de concorrência, paginação sem N+1 por faixa e
  fallback atômico para o último cache utilizável.
- **Critérios de aceitação:**
  1. Biblioteca com menos de sete dias deve ser reutilizada sem chamadas ao Spotify.
  2. Ao vencer, o sistema deve reler o inventário e evitar baixar itens de playlists cujo
     `snapshot_id` não mudou.
  3. A sincronização deve paginar itens em lotes, nunca consultar detalhes individualmente por faixa,
     e usar concorrência externa limitada e configurável.
  4. `429` deve respeitar `Retry-After`; `QUOTA_EXCEEDED` deve ser distinguido de rate limit transitório.
     Em ambos, o último cache pronto permanece utilizável e dados parciais não o substituem.
  5. Duas sincronizações simultâneas do mesmo usuário devem convergir sem HTTP 500, duplicidade ou
     corrupção, encerrando também o defeito conhecido `DEF-PB08-01` no fluxo compartilhado.
  6. Sem cache anterior, a falha deve ser explícita, recuperável e não apagar os Tops já existentes.
- **Prioridade:** Alta.
- **Estimativa:** 5 pontos.
- **Dependências:** PB-31.
- **Sprint sugerida:** Sprint 7.
- **Status inicial:** A fazer.

### PB-33 — Perfil ponderado e seleção limitada de candidatas *(pós-MVP)*

- **Épico:** EP-09 — Biblioteca musical ampliada.
- **História:** Como grupo, queremos que Tops tenham mais valor do que uma faixa ocasional de
  playlist, para ganhar variedade sem confundir presença em playlist com preferência forte.
- **Descrição:** Evoluir o motor puro para sinais ponderados por origem/rank e extrair, por geração,
  um conjunto contextual e equilibrado de no máximo 250 candidatas por usuário.
- **Critérios de aceitação:**
  1. Pesos default devem ser centralizados e decrescentes: Top recente `1,00`, Top médio `0,85`, Top
     longo `0,65`, playlist própria `0,45` e colaborativa `0,35`, com bônus limitado por recorrência.
  2. Uma faixa em mais de uma origem deve combinar evidências sem ultrapassar 1,00 nem duplicar a
     candidata.
  3. O conjunto ativo deve ter no máximo 250 faixas por pessoa, mirando até 150 Tops e até 100
     faixas de playlists; uma origem pode preencher capacidade ociosa sem retirar prioridade dos Tops.
  4. A seleção deve ser determinística, considerar o contexto e impedir que quem possui 500 faixas
     domine quem possui uma biblioteca pequena.
  5. Compatibilidade e afinidade devem consumir pesos, não inserir todas as faixas de playlist como
     um conjunto binário equivalente ao Top atual.
  6. Todo o cálculo deve permanecer em `engine/`, puro e sem banco ou rede.
- **Prioridade:** Alta.
- **Estimativa:** 8 pontos.
- **Dependências:** PB-32.
- **Sprint sugerida:** Sprint 7.
- **Status inicial:** A fazer.

### PB-34 — Integração e observabilidade da biblioteca ampliada *(pós-MVP)*

- **Épico:** EP-09 — Biblioteca musical ampliada.
- **História:** Como integrante, quero saber se meu repertório está sincronizado e usá-lo na geração,
  para confiar que Tops e playlists realmente influenciaram o resultado.
- **Descrição:** Expor status/refresh sanitizados, integrar o perfil ponderado ao pipeline e explicar
  origens apenas de forma agregada, preservando o fallback histórico de Tops.
- **Critérios de aceitação:**
  1. `GET /me/music-library` deve retornar estado, quantidade `0..500`, idade, stale/warning e contagem
     agregada por origem, sem listar playlists ou faixas privadas de outro usuário.
  2. `POST /me/refresh-music-library` deve iniciar/realizar uma atualização idempotente e informar
     rate limit, quota ou reautenticação de modo acionável.
  3. A Home deve mostrar quantidade e idade da sincronização no componente existente, sem criar tela
     fora do design oficial.
  4. A geração deve usar a biblioteca ponderada quando pronta e cair para o snapshot Top do PB-08
     quando a biblioteca não existir ou estiver indisponível, sem bloquear a sala.
  5. Faixas nativas de playlist devem reutilizar ID/URI conforme PB-25; Search continua restrito às
     candidatas externas.
  6. Resultado e logs devem explicar somente proporções agregadas de Top/playlist/contexto, sem nome
     de playlist, resposta privada, token ou perfil bruto.
- **Prioridade:** Alta.
- **Estimativa:** 3 pontos.
- **Dependências:** PB-31, PB-32 e PB-33.
- **Sprint sugerida:** Sprint 7.
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
| 13 | PB-14 | EP-06 | Correspondência no Spotify | Alta | 5 | PB-02, PB-11, PB-12, PB-13 | Sprint 3 | A fazer |
| 14 | PB-15 | EP-06 | Criação da playlist | Alta | 3 | PB-14 | Sprint 3 | A fazer |
| 15 | PB-16 | EP-07 | Resultado e explicabilidade | Média | 5 | PB-13, PB-14, PB-15 | Sprint 3 | A fazer |
| 16 | PB-17 | EP-06 | Contexto por LLM | Média | 5 | PB-06, PB-10 | Sprint 3 | A fazer |
| 17 | PB-03 | EP-02 | Logout e remoção | Média | 3 | PB-02 | Sprint 4 | A fazer |
| 18 | PB-18 | EP-06 | Contexto Last.fm | Média | 5 | PB-10, PB-17 | Sprint 4 | A fazer |
| 19 | PB-19 | EP-07 | Sequenciamento | Média | 3 | PB-12, PB-14, PB-15 | Sprint 4 | A fazer |
| 20 | PB-20 | EP-07 | Feedback | Média | 3 | PB-16 | Sprint 4 | A fazer |
| 21 | PB-21 | EP-08 | Modo Descoberta | Baixa | 5 | PB-11, PB-12, PB-16 | Sprint 5 | A fazer |
| 22 | PB-22 | EP-05 | Agrupamento de perfis | Baixa | 4 | PB-09 | Sprint 5 | A fazer |
| 23 | PB-23 | EP-05 | Músicas-ponte | Baixa | 5 | PB-11, PB-22 | Sprint 5 | A fazer |
| 24 | PB-24 | EP-05 | Balanceamento entre subgrupos | Baixa | 4 | PB-12, PB-16, PB-22, PB-23 | Sprint 5 | A fazer |
| 25 | PB-25 | EP-06 | Resiliência Spotify | Alta | 3 | PB-13, PB-14, PB-15 | Sprint 6 | A fazer |
| 26 | PB-26 | EP-06 | Pool contextual híbrido | Alta | 8 | PB-17, PB-18, PB-21, PB-25 | Sprint 6 | A fazer |
| 27 | PB-27 | EP-07 | Progresso compartilhado | Média | 5 | PB-13, PB-16 | Sprint 6 | A fazer |
| 28 | PB-28 | EP-07 | Login conforme design | Média | 3 | PB-02 | Sprint 6 | A fazer |
| 29 | PB-29 | EP-04 | Estado do Vibe Check | Média | 5 | PB-07, PB-27 | Sprint 6 | A fazer |
| 30 | PB-30 | EP-09 | Autorização e inventário | Alta | 3 | — | Sprint 7 | A fazer |
| 31 | PB-31 | EP-09 | Biblioteca de 500 faixas | Alta | 5 | PB-30 | Sprint 7 | A fazer |
| 32 | PB-32 | EP-09 | Sincronização resiliente | Alta | 5 | PB-31 | Sprint 7 | A fazer |
| 33 | PB-33 | EP-09 | Perfil ponderado e candidatas | Alta | 8 | PB-32 | Sprint 7 | A fazer |
| 34 | PB-34 | EP-09 | Integração da biblioteca | Alta | 3 | PB-31..33 | Sprint 7 | A fazer |

> "Qualidade, robustez e documentação" (antigo PB-20) não é mais item do backlog — virou a
> **Definition of Done**, aplicada a todos os PBs.

### 11.1 Totais

- **Total de histórias/itens:** 34.
- **Total geral:** 152 pontos (MVP: 86; expansão pós-MVP: 66).
- **Prioridade Alta:** 20 itens, totalizando 92 pontos.
- **Prioridade Média:** 10 itens, totalizando 42 pontos.
- **Prioridade Baixa:** 4 itens, totalizando 18 pontos.
- **Sprint 1:** 25 pontos.
- **Sprint 2:** 24 pontos.
- **Sprint 3:** 23 pontos.
- **Sprint 4:** 14 pontos.
- **Sprint 5 (pós-MVP):** 18 pontos.
- **Sprint 6 (pós-MVP):** 24 pontos.
- **Sprint 7 (pós-MVP):** 24 pontos.

## 12. Definição do Produto Mínimo Viável — MVP

O MVP é composto por `PB-01`, `PB-02`, `PB-04`, `PB-05`, `PB-06`, `PB-08`, `PB-09`, `PB-10`, `PB-11`, `PB-12`, `PB-13`, `PB-14`, `PB-15` e `PB-16`, com as práticas de qualidade aplicadas continuamente pela **Definition of Done** (ver §15).

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

O núcleo do MVP possui cerca de 62 pontos nominais, com a consolidação de qualidade distribuída pela Definition of Done. Com capacidade assumida de 25 pontos por sprint, são necessárias aproximadamente três a quatro sprints de duas semanas. Portanto, o prazo original de cerca de um mês exige aumento comprovado de velocidade, paralelização segura ou redução adicional de escopo. Essa decisão deve ser tomada após a equipe medir sua velocidade na primeira sprint.

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

### 15.1 Definition of Done da Sprint

Além da DoD por história, uma Sprint só é considerada concluída quando:

- todos os PBs obrigatórios da Sprint atendem à DoD acima;
- os testes individuais de cada PB da Sprint estão passando;
- os testes integrados da Sprint estão passando;
- os testes de regressão das Sprints anteriores continuam passando;
- o incremento da Sprint pode ser demonstrado de ponta a ponta;
- os bloqueios remanescentes estão documentados.

### 15.2 Documentos operacionais de apoio

O detalhamento operacional deste backlog é mantido em dois documentos, que **não** substituem nem
alteram os critérios de aceitação definidos aqui:

- **`PLANO_EXECUCAO.md`** — execução por Sprint, ordem de implementação, status, decisões, riscos e
  ponto exato de retomada (inclui o Protocolo obrigatório do agente de implementação).
- **`PLANO_TESTES.md`** — testes individuais de cada PB e testes integrados de cada Sprint, com os
  critérios de aprovação usados para validar os critérios de aceitação deste backlog.

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
| Inventário de playlists | Autenticação e resiliência Spotify | Requer novo escopo e paginação compatível com a API vigente. |
| Biblioteca de 500 faixas | Tops e inventário de playlists | Deduplica origens e impõe limite único por pessoa. |
| Sincronização incremental | Biblioteca persistida | Usa TTL, `snapshot_id`, atomicidade e fallback em rate limit/quota. |
| Perfil ponderado | Biblioteca pronta e motor existente | Diferencia força de Top e playlist antes da formação do pool. |
| Geração com biblioteca | Perfil ponderado e progresso | Integra a nova entrada sem remover o fallback de Tops. |

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
| R-15 | Sincronização de playlists exceder rate limit ou quota do Spotify | Média | Alto | Limite 500, TTL de 7 dias, `snapshot_id`, paginação sem N+1, concorrência baixa e fallback para cache. |
| R-16 | Faixas ocasionais de playlists diluírem o gosto real | Alta | Alto | Pesos por origem/rank, Tops prioritários e pool ativo limitado por pessoa. |
| R-17 | Retenção excessiva de dados Spotify | Média | Alto | Metadados mínimos, cache temporário, remoção no disconnect e revisão das políticas vigentes. |

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
