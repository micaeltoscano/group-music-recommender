# Diagrama de Casos de Uso — Vibe Check

![Casos de Uso](casos-de-uso.png)

## Fonte PlantUML

```plantuml
@startuml casos-de-uso
left to right direction
skinparam packageStyle rectangle
skinparam usecase {
  BackgroundColor #FEFEFE
  BorderColor #333333
}

actor "Membro da Sala" as Membro
actor "Host" as Host
actor "Spotify" as SpotifySys
actor "Last.fm" as LastFm
actor "IA (LLM local)" as LLM

Host --|> Membro

rectangle "Vibe Check" {

  ' --- Casos de uso primarios (nivel RF-01..RF-11) ---
  usecase "Autenticar com Spotify" as UC1
  usecase "Encerrar sessão e remover dados" as UC2
  usecase "Criar sala" as UC3
  usecase "Entrar em sala" as UC4
  usecase "Definir contexto e modo de consenso" as UC5
  usecase "Responder Vibe Check" as UC6
  usecase "Gerar playlist" as UC7
  usecase "Visualizar resultado e explicação" as UC8
  usecase "Enviar feedback" as UC9

  ' --- Subfluxos do PNE, incluidos por "Gerar playlist" ---
  usecase "Interpretar contexto com IA" as UC7a
  usecase "Calcular compatibilidade do grupo" as UC7b
  usecase "Gerar conjunto de candidatas" as UC7c
  usecase "Enriquecer contexto das candidatas" as UC7d
  usecase "Pontuar candidatas e aplicar justiça" as UC7e
  usecase "Corresponder faixas no Spotify" as UC7f
  usecase "Sequenciar faixas selecionadas" as UC7g
  usecase "Criar playlist no Spotify" as UC7h

  ' --- Variacoes opcionais (extend) ---
  usecase "Aplicar Modo Descoberta" as UC10
  usecase "Identificar músicas-ponte entre subgrupos" as UC11a
  usecase "Balancear entre subgrupos" as UC11b
}

' --- Associacoes: atores humanos ---
Membro -- UC1
Membro -- UC2
Membro -- UC4
Membro -- UC6
Membro -- UC8
Membro -- UC9

Host -- UC3
Host -- UC5
Host -- UC7

' --- Associacoes: atores externos (sistemas) ---
SpotifySys -- UC1
SpotifySys -- UC7f
SpotifySys -- UC7h
LastFm -- UC7d
LLM -- UC7a

' --- Inclusoes obrigatorias do pipeline do PNE ---
UC7 ..> UC7a : <<include>>
UC7 ..> UC7b : <<include>>
UC7 ..> UC7c : <<include>>
UC7 ..> UC7d : <<include>>
UC7 ..> UC7e : <<include>>
UC7 ..> UC7f : <<include>>
UC7 ..> UC7g : <<include>>
UC7 ..> UC7h : <<include>>

' --- Extensoes condicionais ---
UC10 ..> UC7c : <<extend>>
UC11a ..> UC7b : <<extend>>
UC11b ..> UC7e : <<extend>>

@enduml
```

## Decisões de modelagem

Adotamos generalização entre atores (`Host --|> Membro`) porque isso é exatamente o que o código
representa: o host é gravado como o primeiro `MusicSessionMember` da sala (com `role="host"`), então
ele herda todos os casos de uso de um membro comum (autenticar, entrar — embora não exerça este
último na prática —, responder Vibe Check, ver resultado, enviar feedback) e adiciona apenas os três
que exigem o guard `RoomHostRequiredError` no `room_service`/`generation_service`: criar sala, definir
contexto/modo e gerar playlist. As personas "Rafael" e "Lucas" do backlog não geram atores distintos
porque, no código, ambas caem no mesmo papel técnico de membro — a diferença entre elas é de
comportamento (responder vs. pular o Vibe Check), não de capacidade do sistema.

O nível de granularidade segue os RF-01 a RF-11: cada requisito funcional do documento corresponde a
um ou dois casos de uso de topo (ex.: RF-02 → "Criar sala" + "Entrar em sala"; RF-09 → "Visualizar
resultado e explicação" + "Enviar feedback"), evitando abrir um caso de uso por item do Product
Backlog. "Gerar playlist" concentra RF-05 a RF-08 como subfluxos «include» porque, em
`generation_service.execute_generation`, essas etapas (interpretar contexto, calcular
compatibilidade, gerar candidatas, enriquecer contexto, pontuar/aplicar justiça, casar faixas no
Spotify, sequenciar e criar a playlist) sempre executam nessa ordem, sem serem acionadas
independentemente por nenhum ator — não faria sentido tratá-las como casos de uso de primeiro nível.
Já RF-10 (Modo Descoberta) e RF-11 (clusterização, músicas-ponte, balanceamento) viraram «extend»
sobre os pontos do pipeline que eles alteram condicionalmente (respectivamente
`calculate_candidate_diversity_score`, `cluster_taste_profiles`/`evaluate_bridge_candidate` e
`balance_subgroup_candidates`), pois só se aplicam quando o modo/feature correspondente está
habilitado, e não fazem parte do fluxo básico do caso de uso base.

Os três sistemas externos (Spotify, Last.fm e IA local) foram modelados como atores porque
participam de interações reais e observáveis pelo sistema (chamadas HTTP/RPC saindo do backend), e
foram associados diretamente ao subfluxo específico em que atuam — Spotify em "Autenticar com
Spotify" (OAuth), "Corresponder faixas no Spotify" e "Criar playlist no Spotify"; Last.fm em
"Enriquecer contexto das candidatas"; e a IA local em "Interpretar contexto com IA" — em vez de
associá-los ao caso de uso "Gerar playlist" como um todo, o que esconderia qual etapa exatamente
depende de qual serviço externo.

Incluímos "Encerrar sessão e remover dados" como caso de uso pleno mesmo sem existir hoje um botão
correspondente no frontend (`POST /auth/logout` e `DELETE /auth/me` não são chamados por nenhuma tela
em `frontend/src`): é uma capacidade real do sistema, exigida pelo RF-01 e já validada pelo QA
(PB-03), e a ausência de um gatilho de UI é uma lacuna de integração do frontend — um detalhe de
implementação abaixo do nível de abstração deste diagrama, não uma característica ausente do sistema.
