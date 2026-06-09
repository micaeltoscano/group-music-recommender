# 🎵 Sistema de Recomendação Musical para Grupos

Uma plataforma web que permite que usuários conectem suas contas Spotify, compartilhem suas preferências musicais e participem de grupos para gerar playlists de consenso baseadas nos gostos coletivos.

## 📖 Visão Geral

O objetivo deste projeto é resolver um problema comum em situações como viagens, festas, estudos em grupo, treinos e encontros sociais: encontrar músicas que agradem a todos os participantes.

Diferente dos sistemas tradicionais de recomendação individual, esta plataforma foca na experiência musical coletiva, calculando compatibilidade entre usuários e gerando playlists compartilhadas.

---

## 🎯 Problema

Plataformas como Spotify oferecem excelentes recomendações individuais, mas não possuem mecanismos eficientes para recomendar músicas para grupos de pessoas com gostos diferentes.

Este projeto busca solucionar esse problema através da análise das preferências musicais dos participantes.

---

## 💡 Solução Proposta

A plataforma permitirá:

* Cadastro e login de usuários;
* Integração com Spotify;
* Importação de artistas, músicas e gêneros favoritos;
* Criação e gerenciamento de grupos;
* Entrada em grupos por convite;
* Cálculo de compatibilidade musical;
* Geração de playlists de consenso;
* Explicação dos motivos das recomendações.

---

## 🏗️ Arquitetura Geral

![Print da integração Spotify](<Sem título.jpg>)

A integração com Spotify será utilizada apenas para importar dados musicais. A autenticação principal será realizada pela própria plataforma.

---

## 📦 Módulos do Sistema

### 🔐 Autenticação

Responsável pelo acesso dos usuários ao sistema.

#### Funcionalidades

* Cadastro de usuário;
* Login;
* Logout;
* Geração de token JWT;
* Validação de sessão;
* Recuperação de senha (opcional).

#### Tecnologias sugeridas

* FastAPI;
* JWT;
* Hash de senhas.

#### Rotas

```http
POST /auth/register
POST /auth/login
POST /auth/logout
GET /auth/me
```

---

### 👤 Perfil do Usuário e Preferências

Responsável por armazenar informações do usuário e seus dados musicais.

#### Funcionalidades

* Visualizar perfil;
* Editar dados básicos;
* Armazenar artistas favoritos;
* Armazenar músicas favoritas;
* Armazenar gêneros predominantes;
* Vincular conta Spotify;
* Atualizar dados importados.

#### Estrutura básica

```text
id
nome
email
foto
data_criacao
spotify_id
```

---

### 🎧 Integração Spotify

Responsável pela conexão com a conta Spotify e importação de dados musicais.

#### Funcionalidades

* Conectar conta Spotify;
* Autorização via OAuth;
* Importar artistas favoritos;
* Importar músicas favoritas;
* Importar playlists;
* Importar gêneros musicais;
* Atualizar dados sincronizados.

#### Dados disponíveis para o MVP

* Artistas;
* Músicas;
* Gêneros;
* Playlists;
* Popularidade;
* Duração;
* Álbum;
* Data de lançamento.

#### Rotas

```http
GET /spotify/connect
GET /spotify/callback
POST /spotify/sync
GET /spotify/preferences
```

---

### 👥 Grupos

Responsável pela criação e gerenciamento dos grupos musicais.

#### Funcionalidades

* Criar grupo;
* Listar grupos;
* Editar grupo;
* Gerar convite;
* Entrar por convite;
* Listar membros;
* Remover membros;
* Definir contexto do grupo.

#### Exemplos de contexto

* Viagem;
* Festa;
* Estudo;
* Treino;
* Churrasco.

#### Rotas

```http
POST /groups
GET /groups
GET /groups/{group_id}
PUT /groups/{group_id}
POST /groups/{group_id}/invite
POST /groups/join/{invite_code}
DELETE /groups/{group_id}/members/{user_id}
```

---

### 📊 Compatibilidade Musical

Responsável por calcular a afinidade musical entre usuários.

#### Dados utilizados

* Artistas favoritos;
* Músicas favoritas;
* Gêneros favoritos.

#### Exemplo

```text
Usuário A: Arctic Monkeys, The Strokes, Coldplay
Usuário B: Arctic Monkeys, Coldplay, Imagine Dragons
```

Artistas em comum:

```text
Arctic Monkeys, Coldplay
```

Similaridade:

```text
itens_em_comum / itens_totais_unicos
```

#### Fórmula sugerida

```text
Compatibilidade =
40% artistas em comum
+ 35% gêneros em comum
+ 25% músicas em comum
```

#### Exemplo

```text
Artistas: 70%
Gêneros: 80%
Músicas: 40%

Compatibilidade = 66%
```

#### Compatibilidade em grupo

```text
Micael x João = 80%
Micael x Ana = 60%
João x Ana = 70%

Compatibilidade do grupo = 70%
```

#### Rotas

```http
GET /groups/{group_id}/compatibility
GET /groups/{group_id}/compatibility/members
```

---

### 🎶 Recomendação Musical

Responsável por gerar playlists de consenso.

#### Objetivo

Selecionar músicas com maior probabilidade de agradar ao grupo.

