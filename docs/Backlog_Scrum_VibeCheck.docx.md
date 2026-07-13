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

*(Ao abrir no Microsoft Word, clique com o botão direito sobre esta área e selecione "Atualizar campo" para preencher automaticamente os números de página.)*

[**Ficha Técnica	2**](#heading=)

[Equipe Responsável pela Elaboração	2](#heading=)

[Papéis Scrum	2](#heading=)

[Público Alvo	2](#heading=)

[**Sumário	3**](#heading=)

[**1 Visão Geral do Produto	4**](#heading=)

[1.1 Descrição do Produto	4](#heading=)

[1.2 Problema que o Produto Busca Resolver	4](#heading=)

[1.3 Objetivo Geral	4](#heading=)

[1.4 Objetivos Específicos	4](#heading=)

[**2 Público-Alvo e Personas	4**](#heading=)

[2.1 Público-Alvo	4](#heading=)

[2.2 Persona 1 — Marina, a Anfitriã	5](#heading=)

[2.3 Persona 2 — Rafael, o Convidado com Gosto Minoritário	5](#heading=)

[2.4 Persona 3 — Lucas, o Participante Casual	5](#heading=)

[**3 Processo Ágil Adotado — Scrum	5**](#heading=)

[3.1 Papéis Scrum	5](#heading=)

[3.2 Eventos Scrum	6](#heading=)

[3.3 Artefatos Scrum	6](#heading=)

[3.4 Estrutura dos Itens do Product Backlog	6](#heading=)

[**4 Épicos do Produto	6**](#heading=)

[**5 Product Backlog	7**](#heading=)

[5.1 PB-01 — Fundação técnica do produto	7](#heading=)

[5.2 PB-02 — Autenticação com Spotify	7](#heading=)

[5.3 PB-03 — Logout e remoção de dados	8](#heading=)

[5.4 PB-04 — Criação de sala efêmera	8](#heading=)

[5.5 PB-05 — Entrada e acompanhamento da sala	9](#heading=)

[5.6 PB-06 — Contexto e modo de consenso	9](#heading=)

[5.7 PB-07 — Vibe Check opcional	10](#heading=)

[5.8 PB-08 — Coleta e cache de dados musicais	10](#heading=)

[5.9 PB-09 — Modelagem de gosto e compatibilidade	11](#heading=)

[5.10 PB-10 — Geração do conjunto de candidatas	11](#heading=)

[5.11 PB-11 — Pontuação individual e coletiva	11](#heading=)

[5.12 PB-12 — Rejeição, justiça e modos de consenso	12](#heading=)

[5.13 PB-13 — Controle e histórico da geração	12](#heading=)

[5.14 PB-14 — Correspondência e criação da playlist no Spotify	13](#heading=)

[5.15 PB-15 — Resultado e explicabilidade	13](#heading=)

[5.16 PB-16 — Interpretação estruturada do contexto	14](#heading=)

[5.17 PB-17 — Enriquecimento de contexto com Last.fm	14](#heading=)

[5.18 PB-18 — Sequenciamento da experiência musical	15](#heading=)

[5.19 PB-19 — Feedback pós-playlist	15](#heading=)

[5.20 PB-20 — Qualidade, robustez e documentação	15](#heading=)

[5.21 PB-21 — Modo Descoberta	16](#heading=)

[5.22 PB-22 — Agrupamento de gostos e faixas-ponte	16](#heading=)

[**6 Sprint Backlogs	17**](#heading=)

[6.1 Sprint 1	17](#heading=)

[6.2 Sprint 2	17](#heading=)

[6.3 Sprint 3	18](#heading=)

[6.4 Sprint 4	18](#heading=)

[6.5 Backlog de Versões Futuras	18](#heading=)

[**7 Backlog Resumido e Priorizado	18**](#heading=)

[7.1 Totais	19](#heading=)

[**8 Definição do Produto Mínimo Viável — MVP	19**](#heading=)

[**9 Critérios de Priorização	20**](#heading=)

[**10 Definition of Ready (DoR)	20**](#heading=)

[**11 Definition of Done (DoD)	20**](#heading=)

[**12 Dependências entre Funcionalidades	21**](#heading=)

[**13 Riscos do Projeto	21**](#heading=)

[**14 Regras para Atualização e Refinamento do Backlog	22**](#heading=)

[**15 Considerações Finais	22**](#heading=)

[**16 Referências Utilizadas	23**](#heading=)

# **1 Visão Geral do Produto**

## **1.1 Descrição do Produto**

O Vibe Check é uma aplicação web de recomendação musical em grupo. Um usuário, denominado host, cria uma sala efêmera e compartilha um código curto. Os demais integrantes entram na sala, autenticam-se por meio do Spotify e permitem que o sistema consulte seus principais artistas e músicas.

O produto não se limita a combinar históricos musicais. Seu elemento central é o Preference Negotiation Engine (PNE), ou Motor de Negociação de Preferências, responsável por equilibrar afinidade musical, contexto do encontro, rejeições, diversidade e representação dos integrantes. O resultado é uma playlist real criada na conta Spotify do host.

O MVP utiliza Spotify OAuth para autenticação, salas temporárias com até cinco integrantes, contexto informado pelo host, Vibe Check opcional, modos de consenso, cálculo de compatibilidade, seleção justa de músicas, sequenciamento e explicações sobre o resultado.

## **1.2 Problema que o Produto Busca Resolver**

Escolher músicas para um grupo é uma atividade sujeita a conflitos. Playlists baseadas apenas na média das preferências tendem a favorecer a maioria e podem ignorar participantes com gostos diferentes. Além disso, o histórico musical não representa necessariamente o humor ou a ocasião atual.

As soluções existentes normalmente misturam preferências passadas, mas oferecem pouco controle sobre contexto, rejeições, grau de descoberta e justiça. Como consequência, um integrante pode ter baixa representação mesmo quando a playlist apresenta uma boa aceitação média.

O Vibe Check busca resolver esse problema por meio de uma negociação computacional de preferências. O sistema considera a satisfação média, a menor satisfação individual, a cobertura dos integrantes, as rejeições e o contexto atual antes de criar a playlist.

## **1.3 Objetivo Geral**

Desenvolver uma aplicação web capaz de gerar playlists coletivas no Spotify que representem os integrantes de um grupo, considerando gostos musicais, contexto, rejeições e critérios de justiça.

## **1.4 Objetivos Específicos**

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

O público-alvo é formado por grupos pequenos, de uma a cinco pessoas, que desejam criar uma playlist conjunta para situações como festas, viagens, estudos, academias ou encontros sociais. O MVP é direcionado a usuários do Spotify previamente autorizados no aplicativo em Development Mode e com as condições de conta exigidas pela plataforma para a demonstração.

Também são partes interessadas a equipe de desenvolvimento, o professor da disciplina e avaliadores acadêmicos, responsáveis por verificar a adequação do processo de Engenharia de Software e a qualidade do incremento entregue.

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
| EP-01 | Fundação e qualidade | Estrutura técnica, banco de dados, migrações, testes e documentação necessários ao desenvolvimento sustentável. |
| EP-02 | Autenticação e privacidade | Identidade por Spotify OAuth, sessão segura, logout e remoção de dados. |
| EP-03 | Salas e colaboração | Criação de salas efêmeras, entrada por código, papéis e acompanhamento dos integrantes. |
| EP-04 | Contexto e preferências | Contexto informado pelo host, Vibe Check e snapshots musicais. |
| EP-05 | Negociação e recomendação | Modelagem de gosto, pool de candidatas, scoring, rejeição, justiça e modos de consenso. |
| EP-06 | Integrações e geração | Integração com Spotify, LLM e Last.fm, controle da geração e criação da playlist. |
| EP-07 | Experiência e explicabilidade | Sequenciamento, tela de resultado, explicações e feedback. |
| EP-08 | Evolução do produto | Funcionalidades previstas para versões posteriores, como descoberta e agrupamento de gostos. |

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

**Prioridade: ☑ Alta**

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

**Prioridade: ☑ Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-01

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **5.3 PB-03 — Logout e remoção de dados**

**Épico:** EP-02 — Autenticação e privacidade

**História:** Como usuário, quero encerrar minha sessão e remover meus dados, para manter controle sobre minha privacidade.

**Descrição:** Disponibilizar encerramento da sessão e fluxo de exclusão ou anonimização dos dados mantidos pelo sistema.

**Critérios de aceitação:**

* O logout deve invalidar a sessão da aplicação no backend.

* Após o logout, rotas autenticadas devem responder como não autorizadas.

* A solicitação de remoção deve excluir ou anonimizar os dados pessoais previstos pela política do produto.

* A operação não deve expor tokens ou informações de outros integrantes.

**Prioridade: ☑ Média**

**Estimativa:** 3 pontos

**Dependências:** PB-02

**Sprint sugerida:** Sprint 4

**Status inicial:** A fazer

## **5.4 PB-04 — Criação de sala efêmera**

**Épico:** EP-03 — Salas e colaboração

**História:** Como host, quero criar uma sala com um código curto, para convidar outras pessoas a participar da negociação musical.

**Descrição:** Criar uma sala temporária, associar o criador como host e gerar um código compartilhável.

**Critérios de aceitação:**

* Apenas um usuário autenticado deve poder criar uma sala.

* Cada sala deve receber um código curto único.

* O criador deve ser registrado como host e primeiro integrante.

* A sala deve receber data de expiração de 24 horas após sua criação.

* O sistema deve retornar o código e os dados iniciais da sala.

**Prioridade: ☑ Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-01 e PB-02

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **5.5 PB-05 — Entrada e acompanhamento da sala**

**Épico:** EP-03 — Salas e colaboração

**História:** Como convidado, quero entrar em uma sala pelo código e visualizar seus integrantes, para saber quando o grupo está pronto.

**Descrição:** Permitir entrada por código, impedir duplicidade e atualizar integrantes e estado da sala por polling.

**Critérios de aceitação:**

* O sistema deve rejeitar código inexistente ou sala expirada.

* A sala deve aceitar no máximo cinco integrantes.

* O mesmo usuário não deve ser associado duas vezes à mesma sala.

* Apenas membros da sala devem consultar seus dados; os demais devem receber resposta 403\.

* A interface deve atualizar integrantes e estado por polling a cada três a cinco segundos.

**Prioridade: ☑ Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-02 e PB-04

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **5.6 PB-06 — Contexto e modo de consenso**

**Épico:** EP-04 — Contexto e preferências

**História:** Como host, quero informar a ocasião, uma descrição e o modo de consenso, para adequar a playlist ao momento do grupo.

**Descrição:** Armazenar o contexto livre e oferecer os modos Democrático e Festa Segura.

**Critérios de aceitação:**

* Somente o host deve poder alterar o contexto e o modo da sala.

* O sistema deve aceitar ocasião, descrição livre ou ambos.

* O modo selecionado deve ser Democrático ou Festa Segura.

* As alterações devem ficar disponíveis para os integrantes na próxima atualização da sala.

**Prioridade: ☑ Alta**

**Estimativa:** 3 pontos

**Dependências:** PB-04

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **5.7 PB-07 — Vibe Check opcional**

**Épico:** EP-04 — Contexto e preferências

**História:** Como integrante, quero responder ou pular um questionário curto, para expressar meu humor e minhas preferências do momento.

**Descrição:** Apresentar de três a cinco perguntas gamificadas e converter as respostas em variáveis normalizadas para o motor.

**Critérios de aceitação:**

* O questionário deve apresentar no mínimo três e no máximo cinco perguntas.

* O usuário deve poder pular o questionário sem bloquear a geração.

* As respostas devem ser armazenadas por usuário e sala.

* As preferências derivadas devem possuir valores entre 0 e 1\.

* Uma nova resposta do mesmo usuário deve atualizar sua participação na geração seguinte.

**Prioridade: ☑ Média**

**Estimativa:** 5 pontos

**Dependências:** PB-05 e PB-06

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **5.8 PB-08 — Coleta e cache de dados musicais**

**Épico:** EP-04 — Contexto e preferências

**História:** Como integrante, quero que meus principais artistas e músicas sejam obtidos automaticamente, para participar sem preencher preferências manualmente.

**Descrição:** Consultar top artists e top tracks do Spotify e armazenar snapshots com validade configurável.

**Critérios de aceitação:**

* O sistema deve consultar apenas os endpoints Spotify autorizados no escopo do MVP.

* Faixas e artistas obtidos devem ser associados ao usuário em um snapshot.

* Um snapshot com menos de sete dias deve ser reutilizado por padrão.

* Um snapshot vencido deve ser atualizado antes da geração.

* Falha de renovação do token deve marcar a necessidade de nova autenticação.

**Prioridade: ☑ Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-02

**Sprint sugerida:** Sprint 1

**Status inicial:** A fazer

## **5.9 PB-09 — Modelagem de gosto e compatibilidade**

**Épico:** EP-05 — Negociação e recomendação

**História:** Como integrante, quero que o sistema modele meu gosto e calcule a compatibilidade do grupo, para representar as afinidades e diferenças existentes.

**Descrição:** Construir perfis temporários com faixas, artistas, gêneros e medidas de similaridade entre os participantes.

**Critérios de aceitação:**

* O modelo individual deve considerar faixas, artistas e gêneros disponíveis no snapshot.

* O cálculo deve tratar corretamente listas vazias e grupos com apenas um integrante.

* A compatibilidade deve resultar em valor normalizado e reprodutível para a mesma entrada.

* O motor não deve realizar chamadas de rede durante o cálculo.

**Prioridade: ☑ Alta**

**Estimativa:** 3 pontos

**Dependências:** PB-05 e PB-08

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **5.10 PB-10 — Geração do conjunto de candidatas**

**Épico:** EP-05 — Negociação e recomendação

**História:** Como grupo, queremos que o sistema reúna músicas relacionadas aos nossos gostos, para formar uma base equilibrada de possíveis escolhas.

**Descrição:** Construir o pool de candidatas a partir das músicas e artistas fortes dos integrantes e de fontes contextuais permitidas.

**Critérios de aceitação:**

* O conjunto deve incluir contribuições dos diferentes integrantes quando houver dados disponíveis.

* Uma mesma música não deve aparecer mais de uma vez no conjunto.

* A origem de cada candidata deve ser registrada.

* Candidatas sem identificação suficiente para busca posterior devem ser descartadas com motivo.

**Prioridade: ☑ Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-06 e PB-09

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **5.11 PB-11 — Pontuação individual e coletiva**

**Épico:** EP-05 — Negociação e recomendação

**História:** Como grupo, queremos que cada música candidata seja avaliada individual e coletivamente, para selecionar músicas adequadas ao conjunto de participantes.

**Descrição:** Implementar as fórmulas configuráveis de afinidade individual e score de grupo definidas para o PNE.

**Critérios de aceitação:**

* O score individual deve considerar afinidade de faixa, artista, gênero ou tag, popularidade e novidade disponíveis.

* O score de grupo deve considerar média, menor score individual, cobertura, contexto e diversidade.

* Os pesos devem permanecer centralizados e configuráveis.

* A mesma entrada e configuração devem produzir o mesmo resultado.

* Os cálculos principais devem possuir testes automatizados com valores esperados.

**Prioridade: ☑ Alta**

**Estimativa:** 8 pontos

**Dependências:** PB-09 e PB-10

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **5.12 PB-12 — Rejeição, justiça e modos de consenso**

**Épico:** EP-05 — Negociação e recomendação

**História:** Como integrante, quero que minhas rejeições e preferências minoritárias sejam consideradas, para não ser ignorado pela preferência média do grupo.

**Descrição:** Aplicar penalidades de rejeição, least misery, cobertura, representação mínima e perfis de peso dos modos de consenso.

**Critérios de aceitação:**

* Uma rejeição forte deve reduzir o score da música mesmo quando ela agradar à maioria.

* O sistema deve calcular satisfação média, menor satisfação, cobertura e fairness score.

* O modo Democrático deve atribuir o mesmo peso aos integrantes.

* O modo Festa Segura deve favorecer familiaridade e baixa rejeição.

* A seleção deve tentar elevar o integrante menos representado sem reduzir excessivamente a satisfação do grupo.

**Prioridade: ☑ Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-11. Quando PB-07 estiver disponível, suas respostas serão usadas como entrada opcional, sem bloquear esta história.

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **5.13 PB-13 — Controle e histórico da geração**

**Épico:** EP-06 — Integrações e geração

**História:** Como host, quero solicitar a geração de forma segura, para que cliques repetidos não criem playlists duplicadas.

**Descrição:** Criar uma execução de playlist por solicitação, controlar estados e impedir concorrência na mesma sala.

**Critérios de aceitação:**

* A primeira solicitação válida deve criar uma execução com estado running.

* Uma solicitação concorrente na mesma sala deve retornar resposta 409\.

* Uma execução concluída deve receber estado completed e uma falha deve receber estado failed.

* Após uma falha, o host deve poder iniciar uma nova execução controlada.

* Cada nova geração concluída deve possuir registro independente.

**Prioridade: ☑ Alta**

**Estimativa:** 3 pontos

**Dependências:** PB-05, PB-06 e PB-11

**Sprint sugerida:** Sprint 2

**Status inicial:** A fazer

## **5.14 PB-14 — Correspondência e criação da playlist no Spotify**

**Épico:** EP-06 — Integrações e geração

**História:** Como host, quero receber uma playlist real com músicas válidas na minha conta Spotify, para utilizá-la imediatamente.

**Descrição:** Resolver candidatas pelo Spotify Search com o token do host, validar disponibilidade e criar a playlist privada.

**Critérios de aceitação:**

* A busca deve usar o mercado associado ao token do host quando disponível.

* Título e artista devem ser normalizados para tratar variações como live, remastered e acoustic.

* Resultados abaixo da confiança mínima ou indisponíveis devem ser descartados com motivo registrado.

* A seleção final deve conter de 20 a 30 músicas e no máximo duas músicas por artista.

* A playlist deve ser privada por padrão e criada na conta do host.

* O identificador e a URL da playlist devem ser armazenados na execução correspondente.

**Prioridade: ☑ Alta**

**Estimativa:** 8 pontos

**Dependências:** PB-02, PB-11, PB-12 e PB-13

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **5.15 PB-15 — Resultado e explicabilidade**

**Épico:** EP-07 — Experiência e explicabilidade

**História:** Como integrante, quero visualizar o resultado e entender sua justiça, para avaliar se o grupo foi representado.

**Descrição:** Exibir playlist, compatibilidade, métricas de justiça, representação e justificativas legíveis.

**Critérios de aceitação:**

* A tela deve apresentar o link da playlist criada no Spotify.

* O resultado deve apresentar compatibilidade e fairness score da execução.

* A representação dos integrantes deve ser exibida em formato compreensível.

* Cada música selecionada deve possuir uma justificativa resumida.

* As explicações não devem identificar rejeições ou dados sensíveis de outro integrante.

**Prioridade: ☑ Alta**

**Estimativa:** 5 pontos

**Dependências:** PB-13 e PB-14

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **5.16 PB-16 — Interpretação estruturada do contexto**

**Épico:** EP-06 — Integrações e geração

**História:** Como host, quero que minha descrição livre seja interpretada, para transformar a intenção do encontro em critérios musicais estruturados.

**Descrição:** Integrar o LLM exclusivamente para interpretação de contexto, com schema validado e fallback determinístico.

**Critérios de aceitação:**

* A saída deve seguir um schema JSON com ocasião, humor, energia, tags positivas, tags negativas e itens a evitar.

* Uma resposta inválida deve ser rejeitada sem interromper a geração.

* Na indisponibilidade do LLM, o sistema deve continuar usando consenso, afinidade e popularidade.

* Dados brutos de top tracks e top artists não devem ser enviados ao LLM.

* O LLM não deve decidir diretamente quais músicas compõem a playlist.

**Prioridade: ☑ Média**

**Estimativa:** 5 pontos

**Dependências:** PB-06 e PB-10

**Sprint sugerida:** Sprint 3

**Status inicial:** A fazer

## **5.17 PB-17 — Enriquecimento de contexto com Last.fm**

**Épico:** EP-06 — Integrações e geração

**História:** Como grupo, queremos que o contexto das candidatas seja avaliado, para que a playlist combine melhor com a ocasião.

**Descrição:** Consultar tags do Last.fm, combinar gêneros do Spotify e armazenar resultados em cache com indicação de confiança.

**Critérios de aceitação:**

* O sistema deve tentar tags da faixa antes das tags do artista.

* Na ausência de tags do Last.fm, deve utilizar gêneros do Spotify e os demais sinais disponíveis.

* Cada resultado deve registrar fonte e nível de confiança.

* Consultas repetidas devem reutilizar o cache enquanto válido.

* Resposta vazia ou erro do Last.fm não deve interromper a geração.

**Prioridade: ☑ Média**

**Estimativa:** 5 pontos

**Dependências:** PB-10 e PB-16

**Sprint sugerida:** Sprint 4

**Status inicial:** A fazer

## **5.18 PB-18 — Sequenciamento da experiência musical**

**Épico:** EP-07 — Experiência e explicabilidade

**História:** Como ouvinte, quero uma playlist com fluxo coerente, para evitar uma sequência desorganizada de músicas bem pontuadas.

**Descrição:** Ordenar a seleção final com regras simples de abertura, risco, alternância e repetição de artistas.

**Critérios de aceitação:**

* Duas músicas do mesmo artista não devem ficar consecutivas.

* A playlist deve começar com uma música de alta aceitação.

* Músicas de maior risco devem ser posicionadas preferencialmente na parte intermediária.

* O sequenciador deve respeitar o limite máximo de duas músicas por artista.

**Prioridade: ☑ Média**

**Estimativa:** 3 pontos

**Dependências:** PB-12 e PB-14

**Sprint sugerida:** Sprint 4

**Status inicial:** A fazer

## **5.19 PB-19 — Feedback pós-playlist**

**Épico:** EP-07 — Experiência e explicabilidade

**História:** Como integrante, quero avaliar faixas e a playlist, para registrar minha satisfação e meu nível de representação.

**Descrição:** Coletar feedback por música e notas gerais, sem utilizar os dados no ranqueamento do MVP.

**Critérios de aceitação:**

* O integrante deve poder marcar like, dislike, more like this ou never again por faixa.

* O integrante deve poder informar satisfação e representação da playlist.

* O feedback deve ser associado ao usuário e à execução correta.

* Um usuário não deve registrar feedback em uma execução de sala da qual não participa.

* O sistema deve deixar explícito que o feedback será utilizado em evoluções futuras.

**Prioridade: ☑ Média**

**Estimativa:** 3 pontos

**Dependências:** PB-15

**Sprint sugerida:** Sprint 4

**Status inicial:** A fazer

## **5.20 PB-20 — Qualidade, robustez e documentação**

**Épico:** EP-01 — Fundação e qualidade

**História:** Como equipe de desenvolvimento, queremos validar o produto e documentar seu uso, para entregar um incremento verificável e passível de manutenção.

**Descrição:** Consolidar testes automatizados, fallbacks, proteção de dados, documentação técnica e roteiro de demonstração.

**Critérios de aceitação:**

* O motor deve possuir testes para scoring, justiça, rejeição, duplicidade e limite por artista.

* A API deve possuir testes para autorização, entrada duplicada e Generation Lock.

* Clientes externos devem possuir testes mockados para token expirado, resposta 429, JSON inválido e busca sem resultado.

* Nenhum teste ou log deve expor tokens reais.

* O README deve conter instruções atualizadas de configuração e execução.

* Um roteiro de demonstração do fluxo principal deve ser documentado.

**Prioridade: ☑ Alta**

**Estimativa:** 8 pontos

**Dependências:** PB-02 a PB-19, sendo executado continuamente durante todas as sprints.

**Sprint sugerida:** Sprint 4 (consolidação contínua)

**Status inicial:** A fazer

## **5.21 PB-21 — Modo Descoberta**

**Épico:** EP-08 — Evolução do produto

**História:** Como grupo, queremos um modo que favoreça músicas novas, para descobrir faixas sem abandonar completamente o consenso.

**Descrição:** Criar um perfil de pesos que aumente novidade e diversidade, mantendo limites de rejeição e justiça.

**Critérios de aceitação:**

* O modo deve ser selecionável apenas quando estiver habilitado na configuração do produto.

* A novidade deve possuir peso superior ao utilizado no modo Democrático.

* Rejeições fortes e representação mínima devem continuar sendo consideradas.

* O resultado deve explicar que o modo favoreceu descoberta musical.

**Prioridade: ☑ Baixa**

**Estimativa:** 5 pontos

**Dependências:** PB-11, PB-12 e PB-15

**Sprint sugerida:** Versão futura

**Status inicial:** A fazer

## **5.22 PB-22 — Agrupamento de gostos e faixas-ponte**

**Épico:** EP-08 — Evolução do produto

**História:** Como grupo com gostos divergentes, queremos que o sistema identifique subgrupos e músicas intermediárias, para reduzir a distância entre preferências muito diferentes.

**Descrição:** Agrupar perfis semelhantes e alternar consenso geral, representações dos subgrupos e possíveis faixas-ponte.

**Critérios de aceitação:**

* O agrupamento deve utilizar somente dados musicais autorizados e temporários.

* O sistema deve identificar quando não há evidência suficiente para formar subgrupos.

* A seleção deve limitar a predominância de um único subgrupo.

* A explicação deve indicar, de forma agregada, quando uma faixa atua como ponte musical.

* A funcionalidade não deve alterar o comportamento dos modos existentes quando estiver desabilitada.

**Prioridade: ☑ Baixa**

**Estimativa:** 13 pontos

**Dependências:** PB-09, PB-11, PB-12 e PB-15

**Sprint sugerida:** Versão futura

**Status inicial:** A fazer

# **6 Sprint Backlogs**

Cada Sprint Backlog representa o subconjunto de itens do Product Backlog selecionado durante a Sprint Planning para ser entregue ao final do respectivo ciclo, junto com a Meta da Sprint que orienta as decisões da equipe durante a execução.

## **6.1 Sprint 1**

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

## **6.2 Sprint 2**

**Meta da Sprint:** Implementar o núcleo do Preference Negotiation Engine (PNE): modelagem de gosto, geração do pool de candidatas, pontuação individual e coletiva, tratamento de rejeição e justiça, e controle seguro da execução da geração.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-09 | Modelagem de gosto e compatibilidade | Alta | 3 | A fazer |
| PB-10 | Geração do conjunto de candidatas | Alta | 5 | A fazer |
| PB-11 | Pontuação individual e coletiva | Alta | 8 | A fazer |
| PB-12 | Rejeição, justiça e modos de consenso | Alta | 5 | A fazer |
| PB-13 | Controle e histórico da geração | Alta | 3 | A fazer |

**Total da Sprint: 24 pontos**

## **6.3 Sprint 3**

**Meta da Sprint:** Entregar o fluxo principal de ponta a ponta: Vibe Check opcional, criação real da playlist na conta Spotify do host, tela de resultado com explicabilidade e interpretação estruturada do contexto por LLM.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-07 | Vibe Check opcional | Média | 5 | A fazer |
| PB-14 | Correspondência e criação da playlist no Spotify | Alta | 8 | A fazer |
| PB-15 | Resultado e explicabilidade | Alta | 5 | A fazer |
| PB-16 | Interpretação estruturada do contexto | Média | 5 | A fazer |

**Total da Sprint: 23 pontos**

## **6.4 Sprint 4**

**Meta da Sprint:** Complementar a experiência e consolidar a qualidade do incremento: logout e remoção de dados, enriquecimento de contexto com Last.fm, sequenciamento da playlist, coleta de feedback e consolidação de testes e documentação.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-03 | Logout e remoção de dados | Média | 3 | A fazer |
| PB-17 | Enriquecimento de contexto com Last.fm | Média | 5 | A fazer |
| PB-18 | Sequenciamento da experiência musical | Média | 3 | A fazer |
| PB-19 | Feedback pós-playlist | Média | 3 | A fazer |
| PB-20 | Qualidade, robustez e documentação | Alta | 8 | A fazer |

**Total da Sprint: 22 pontos**

## **6.5 Backlog de Versões Futuras**

**Meta:** Itens de prioridade Baixa, fora do MVP, a serem promovidos somente após o MVP estar estável ou mediante decisão explícita de escopo.

| ID | Item | Prioridade | Pontos | Status |
| :---- | :---- | :---- | :---- | :---- |
| PB-21 | Modo Descoberta | Baixa | 5 | A fazer |
| PB-22 | Agrupamento de gostos e faixas-ponte | Baixa | 13 | A fazer |

**Total: 18 pontos**

# **7 Backlog Resumido e Priorizado**

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

## **7.1 Totais**

* Total de histórias/itens: 22\.

* Total geral: 112 pontos.

* Prioridade Alta: 14 itens, totalizando 70 pontos.

* Prioridade Média: 6 itens, totalizando 24 pontos.

* Prioridade Baixa: 2 itens, totalizando 18 pontos.

* Sprint 1: 25 pontos.

* Sprint 2: 24 pontos.

* Sprint 3: 23 pontos.

* Sprint 4: 22 pontos.

* Versões futuras: 18 pontos.

# **8 Definição do Produto Mínimo Viável — MVP**

O MVP é composto por PB-01, PB-02, PB-04, PB-05, PB-06, PB-08, PB-09, PB-10, PB-11, PB-12, PB-13, PB-14 e PB-15, com apoio contínuo das práticas de qualidade de PB-20.

Esses itens permitem executar o fluxo principal:

* autenticar os participantes;

* criar e preencher uma sala;

* informar o contexto e o modo;

* obter os gostos musicais;

* calcular compatibilidade e pontuações;

* aplicar rejeição e justiça;

* gerar uma playlist real no Spotify;

* explicar o resultado.

A hipótese validada pelo MVP é: um motor que considera contexto, menor satisfação individual e representação produz uma playlist coletiva percebida como mais justa do que uma simples mistura ou média dos históricos musicais.

Vibe Check, interpretação pelo LLM, tags do Last.fm, sequenciamento avançado e feedback são importantes para o MVP completo descrito no README, mas não são indispensáveis para a primeira validação técnica da hipótese. Modo Descoberta e agrupamento de gostos permanecem em versões futuras.

O núcleo do MVP possui 67 pontos nominais, sem contar integralmente a consolidação de PB-20. Com capacidade assumida de 25 pontos por Sprint, são necessárias aproximadamente três Sprints de duas semanas. Portanto, o prazo original de cerca de um mês exige aumento comprovado de velocidade, paralelização segura ou redução adicional de escopo. Essa decisão deve ser tomada após a equipe medir sua velocidade na primeira Sprint.

# **9 Critérios de Priorização**

Os itens foram priorizados pelos seguintes critérios:

**Valor para a hipótese do produto:** funções que demonstram negociação musical e justiça recebem prioridade superior

**Dependência técnica:** infraestrutura, autenticação, salas e dados musicais antecedem o motor e a geração

**Risco:** integrações com Spotify e regras centrais são antecipadas para revelar problemas cedo

**Obrigatoriedade do fluxo:** itens sem os quais não existe uma playlist utilizável são classificados como Alta

**Experiência complementar:** recursos que enriquecem, mas não desbloqueiam o fluxo principal, são classificados como Média

**Evolução futura:** funcionalidades fora do prazo e do núcleo do MVP recebem prioridade Baixa

# **10 Definition of Ready (DoR)**

Uma história está pronta para entrar em uma Sprint quando:

* possui história de usuário, descrição e valor esperado compreensíveis;

* apresenta entre três e seis critérios de aceitação objetivos;

* tem dependências identificadas e concluídas ou planejadas antes dela;

* possui estimativa acordada pela equipe;

* não contém dúvidas de negócio que impeçam a implementação;

* integrações externas necessárias foram verificadas ou possuem estratégia de mock;

* dados, regras e exceções relevantes estão identificados;

* o item cabe em uma Sprint ou foi dividido.

# **11 Definition of Done (DoD)**

Uma história é considerada concluída quando:

* todos os critérios de aceitação foram atendidos;

* o código foi revisado por pelo menos outro integrante;

* testes automatizados pertinentes foram criados e aprovados;

* testes regressivos existentes continuam aprovados;

* migrações e configurações necessárias foram documentadas;

* nenhum token ou segredo foi incluído no código ou nos logs;

* mensagens de erro e fallbacks relevantes foram verificados;

* a funcionalidade foi integrada ao incremento principal;

* a documentação afetada foi atualizada;

* o Product Owner ou representante acadêmico aceitou o resultado demonstrado.

# **12 Dependências entre Funcionalidades**

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

# **13 Riscos do Projeto**

| ID | Risco | Probabilidade | Impacto | Estratégia de mitigação |
| :---- | :---- | :---- | :---- | :---- |
| R-01 | Limite de cinco usuários autorizados no Spotify Development Mode | Alta | Alto | Pré-cadastrar contas da demonstração e iniciar cedo a avaliação de Extended Quota Mode. |
| R-02 | Endpoints Spotify indisponíveis ou restritos para novos aplicativos | Média | Alto | Realizar spike técnico e não depender de Recommendations, Audio Features ou Audio Analysis. |
| R-03 | Expiração ou falha de renovação do token | Média | Alto | Centralizar refresh, marcar reautenticação necessária e testar falhas do fluxo. |
| R-04 | Música indisponível no mercado do host | Alta | Médio | Buscar com o token do host, validar mercado e manter candidatas substitutas. |
| R-05 | Correspondência com versão incorreta da música | Média | Médio | Normalizar título e artista, exigir confiança mínima e registrar descarte. |
| R-06 | Resposta inválida ou indisponibilidade do LLM | Média | Médio | Validar schema e manter fallback determinístico sem IA. |
| R-07 | Ausência de tags no Last.fm | Alta | Baixo | Aplicar cascata para tags do artista, gêneros Spotify e sinais de consenso. |
| R-08 | Vazamento de tokens ou preferências pessoais | Baixa | Alto | Criptografia, cookies seguros, logs sanitizados e revisão de segurança. |
| R-09 | Gerações duplicadas por concorrência | Média | Alto | Generation Lock, estado transacional e resposta 409\. |
| R-10 | Backlog incompatível com o prazo de um mês | Alta | Alto | Medir velocidade na primeira sprint, reduzir escopo ou renegociar prazo. |
| R-11 | Questionário causar abandono | Média | Médio | Limitar a cinco perguntas e permitir que o usuário pule. |
| R-12 | Maioria dominar a seleção | Média | Alto | Usar least misery, cobertura, rejeição e testes com grupos divergentes. |
| R-13 | Falta de dados musicais de um integrante | Média | Médio | Tratar listas vazias, informar limitação e utilizar os demais sinais disponíveis. |
| R-14 | Crescimento não controlado do escopo | Alta | Alto | Manter itens futuros fora do MVP e exigir refinamento antes de promoção. |

# **14 Regras para Atualização e Refinamento do Backlog**

* O Product Owner deve revisar prioridades antes de cada Sprint Planning.

* Histórias podem ser detalhadas progressivamente, mas não devem entrar na Sprint sem atender à DoR.

* Novas funcionalidades devem indicar valor, critérios de aceitação, dependências e impacto no MVP.

* Alterações de escopo devem atualizar histórias relacionadas, totais e dependências.

* Histórias acima de 13 pontos devem ser obrigatoriamente decompostas.

* A velocidade deve ser recalculada ao final de cada Sprint usando apenas itens concluídos pela DoD.

* Itens não concluídos retornam ao Product Backlog e devem ser reestimados quando necessário; a Sprint não deve ser estendida.

* Critérios de aceitação não devem ser removidos apenas para declarar uma história concluída.

* Riscos e restrições de serviços externos devem ser revisados em cada refinamento.

* Itens de prioridade Baixa só devem ser promovidos quando o MVP estiver estável ou quando houver decisão explícita de escopo.

# **15 Considerações Finais**

O backlog organiza o desenvolvimento do Vibe Check de forma incremental e rastreável. As histórias iniciais estabelecem a infraestrutura, a autenticação, as salas e a coleta de dados. Em seguida, o motor determinístico implementa o diferencial acadêmico do produto: negociar preferências em vez de calcular apenas uma média.

A priorização preserva um caminho demonstrável até a criação de uma playlist real no Spotify. Recursos de contexto por LLM, tags do Last.fm, sequenciamento e feedback complementam a experiência, mas possuem fallbacks ou podem ser postergados durante a validação inicial.

As estimativas são relativas e devem ser refinadas com base na velocidade observada. A diferença entre o prazo aproximado de um mês e o esforço estimado do MVP representa um risco que deve ser tratado por negociação de escopo, não por extensão informal das Sprints ou redução dos critérios de qualidade.

# **16 Referências Utilizadas**

* README do projeto Group Music Recommender — Vibe Check, seções anteriores ao tópico 4\.

* ELIAS, Gledson. Desenvolvimento Ágil. Material da disciplina de Engenharia de Software.

* ELIAS, Gledson. Engenharia de Requisitos. Material da disciplina de Engenharia de Software.