# 01 — Autenticação via Spotify OAuth

![Autenticação via Spotify OAuth](01-autenticacao-spotify.png)

```mermaid
%%{init: {'sequence': {'mirrorActors': false}}}%%
sequenceDiagram
    actor Membro as Membro da Sala
    participant Frontend as Frontend (React)
    participant API as API (auth.py)
    participant Spotify as Spotify
    participant DB as Banco (User, SpotifyToken, AppSession)

    Membro->>Frontend: 1: clica "Entrar com Spotify"
    Frontend->>API: 1.1: GET /auth/login
    API->>API: 1.1.1: gera state (secrets.token_urlsafe)
    API-->>Frontend: 302 Redirect + Set-Cookie(spotify_auth_state, httpOnly)
    Frontend->>Spotify: 1.2: redireciona para autorização OAuth
    Membro->>Spotify: 2: autoriza acesso (login + consentimento)
    Spotify-->>API: GET /auth/callback?code&state

    alt state ausente ou diferente do cookie
        API-->>Frontend: 400 "State inválido ou ausente"
    else code ausente ou error=acesso negado
        API-->>Frontend: 400 "Autorização Spotify negada"
    else state válido
        API->>Spotify: 2.1: exchange_code_for_token(code)
        Spotify-->>API: access_token, refresh_token, expires_in
        API->>Spotify: 2.2: get_current_user_profile(access_token)
        Spotify-->>API: perfil {id, display_name, images}
        API->>DB: 2.3: SELECT User WHERE spotify_id
        alt usuário novo
            API->>DB: 2.4: INSERT User
        else usuário existente
            API->>DB: 2.5: UPDATE User (display_name, image_url)
        end
        API->>API: 2.6: crypto.encrypt(access_token, refresh_token)
        API->>DB: 2.7: UPSERT SpotifyToken (tokens cifrados, token_expires_at)
        API->>DB: 2.8: CREATE AppSession (session_token_hash, expires_at = +30d)
        API-->>Frontend: 302 Redirect + Set-Cookie(vibe_session, httpOnly)
    end

    Frontend->>API: 3: GET /auth/me (cookie vibe_session)
    API->>DB: 3.1: SELECT AppSession WHERE session_token_hash
    alt sessão inexistente ou expirada
        API-->>Frontend: 401 "Sessão inválida ou expirada"
    else sessão válida
        API->>DB: 3.2: SELECT User WHERE id
        API-->>Frontend: 200 {id, spotify_id, display_name, image_url}
    end
```

Este fluxo cobre RF-01 e é pré-requisito técnico de todo o resto do sistema — nenhum outro caso de
uso é alcançável sem uma `AppSession` válida. Foi escolhido por concentrar as três garantias de
segurança mais sensíveis do backlog (RNF-01): validação do parâmetro `state` contra CSRF, tokens
Spotify cifrados em repouso (`crypto.encrypt`) e o fato de que `access_token`/`refresh_token` nunca
saem do backend — só o `vibe_session` (hash de sessão da aplicação) chega ao navegador. O bloco `alt`
duplo no callback reflete exatamente os três desvios tratados em `auth.py` (state inválido, consentimento
negado, sucesso), e o segundo bloco `alt` mostra que `/auth/me` é a fonte única de verdade sobre a
sessão para o restante do frontend (`App.jsx` decide as rotas a partir dela).
