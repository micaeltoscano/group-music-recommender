Engenharia de Software

**VIBE CHECK**

*Group Music Recommender*

Backlog do Produto e Backlogs de Sprint — Metodologia Scrum

Versão 1.0 – Julho de 2026

# **Ficha Técnica**

## **Equipe Responsável pela Elaboração**

\[Integrantes da equipe a definir\]

## **Papéis Scrum**

**Product Owner:** \[a definir\]

**Scrum Master:** \[a definir\]

**Equipe de Desenvolvimento:** \[integrantes da equipe\]

## **Público Alvo**

Este documento destina-se à equipe de desenvolvimento do produto e ao professor responsável pela disciplina de Engenharia de Software, sendo também referência para avaliadores acadêmicos do processo ágil adotado.

Versão 1.0 – \[Local a definir\], julho de 2026

Dúvidas, críticas e sugestões podem ser encaminhadas para a equipe responsável pelo projeto através dos endereços eletrônicos disponíveis no SIGAA, ou pelo contato: \[telefone a definir\]

# **Sumário**

[**Ficha Técnica	2**](#heading=)

[**Equipe Responsável pela Elaboração	2**](#heading=)

[**Papéis Scrum	2**](#heading=)

[**Público Alvo	2**](#heading=)

[**Sumário	3**](#heading=)

[**1 Visão Geral do Produto	5**](#heading=)

[**1.1 Descrição do Produto	5**](#heading=)

[**1.2 Problema que o Produto Busca Resolver	5**](#heading=)

[**1.3 Objetivo Geral	5**](#heading=)

[**1.4 Objetivos Específicos	5**](#heading=)

[**2 Público-Alvo e Personas	5**](#heading=)

[**2.1 Público-Alvo	5**](#heading=)

[**2.2 Persona 1 — Marina, a Anfitriã	6**](#heading=)

[**2.3 Persona 2 — Rafael, o Convidado com Gosto Minoritário	6**](#heading=)

[**2.4 Persona 3 — Lucas, o Participante Casual	6**](#heading=)

[**3 Épicos do Produto	6**](#heading=)

[**4 Product Backlog	7**](#heading=)

[**4.1 PB-01 — Fundação técnica do produto	7**](#heading=)

[**4.2 PB-02 — Autenticação com Spotify	7**](#heading=)

[**4.3 PB-03 — Logout e remoção de dados	8**](#heading=)

[**4.4 PB-04 — Criação de sala efêmera	8**](#heading=)

[**4.5 PB-05 — Entrada e acompanhamento da sala	9**](#heading=)

[**4.6 PB-06 — Contexto e modo de consenso	9**](#heading=)

[**4.7 PB-07 — Vibe Check opcional	10**](#heading=)

[**4.8 PB-08 — Coleta e cache de dados musicais	10**](#heading=)

[**4.9 PB-09 — Modelagem de gosto e compatibilidade	10**](#heading=)

[**4.10 PB-10 — Geração do conjunto de candidatas	11**](#heading=)

[**4.11 PB-11 — Pontuação individual e coletiva	11**](#heading=)

[**4.12 PB-12 — Rejeição, justiça e modos de consenso	12**](#heading=)

[**4.13 PB-13 — Controle e histórico da geração	12**](#heading=)

[**4.14 PB-14 — Correspondência das músicas no Spotify	13**](#heading=)

[4.15 PB-15 — Criação da playlist no Spotify	13](#4.15-pb-15-—-criação-da-playlist-no-spotify)

[**4.16 PB-16 — Resultado e explicabilidade	14**](#heading=)

[**4.17 PB-17 — Interpretação estruturada do contexto	14**](#heading=)

[**4.18 PB-18 — Enriquecimento de contexto com Last.fm	15**](#heading=)

[**4.19 PB-19 — Sequenciamento da experiência musical	15**](#heading=)

[**4.20 PB-20 — Feedback pós-playlist	15**](#heading=)

[**4.21 PB-21 — Modo Descoberta	16**](#heading=)

[**4.22 PB-22 — Agrupamento de perfis musicais	16**](#heading=)

[4.23 PB-23 — Identificação de músicas-ponte	17](#4.23-pb-23-—-identificação-de-músicas-ponte)

[4.24 PB-24 — Balanceamento entre subgrupos	17](#4.24-pb-24-—-balanceamento-entre-subgrupos)

[**5 Sprint Backlogs	18**](#heading=)

[**5.1 Sprint 1	18**](#heading=)

[**5.2 Sprint 2	18**](#heading=)

[**5.3 Sprint 3	18**](#heading=)

[**5.4 Sprint 4	19**](#heading=)

[**5.5 Sprint 5	19**](#heading=)

[**6 Backlog Resumido e Priorizado	19**](#heading=)

[**6.1 Totais	20**](#heading=)

[**7 Critérios de Priorização	20**](#heading=)

[**8 Definition of Ready (DoR)	21**](#heading=)

[**9 Definition of Done (DoD)	21**](#heading=)

[**10 Dependências entre Funcionalidades	21**](#heading=)

[**11 Riscos do Projeto	22**](#heading=)

# **1 Visão Geral do Produto**

## **1.1 Descrição do Produto**

O Vibe Check é uma aplicação web de recomendação musical em grupo integrada ao Spotify. Através de salas efêmeras criadas por um *host*, até cinco participantes conectam seus perfis e o núcleo da aplicação, *Preference Negotiation Engine (PNE)*, um motor que processa o histórico dos usuários e gera uma playlist real na conta do *host*. O motor garante uma curadoria equilibrada ao ponderar afinidade musical, contexto do encontro, rejeições e representatividade justa de todos os membros.

O MVP utiliza Spotify OAuth para autenticação, salas temporárias com até cinco integrantes, contexto informado pelo host, Vibe Check opcional, modos de consenso, cálculo de compatibilidade, seleção justa de músicas, sequenciamento e explicações sobre o resultado.

## **1.2 Problema que o Produto Busca Resolver**

Escolher músicas para um grupo é uma atividade sujeita a conflitos. Playlists baseadas apenas na média das preferências tendem a favorecer a maioria e podem ignorar participantes com gostos diferentes. As soluções existentes normalmente misturam preferências passadas, mas oferecem pouco controle sobre o contexto do momento em que a seleção foi criada. Por consequência, um integrante pode ter baixa representação mesmo quando a playlist apresenta uma boa aceitação média.

O Vibe Check busca resolver esse problema por meio de uma negociação computacional de preferências. O sistema considera a satisfação média, a menor satisfação individual, a cobertura dos integrantes, as rejeições e o contexto atual antes de criar a playlist.

## **1.3 Objetivo Geral**

Desenvolver uma aplicação web capaz de gerar playlists coletivas no Spotify que representem os integrantes de um grupo, considerando gostos musicais, contexto, rejeições e critérios de justiça.

## **1.4 Objetivos Específicos**

* Gerenciar acesso e salas efêmeras via código com autenticação exclusiva por *Spotify OAuth*.

* Extrair automaticamente os dados musicais dos usuários e capturar o humor/ocasião do grupo.

* Calcular compatibilidade e selecionar faixas evitando o favorecimento exclusivo da maioria.

* Disponibilizar modos de consenso específicos (ex: Democrático, Festa Segura).

* Criar uma playlist privada (20 a 30 músicas) na conta do *host*.

* Fornecer explicações claras sobre o resultado da playlist e coletar feedback para iterações futuras.

* Autenticar usuários exclusivamente por meio do Spotify OAuth.

* Permitir a criação e o ingresso em salas efêmeras por código curto.

* Obter automaticamente os principais artistas e músicas dos integrantes.

* Capturar a ocasião e o humor atual do grupo.

* Calcular a compatibilidade musical entre os participantes.

* Gerar e pontuar um conjunto de músicas candidatas.

* Evitar que a preferência da maioria elimine a representação das minorias.

* Oferecer modos de consenso Democrático e Festa Segura.

* Criar uma playlist privada de 20 a 30 músicas na conta do host.

* Apresentar explicações compreensíveis e compatíveis com a privacidade.

* Coletar feedback para apoiar futuras evoluções do produto.

# **2 Público-Alvo e Personas**

## **2.1 Público-Alvo**

Pequenos grupos (1 a 5 pessoas) que buscam criar trilhas sonoras colaborativas para momentos sociais (festas, estudos, viagens, etc.). Para o escopo do MVP, os usuários finais devem estar autorizados no Development Mode do Spotify. Como se trata de um projeto acadêmico, a equipe de desenvolvimento, professores e avaliadores também atuam como stakeholders diretos para a validação técnica e metodológica da entrega.

## **2.2 Persona 1 — Marina, a Anfitriã**

**Idade:** 24 anos

**Ocupação/contexto:** estudante universitária que organiza encontros com amigos

**Objetivo:** criar rapidamente uma playlist que funcione para todos durante uma festa

**Necessidade:** transformar a ocasião e os gostos do grupo em uma playlist pronta no Spotify

**Dificuldade:** perde tempo negociando músicas e costuma receber reclamações quando escolhe apenas seus próprios hits

**Uso do produto:** cria a sala, informa o contexto, escolhe o modo de consenso, acompanha a entrada dos convidados e solicita a geração da playlist

## **2.3 Persona 2 — Rafael, o Convidado com Gosto Minoritário**

**Idade:** 27 anos

**Ocupação/contexto:** desenvolvedor de software que participa de viagens e reuniões com amigos

**Objetivo:** sentir que seu gosto musical foi considerado sem precisar controlar a playlist

**Necessidade:** ter alguma representação e evitar músicas pelas quais possui forte rejeição

**Dificuldade:** seus gêneros favoritos diferem dos da maioria e normalmente desaparecem de playlists coletivas

**Uso do produto:** entra pelo código da sala, autentica-se, responde ao Vibe Check e consulta a explicação de justiça do resultado

## **2.4 Persona 3 — Lucas, o Participante Casual**

**Idade:** 21 anos

**Ocupação/contexto:** estudante que usa o Spotify diariamente, mas não deseja preencher formulários longos

**Objetivo:** participar da criação da playlist com o menor esforço possível

**Necessidade:** permitir que o sistema obtenha suas preferências automaticamente

**Dificuldade:** abandona aplicações que exigem cadastros adicionais ou questionários extensos

**Uso do produto:** autentica-se pelo Spotify, entra na sala, pula ou responde rapidamente ao Vibe Check e acessa a playlist final

# **3 Épicos do Produto**

Um épico agrupa histórias de usuário relacionadas por tema, funcionando como um nível de organização acima das histórias individuais do Product Backlog.

| ID | Épico | Descrição |
| :---- | :---- | :---- |
| EP-01 | Fundação e qualidade | Infraestrutura técnica, banco de dados, migrações, testes e documentação necessários ao desenvolvimento e manutenção do sistema. |
| EP-02 | Autenticação e privacidade | Autenticação via Spotify OAuth, gerenciamento seguro de sessões e proteção dos dados dos usuários. |
| EP-03 | Salas e colaboração | Criação e gerenciamento de salas, entrada de participantes e acompanhamento do estado da sessão. |
| EP-04 | Contexto e preferências | Coleta do contexto da sessão e das preferências musicais dos participantes para apoiar a recomendação. |
| EP-05 | Negociação e recomendação | Modelagem do perfil musical, cálculo de compatibilidade, negociação e seleção das músicas da playlist. |
| EP-06 | Integrações e geração | Integração com serviços externos, interpretação do contexto e geração da playlist no Spotify. |
| EP-07 | Experiência e explicabilidade | Apresentação dos resultados, explicações sobre a recomendação, sequenciamento da playlist e coleta de feedback dos usuários. |

# **4 Product Backlog**

O Product Backlog reúne todas as funcionalidades previstas para o produto, priorizadas pelo Product Owner e refinadas continuamente pela equipe. Cada item abaixo corresponde a uma história de usuário pronta para ser selecionada em uma Sprint Planning.

## **4.1 PB-01 — Fundação técnica do produto**

**Épico:** EP-01 — Fundação e qualidade

**História:** Como membro da equipe de desenvolvimento, quero uma estrutura integrada de frontend, backend e banco de dados, para implementar as funcionalidades do produto de forma incremental.

**Descrição:** Preparar os projetos React/Vite e FastAPI, banco PostgreSQL, SQLAlchemy, Alembic e configuração local do ambiente.

**Critérios de aceitação:**

* O frontend e o backend devem iniciar no ambiente local conforme instruções documentadas.

* O backend deve estabelecer conexão com o PostgreSQL.

* Uma migração inicial do Alembic deve ser executada e revertida sem erro.

* Configurações sensíveis devem ser obtidas por variáveis de ambiente e não versionadas.

**Prioridade: Alta**

**Estimativa:** 2 pontos

**Dependências:** Nenhuma

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **4.2 PB-02 — Autenticação com Spotify**

**Épico:** EP-02 — Autenticação e privacidade

**História:** Como usuário, quero entrar com minha conta Spotify, para participar das salas sem criar uma nova senha.

**Descrição:** Implementar o fluxo Spotify OAuth, persistência segura dos tokens e sessão da aplicação por cookie.

**Critérios de aceitação:**

* O sistema deve redirecionar o usuário para a autorização oficial do Spotify.

* O callback deve rejeitar uma resposta com parâmetro state ausente ou inválido.

* Uma autorização válida deve criar ou atualizar o usuário e iniciar uma sessão da aplicação.

* Access token e refresh token não devem ser enviados ao frontend nem registrados em logs.

* Os tokens armazenados devem estar criptografados em repouso.

**Prioridade: Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-01

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **4.3 PB-03 — Logout e remoção de dados**

**Épico:** EP-02 — Autenticação e privacidade

**História:** Como usuário, quero encerrar minha sessão e remover meus dados, para manter controle sobre minha privacidade.

**Descrição:** Disponibilizar encerramento da sessão e fluxo de exclusão ou anonimização dos dados mantidos pelo sistema.

**Critérios de aceitação:**

* O logout deve invalidar a sessão da aplicação no backend.

* Após o logout, rotas autenticadas devem responder como não autorizadas.

* A solicitação de remoção deve excluir ou anonimizar os dados pessoais previstos pela política do produto.

* A operação não deve expor tokens ou informações de outros integrantes.

**Prioridade: Média**

**Estimativa:** 3 pontos

**Dependências:** PB-02

**Sprint sugerida:** Sprint 4

**Status inicial:** A fazer

## **4.4 PB-04 — Criação de sala efêmera**

**Épico:** EP-03 — Salas e colaboração

**História:** Como host, quero criar uma sala com um código curto, para convidar outras pessoas a participar da negociação musical.

**Descrição:** Criar uma sala temporária, associar o criador como host e gerar um código compartilhável.

**Critérios de aceitação:**

* Apenas um usuário autenticado deve poder criar uma sala.

* Cada sala deve receber um código curto único.

* O criador deve ser registrado como host e primeiro integrante.

* A sala deve receber data de expiração de 24 horas após sua criação.

* O sistema deve retornar o código e os dados iniciais da sala.

**Prioridade: Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-01 e PB-02

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **4.5 PB-05 — Entrada e acompanhamento da sala**

**Épico:** EP-03 — Salas e colaboração

**História:** Como convidado, quero entrar em uma sala pelo código e visualizar seus integrantes, para saber quando o grupo está pronto.

**Descrição:** Permitir entrada por código, impedir duplicidade e atualizar integrantes e estado da sala por polling.

**Critérios de aceitação:**

* O sistema deve rejeitar código inexistente ou sala expirada.

* A sala deve aceitar no máximo cinco integrantes.

* O mesmo usuário não deve ser associado duas vezes à mesma sala.

* Apenas membros da sala devem consultar seus dados; os demais devem receber resposta 403\.

* A interface deve atualizar integrantes e estado por polling a cada três a cinco segundos.

**Prioridade: Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-02 e PB-04

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **4.6 PB-06 — Contexto e modo de consenso**

**Épico:** EP-04 — Contexto e preferências

**História:** Como host, quero informar a ocasião, uma descrição e o modo de consenso, para adequar a playlist ao momento do grupo.

**Descrição:** Armazenar o contexto livre e oferecer os modos Democrático e Festa Segura.

**Critérios de aceitação:**

* Somente o host deve poder alterar o contexto e o modo da sala.

* O sistema deve aceitar ocasião, descrição livre ou ambos.

* O modo selecionado deve ser Democrático ou Festa Segura.

* As alterações devem ficar disponíveis para os integrantes na próxima atualização da sala.

**Prioridade: Alta**

**Estimativa:** 3 pontos

**Dependências:** PB-04

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **4.7 PB-07 — Vibe Check opcional**

**Épico:** EP-04 — Contexto e preferências

**História:** Como integrante, quero responder ou pular um questionário curto, para expressar meu humor e minhas preferências do momento.

**Descrição:** Apresentar de três a cinco perguntas gamificadas e converter as respostas em variáveis normalizadas para o motor.

**Critérios de aceitação:**

* O questionário deve apresentar no mínimo três e no máximo cinco perguntas.

* O usuário deve poder pular o questionário sem bloquear a geração.

* As respostas devem ser armazenadas por usuário e sala.

* As preferências derivadas devem possuir valores entre 0 e 1\.

* Uma nova resposta do mesmo usuário deve atualizar sua participação na geração seguinte.

**Prioridade: Média**

**Estimativa:** 5 pontos

**Dependências:** PB-05 e PB-06

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **4.8 PB-08 — Coleta e cache de dados musicais**

**Épico:** EP-04 — Contexto e preferências

**História:** Como integrante, quero que meus principais artistas e músicas sejam obtidos automaticamente, para participar sem preencher preferências manualmente.

**Descrição:** Consultar top artists e top tracks do Spotify e armazenar snapshots com validade configurável.

**Critérios de aceitação:**

* O sistema deve consultar apenas os endpoints Spotify autorizados no escopo do MVP.

* Faixas e artistas obtidos devem ser associados ao usuário em um snapshot.

* Um snapshot com menos de sete dias deve ser reutilizado por padrão.

* Um snapshot vencido deve ser atualizado antes da geração.

* Falha de renovação do token deve marcar a necessidade de nova autenticação.

**Prioridade: Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-02

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **4.9 PB-09 — Modelagem de gosto e compatibilidade**

**Épico:** EP-05 — Negociação e recomendação

**História:** Como integrante, quero que o sistema modele meu gosto e calcule a compatibilidade do grupo, para representar as afinidades e diferenças existentes.

**Descrição:** Construir perfis temporários com faixas, artistas, gêneros e medidas de similaridade entre os participantes.

**Critérios de aceitação:**

* O modelo individual deve considerar faixas, artistas e gêneros disponíveis no snapshot.

* O cálculo deve tratar corretamente listas vazias e grupos com apenas um integrante.

* A compatibilidade deve resultar em valor normalizado e reprodutível para a mesma entrada.

* O motor não deve realizar chamadas de rede durante o cálculo.

**Prioridade: Alta**

**Estimativa:** 3 pontos

**Dependências:** PB-05 e PB-08

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **4.10 PB-10 — Geração do conjunto de candidatas**

**Épico:** EP-05 — Negociação e recomendação

**História:** Como grupo, queremos que o sistema reúna músicas relacionadas aos nossos gostos, para formar uma base equilibrada de possíveis escolhas.

**Descrição:** Construir o pool de candidatas a partir das músicas e artistas fortes dos integrantes e de fontes contextuais permitidas.

**Critérios de aceitação:**

* O conjunto deve incluir contribuições dos diferentes integrantes quando houver dados disponíveis.

* Uma mesma música não deve aparecer mais de uma vez no conjunto.

* A origem de cada candidata deve ser registrada.

* Candidatas sem identificação suficiente para busca posterior devem ser descartadas com motivo.

**Prioridade:  Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-06 e PB-09

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **4.11 PB-11 — Pontuação individual e coletiva**

**Épico:** EP-05 — Negociação e recomendação

**História:** Como grupo, queremos que cada música candidata seja avaliada individual e coletivamente, para selecionar músicas adequadas ao conjunto de participantes.

**Descrição:** Implementar as fórmulas configuráveis de afinidade individual e score de grupo definidas para o PNE.

**Critérios de aceitação:**

* O score individual deve considerar afinidade de faixa, artista, gênero ou tag, popularidade e novidade disponíveis.

* O score de grupo deve considerar média, menor score individual, cobertura, contexto e diversidade.

* Os pesos devem permanecer centralizados e configuráveis.

* A mesma entrada e configuração devem produzir o mesmo resultado.

* Os cálculos principais devem possuir testes automatizados com valores esperados.

**Prioridade: Alta**

**Estimativa:** 8 pontos

**Dependências:** PB-09 e PB-10

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **4.12 PB-12 — Rejeição, justiça e modos de consenso**

**Épico:** EP-05 — Negociação e recomendação

**História:** Como integrante, quero que minhas rejeições e preferências minoritárias sejam consideradas, para não ser ignorado pela preferência média do grupo.

**Descrição:** Aplicar penalidades de rejeição, least misery, cobertura, representação mínima e perfis de peso dos modos de consenso.

**Critérios de aceitação:**

* Uma rejeição forte deve reduzir o score da música mesmo quando ela agradar à maioria.

* O sistema deve calcular satisfação média, menor satisfação, cobertura e fairness score.

* O modo Democrático deve atribuir o mesmo peso aos integrantes.

* O modo Festa Segura deve favorecer familiaridade e baixa rejeição.

* A seleção deve tentar elevar o integrante menos representado sem reduzir excessivamente a satisfação do grupo.

**Prioridade: Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-11. Quando PB-07 estiver disponível, suas respostas serão usadas como entrada opcional, sem bloquear esta história.

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **4.13 PB-13 — Controle e histórico da geração**

**Épico:** EP-06 — Integrações e geração

**História:** Como host, quero solicitar a geração de forma segura, para que cliques repetidos não criem playlists duplicadas.

**Descrição:** Criar uma execução de playlist por solicitação, controlar estados e impedir concorrência na mesma sala.

**Critérios de aceitação:**

* A primeira solicitação válida deve criar uma execução com estado running.

* Uma solicitação concorrente na mesma sala deve retornar resposta 409\.

* Uma execução concluída deve receber estado completed e uma falha deve receber estado failed.

* Após uma falha, o host deve poder iniciar uma nova execução controlada.

* Cada nova geração concluída deve possuir registro independente.

**Prioridade: Alta**

**Estimativa:** 3 pontos

**Dependências:** PB-05, PB-06 e PB-11

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **4.14 PB-14 — Correspondência das músicas no Spotify**

**Épico:** EP-06 — Integrações e geração

**História:** Como grupo, queremos que as músicas candidatas sejam corretamente identificadas no Spotify, para que apenas faixas válidas sejam utilizadas na playlist. 

**Descrição:** Resolver as músicas candidatas utilizando o Spotify Search, normalizando títulos e artistas, validando disponibilidade e descartando resultados ambíguos ou indisponíveis. 

**Critérios de aceitação:**

* A busca deve utilizar o mercado associado ao token do host quando disponível.

* Título e artista devem ser normalizados para tratar variações como *live*, *remastered* e *acoustic*.

* Resultados abaixo da confiança mínima devem ser descartados com o motivo registrado.

* Músicas indisponíveis para o mercado do host não devem ser selecionadas.

* Cada música válida deve possuir o identificador Spotify associado.

**Prioridade: Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-02, PB-11, PB-12 e PB-13

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **4.15 PB-15 — Criação da playlist no Spotify** {#4.15-pb-15-—-criação-da-playlist-no-spotify}

**Épico:** EP-06 — Integrações e geração

**História:** Como host, quero que a playlist seja criada automaticamente na minha conta Spotify, para utilizá-la imediatamente.

**Descrição:** Criar uma playlist privada contendo as músicas selecionadas pelo motor de recomendação e registrar sua execução.

**Critérios de aceitação:**

* A playlist deve conter entre 20 e 30 músicas.

* Deve haver no máximo duas músicas por artista.

* A playlist deve ser criada como privada por padrão.

* O identificador e a URL da playlist devem ser armazenados na execução correspondente.

* O host deve receber o link da playlist criada.

**Prioridade: Alta**

**Estimativa:** 3 pontos

**Dependências:** PB-14

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **4.16 PB-16 — Resultado e explicabilidade**

**Épico:** EP-07 — Experiência e explicabilidade

**História:** Como integrante, quero visualizar o resultado e entender sua justiça, para avaliar se o grupo foi representado.

**Descrição:** Exibir playlist, compatibilidade, métricas de justiça, representação e justificativas legíveis.

**Critérios de aceitação:**

* A tela deve apresentar o link da playlist criada no Spotify.

* O resultado deve apresentar compatibilidade e fairness score da execução.

* A representação dos integrantes deve ser exibida em formato compreensível.

* Cada música selecionada deve possuir uma justificativa resumida.

* As explicações não devem identificar rejeições ou dados sensíveis de outro integrante.

**Prioridade: Média**

**Estimativa:** 5 pontos

**Dependências:** PB-13, PB-14 e PB-15

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **4.17 PB-17 — Interpretação estruturada do contexto**

**Épico:** EP-06 — Integrações e geração

**História:** Como host, quero que minha descrição livre seja interpretada, para transformar a intenção do encontro em critérios musicais estruturados.

**Descrição:** Integrar o LLM exclusivamente para interpretação de contexto, com schema validado e fallback determinístico.

**Critérios de aceitação:**

* A saída deve seguir um schema JSON com ocasião, humor, energia, tags positivas, tags negativas e itens a evitar.

* Uma resposta inválida deve ser rejeitada sem interromper a geração.

* Na indisponibilidade do LLM, o sistema deve continuar usando consenso, afinidade e popularidade.

* Dados brutos de top tracks e top artists não devem ser enviados ao LLM.

* O LLM não deve decidir diretamente quais músicas compõem a playlist.

**Prioridade: Média**

**Estimativa:** 5 pontos

**Dependências:** PB-06 e PB-10

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **4.18 PB-18 — Enriquecimento de contexto com Last.fm**

**Épico:** EP-06 — Integrações e geração

**História:** Como grupo, queremos que o contexto das candidatas seja avaliado, para que a playlist combine melhor com a ocasião.

**Descrição:** Consultar tags do Last.fm, combinar gêneros do Spotify e armazenar resultados em cache com indicação de confiança.

**Critérios de aceitação:**

* O sistema deve tentar tags da faixa antes das tags do artista.

* Na ausência de tags do Last.fm, deve utilizar gêneros do Spotify e os demais sinais disponíveis.

* Cada resultado deve registrar fonte e nível de confiança.

* Consultas repetidas devem reutilizar o cache enquanto válido.

* Resposta vazia ou erro do Last.fm não deve interromper a geração.

**Prioridade: Média**

**Estimativa:** 5 pontos

**Dependências:** PB-10 e PB-17

**Sprint sugerida:** Sprint 4

**Status inicial:** A fazer

## **4.19 PB-19 — Sequenciamento da experiência musical**

**Épico:** EP-07 — Experiência e explicabilidade

**História:** Como ouvinte, quero uma playlist com fluxo coerente, para evitar uma sequência desorganizada de músicas bem pontuadas.

**Descrição:** Ordenar a seleção final com regras simples de abertura, risco, alternância e repetição de artistas.

**Critérios de aceitação:**

* Duas músicas do mesmo artista não devem ficar consecutivas.

* A playlist deve começar com uma música de alta aceitação.

* Músicas de maior risco devem ser posicionadas preferencialmente na parte intermediária.

* O sequenciador deve respeitar o limite máximo de duas músicas por artista.

**Prioridade: Média**

**Estimativa:** 3 pontos

**Dependências:** PB-12, PB-14 e PB-15

**Sprint sugerida:** Sprint 4

**Status inicial:** A fazer

## **4.20 PB-20 — Feedback pós-playlist**

**Épico:** EP-07 — Experiência e explicabilidade

**História:** Como integrante, quero avaliar faixas e a playlist, para registrar minha satisfação e meu nível de representação.

**Descrição:** Coletar feedback por música e notas gerais, sem utilizar os dados no ranqueamento do MVP.

**Critérios de aceitação:**

* O integrante deve poder marcar like, dislike, more like this ou never again por faixa.

* O integrante deve poder informar satisfação e representação da playlist.

* O feedback deve ser associado ao usuário e à execução correta.

* Um usuário não deve registrar feedback em uma execução de sala da qual não participa.

* O sistema deve deixar explícito que o feedback será utilizado em evoluções futuras.

**Prioridade: Média**

**Estimativa:** 3 pontos

**Dependências:** PB-16

**Sprint sugerida:** Sprint 4

**Status inicial:** A fazer

## **4.21 PB-21 — Modo Descoberta**

**Épico:** EP-08 — Evolução do produto

**História:** Como grupo, queremos um modo que favoreça músicas novas, para descobrir faixas sem abandonar completamente o consenso.

**Descrição:** Criar um perfil de pesos que aumente a novidade e diversidade, mantendo limites de rejeição e justiça.

**Critérios de aceitação:**

* O modo deve ser selecionável apenas quando estiver habilitado na configuração do produto.

* A novidade deve possuir peso superior ao utilizado no modo Democrático.

* Rejeições fortes e representação mínima devem continuar sendo consideradas.

* O resultado deve explicar que o modo favoreceu a descoberta musical.

**Prioridade: Baixa**

**Estimativa:** 5 pontos

**Dependências:** PB-11, PB-12 e PB-16

**Sprint sugerida:** Sprint 5

**Status inicial:** A fazer

## **4.22 PB-22 — Agrupamento de perfis musicais**

**Épico:** EP-05 – Negociação e recomendação 

**História:** Como grupo com gostos diferentes, queremos que o sistema identifique subgrupos de afinidade, para compreender melhor a diversidade de preferências.

**Descrição:** Agrupar participantes com perfis musicais semelhantes utilizando apenas os dados autorizados pelo produto.

**Critérios de aceitação:**

* O agrupamento deve utilizar apenas dados musicais temporários autorizados.

* O sistema deve identificar quando não houver evidências suficientes para formar subgrupos.

* O agrupamento deve produzir resultados determinísticos para a mesma entrada.

* Os subgrupos identificados devem ficar disponíveis para o motor de recomendação.

**Prioridade:  Baixa**

**Estimativa:** 4 pontos

**Dependências:** PB-09

**Sprint sugerida:** Sprint 5

**Status inicial:** A fazer

## **4.23 PB-23 — Identificação de músicas-ponte** {#4.23-pb-23-—-identificação-de-músicas-ponte}

**Épico:** EP-05 – Negociação e recomendação 

**História:** Como grupo, queremos que o sistema identifique músicas capazes de aproximar diferentes gostos musicais, para aumentar a aceitação coletiva.

**Descrição:** Avaliar as músicas candidatas buscando aquelas que apresentam afinidade entre múltiplos subgrupos.

**Critérios de aceitação:**

* O sistema deve identificar músicas com boa aceitação entre diferentes subgrupos.

* As músicas-ponte devem receber marcação específica durante o ranqueamento.

* O cálculo não deve alterar os modos existentes quando a funcionalidade estiver desabilitada.

* O resultado deve indicar quais músicas foram consideradas faixas-ponte.

**Prioridade:  Baixa**

**Estimativa:** 5 pontos

**Dependências:** PB-11 e PB-22

**Sprint sugerida:** Sprint 5

**Status inicial:** A fazer

## **4.24 PB-24 — Balanceamento entre subgrupos** {#4.24-pb-24-—-balanceamento-entre-subgrupos}

**Épico:** EP-05 – Negociação e recomendação 

**História:** Como grupo com preferências distintas, queremos que a seleção considere os diferentes subgrupos identificados, para evitar que apenas um deles domine a playlist.

**Descrição:** Alternar músicas representativas dos subgrupos durante a seleção final, preservando os critérios de consenso e justiça.

**Critérios de aceitação:**

* A seleção deve limitar a predominância de um único subgrupo.

* Os critérios de rejeição e justiça já existentes devem continuar sendo respeitados.

* A funcionalidade deve ser opcional e configurável.

* A explicação da playlist deve indicar quando o balanceamento entre subgrupos foi utilizado.

**Prioridade:  Baixa**

**Estimativa:** 4 pontos

**Dependências:**  PB-12, PB-16, PB-22 e PB-23

**Sprint sugerida:** Sprint 5

**Status inicial:** A fazer

# **5 Sprint Backlogs**

Cada Sprint Backlog representa o subconjunto de itens do Product Backlog selecionado durante a Sprint Planning para ser entregue ao final do respectivo ciclo, junto com a Meta da Sprint que orienta as decisões da equipe durante a execução.

## **5.1 Sprint 1**

**Meta da Sprint:** Estabelecer a fundação técnica do produto e o fluxo básico de autenticação, salas e contexto, permitindo que um grupo já se autentique, crie uma sala, entre nela e informe o cenário do encontro.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-01 | Fundação técnica do produto | Alta | 2 | A fazer |
| PB-02 | Autenticação com Spotify | Alta | 5 | A fazer |
| PB-04 | Criação de sala efêmera | Alta | 5 | A fazer |
| PB-05 | Entrada e acompanhamento da sala | Alta | 5 | A fazer |
| PB-06 | Contexto e modo de consenso | Alta | 3 | A fazer |
| PB-08 | Coleta e cache de dados musicais | Alta | 5 | A fazer |

**Total da Sprint: 25 pontos**

## **5.2 Sprint 2**

**Meta da Sprint:** Implementar o núcleo do Preference Negotiation Engine (PNE): modelagem de gosto, geração do pool de candidatas, pontuação individual e coletiva, tratamento de rejeição e justiça, e controle seguro da execução da geração.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-09 | Modelagem de gosto e compatibilidade | Alta | 3 | A fazer |
| PB-10 | Geração do conjunto de candidatas | Alta | 5 | A fazer |
| PB-11 | Pontuação individual e coletiva | Alta | 8 | A fazer |
| PB-12 | Rejeição, justiça e modos de consenso | Alta | 5 | A fazer |
| PB-13 | Controle e histórico da geração | Alta | 3 | A fazer |

**Total da Sprint: 24 pontos**

## **5.3 Sprint 3**

**Meta da Sprint:** Entregar o fluxo principal de ponta a ponta: Vibe Check opcional, criação real da playlist na conta Spotify do host, tela de resultado com explicabilidade e interpretação estruturada do contexto por LLM.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-07 | Vibe Check opcional | Média | 5 | A fazer |
| PB-14 | Correspondência das músicas no Spotify | Alta | 5 | A fazer |
| PB-15 | Criação da playlist no Spotify | Alta | 3 | A fazer |
| PB-16 | Resultado e explicabilidade | Alta | 5 | A fazer |
| PB-17 | Interpretação estruturada do contexto | Média | 5 | A fazer |

**Total da Sprint: 23 pontos**

## **5.4 Sprint 4**

**Meta da Sprint:** Complementar a experiência e consolidar a qualidade do incremento: logout e remoção de dados, enriquecimento de contexto com Last.fm, sequenciamento da playlist, coleta de feedback e consolidação de testes e documentação.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-03 | Logout e remoção de dados | Média | 3 | A fazer |
| PB-18 | Enriquecimento de contexto com Last.fm | Média | 5 | A fazer |
| PB-19 | Sequenciamento da experiência musical | Média | 3 | A fazer |
| PB-20 | Feedback pós-playlist | Média | 3 | A fazer |

**Total da Sprint: 14 pontos**

## **5.5 Sprint 5**

**Meta:** Itens de prioridade Baixa, fora do MVP, a serem promovidos somente após o MVP estar estável ou mediante decisão explícita de escopo.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-21 | Modo Descoberta | Baixa | 5 | A fazer |
| PB-22 | Agrupamento de perfis musicais | Baixa | 4 | A fazer |
| PB-23 | Identificação de músicas-ponte | Baixa | 5 | A fazer |
| PB-24 | Balanceamento entre subgrupos | Baixa | 4 | A fazer |

**Total: 18 pontos**

# **6 Backlog Resumido e Priorizado**

| Ordem | ID | Épico | Item | Prioridade | Pontos | Dependências | Sprint | Status |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
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
| 13 | PB-14 | EP-06 | Correspondência musical | Alta | 5 | PB-02, PB-11, PB-12 e PB-13 | Sprint 3 | A fazer |
| 14 | PB-15 | EP-06 | Criação de playlist | Alta | 3 | PB-14 | Sprint 3 | A fazer |
| 15 | PB-16 | EP-07 | Resultado e explicabilidade | Média | 5 | PB-13, PB-14, PB-15 | Sprint 3 | A fazer |
| 16 | PB-17 | EP-06 | Contexto por LLM | Média | 5 | PB-06, PB-10 | Sprint 3 | A fazer |
| 17 | PB-03 | EP-02 | Logout e remoção | Média | 3 | PB-02 | Sprint 4 | A fazer |
| 18 | PB-18 | EP-06 | Contexto Last.fm | Média | 5 | PB-10 e PB-17 | Sprint 4 | A fazer |
| 19 | PB-19 | EP-07 | Sequenciamento | Média | 3 | PB-12, PB-14 e PB-15 | Sprint 4 | A fazer |
| 20 | PB-20 | EP-07 | Feedback | Média | 3 | PB-16 | Sprint 4 | A fazer |
| 21 | PB-21 | EP-05 | Modo Descoberta | Baixa | 5 | PB-11, PB-12 e PB-16 | Sprint 5 | A fazer |
| 22 | PB-22 | EP-05 | Agrupamento de perfis | Baixa | 4 | PB-09 | Sprint 5 | A fazer |
| 23 | PB-23 | EP-05 | Identificação músicas-pontes | Baixa | 5 | PB-11 e PB-22 | Sprint 5 | A fazer |
| 24 | PB-24 | EP-05 | Balanceamento subgrupos | Baixa | 4 | PB-12, PB-16, PB-22 e PB-23 | Sprint 5 | A fazer |

## **6.1 Totais**

* Total de histórias/itens: 24\.

* Total geral:  104 pontos.

* Prioridade Alta: 13 itens, totalizando 57 pontos.

* Prioridade Média: 7 itens, totalizando 29 pontos.

* Prioridade Baixa: 4 itens, totalizando 18 pontos.

* Sprint 1: 25 pontos.

* Sprint 2: 24 pontos.

* Sprint 3: 23 pontos.

* Sprint 4: 14 pontos.

* Sprint 5: 18 pontos.

# **7 Critérios de Priorização**

Os itens foram priorizados pelos seguintes critérios:

**Valor para o produto (MVP):** funcionalidades essenciais para a proposta de valor e para o fluxo principal recebem maior prioridade.

**Dependências técnicas:** funcionalidades que servem de base para outras são implementadas primeiro.

**Risco:** funcionalidades com maior risco técnico ou de integração são antecipadas para identificar problemas o quanto antes. 

**Impacto na experiência do usuário:** funcionalidades que melhoram significativamente a usabilidade ou a qualidade da experiência recebem prioridade após o fluxo principal. 

# **8 Definition of Ready (DoR)**

Uma história está pronta para entrar em uma Sprint quando:

* possui história de usuário, descrição e valor esperado compreensíveis;

* apresenta critérios de aceitação bem definidos;

* tem dependências  identificadas e estão resolvidas ou planejadas ;

* não contém dúvidas de negócio que impeçam a implementação;

* o  item cabe em uma Sprint.

# **9 Definition of Done (DoD)**

Uma história é considerada concluída quando:

* todos os critérios de aceitação foram atendidos;

* o código foi implementado e revisado por mais de um integrante;

* testes pertinentes executados com sucesso;

* não há exposição de informações sensíveis;

* A funcionalidade foi integrada ao incremento principal.

# **10 Dependências entre Funcionalidades**

| Funcionalidade | Depende de | Justificativa |
| :---- | :---- | :---- |
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

# **11 Riscos do Projeto**

| ID | Risco | Probabilidade | Impacto | Estratégia de mitigação |
| :---- | :---- | :---- | :---- | :---- |
| R-01 | Limitações do ambiente de desenvolvimento da API do Spotify (quota de usuários)  | Média | Alto | Pré-cadastrar contas para demonstração e solicitar acesso ao Extended Quota Mode o quanto antes.  |
| R-02 | Mudanças ou indisponibilidade da API do Spotify (endpoints, políticas ou restrições)  | Média | Alto | Realizar provas de conceito (spikes), acompanhar a documentação da API e implementar alternativas para funcionalidades afetadas.  |
| R-03 | Falhas de autenticação ou renovação de tokens  | Média | Alto | Centralizar a lógica de autenticação, automatizar a renovação de tokens e testar cenários de expiração e falha.  |
| R-04 | Vazamento de tokens ou preferências pessoais | Baixa | Alto | Utilizar armazenamento seguro de credenciais, criptografia quando aplicável, logs sanitizados e revisão de segurança antes das entregas.  |
| R-05 | Inconsistências causadas por acessos simultâneos durante a geração das playlists  | Média | Alto | Implementar mecanismos de sincronização, controle transacional e testes de concorrência.  |