#### Fórmula sugerida

```text
Score da música =
50% aceitação do grupo
+ 30% afinidade com gêneros do grupo
+ 20% popularidade
```

#### Exemplo

```text
Música X

Aceitação do grupo: 80%
Afinidade com gêneros: 70%
Popularidade: 90%

Score = 0.5*80 + 0.3*70 + 0.2*90
Score = 79%
```

#### Rotas

```http
POST /groups/{group_id}/recommendations
GET /groups/{group_id}/playlist
```

---

### 📈 Dashboard

Responsável pela visualização dos resultados.

#### Funcionalidades

* Compatibilidade geral do grupo;
* Compatibilidade entre membros;
* Artistas em comum;
* Gêneros predominantes;
* Músicas recomendadas;
* Explicação das recomendações;
* Playlist final.

#### Componentes sugeridos

* Card de compatibilidade;
* Ranking de membros;
* Lista de artistas em comum;
* Lista de gêneros;
* Playlist recomendada;
* Justificativas das recomendações.

---

## 🗄️ Banco de Dados

### Tabelas iniciais

```text
users
spotify_accounts
groups
group_members
group_invites
artists
tracks
genres
user_artists
user_tracks
user_genres
group_compatibility
group_playlists
playlist_tracks
```

### Descrição

| Tabela              | Descrição                       |
| ------------------- | ------------------------------- |
| users               | Dados dos usuários              |
| spotify_accounts    | Vínculo com Spotify             |
| groups              | Grupos criados                  |
| group_members       | Relação usuário-grupo           |
| group_invites       | Convites para grupos            |
| artists             | Artistas importados             |
| tracks              | Músicas importadas              |
| genres              | Gêneros musicais                |
| user_artists        | Artistas favoritos dos usuários |
| user_tracks         | Músicas favoritas dos usuários  |
| user_genres         | Gêneros predominantes           |
| group_compatibility | Resultados de compatibilidade   |
| group_playlists     | Playlists geradas               |
| playlist_tracks     | Relação playlist-música         |

---

## 🛠️ Tecnologias Sugeridas

### Frontend

```text
React ou Next.js
```

Responsável por:

* Interfaces;
* Formulários;
* Dashboard;
* Consumo da API.

### Backend

```text
Python + FastAPI
```

Responsável por:

* Autenticação;
* Regras de negócio;
* Integração Spotify;
* Compatibilidade;
* Recomendação.

### Banco de Dados

```text
PostgreSQL
```

### Versionamento

```text
Git + GitHub
```

## 🚀 MVP

### Funcionalidades obrigatórias

* Cadastro e login;
* Integração Spotify;
* Importação de artistas, músicas e gêneros;
* Criação de grupos;
* Entrada em grupos;
* Compatibilidade musical;
* Playlist de consenso;
* Dashboard simples.

### Fora do MVP

* PLN;
* Análise de letras;
* Embeddings;
* Machine Learning;
* Recomendação híbrida avançada.

---

## 📌 Backlog Futuro

### Análise de Letras com PLN

Objetivos:

* Identificar temas;
* Identificar sentimentos;
* Melhorar explicações das recomendações.

Exemplos:

```text
nostalgia
relacionamento
superação
amizade
melancolia
festa
```

### Compatibilidade Temática

Comparar usuários através dos temas presentes nas letras das músicas favoritas.

### Embeddings Musicais

Representar músicas e usuários como vetores para cálculo de similaridade.

### Aprendizado por Feedback

Utilizar:

* Curtidas;
* Rejeições;
* Músicas puladas;
* Músicas salvas.

### Sistema de Recomendação Híbrida

Combinar:

* Artistas;
* Gêneros;
* Histórico;
* Letras;
* Temas;
* Feedback;
* Comportamento do grupo.


## ✅ Critérios de Aceitação

O sistema será considerado funcional quando:

* Usuários conseguirem se cadastrar e autenticar;
* Spotify puder ser conectado;
* Dados musicais forem importados corretamente;
* Grupos puderem ser criados;
* Usuários puderem entrar em grupos;
* Compatibilidade puder ser calculada;
* Playlists forem geradas;
* Dashboard apresentar os resultados.

---

## 📌 Observações Importantes

* A autenticação deve ser própria da plataforma.
* O Spotify deve ser tratado apenas como fonte externa de dados.
* O MVP deve ser simples, explicável e implementável.
* Recursos de IA e PLN ficam para versões futuras.
* As recomendações precisam ser justificáveis e coerentes com os dados disponíveis.

---

## 🎯 Resumo

O projeto consiste em uma plataforma web onde usuários:

1. Criam uma conta;
2. Conectam o Spotify;
3. Participam de grupos;
4. Compartilham preferências musicais;
5. Recebem recomendações coletivas.

### Diferenciais

* Foco em recomendação musical para grupos;
* Compatibilidade musical entre usuários;
* Playlists de consenso;
* Explicações transparentes das recomendações.

### Prioridades da Primeira Versão

* ✅ Autenticação própria;
* ✅ Integração Spotify;
* ✅ Grupos;
* ✅ Compatibilidade;
* ✅ Playlist consenso;
* ✅ Dashboard explicativo.

