import { useEffect, useState } from 'react'
import { api } from './apiClient'

const HOW_IT_WORKS = [
  { number: '01', title: 'Crie a sala', copy: 'O host abre uma sessão, define ocasião e modo de consenso.' },
  { number: '02', title: 'Grupo entra', copy: 'Cada pessoa conecta o Spotify e responde o Vibe Check opcional.' },
  { number: '03', title: 'Motor negocia', copy: 'Gosto, contexto, justiça e rejeição são equilibrados por faixa.' },
  { number: '04', title: 'Playlist real', copy: 'O resultado vai ao Spotify do host com explicações agregadas.' },
]

const FEATURES = [
  { symbol: '⚖', title: 'Justiça, não média', copy: 'O motor preserva representação do grupo, não apenas o gosto dominante.' },
  { symbol: '◎', title: 'Contexto de verdade', copy: 'A ocasião e o clima ampliam os Tops com descoberta musical adequada.' },
  { symbol: '◇', title: 'Vetos respeitados', copy: 'Uma rejeição forte não é escondida por uma média aparentemente boa.' },
]

function Equalizer({ dark = false }) {
  return (
    <span className={dark ? 'login-equalizer dark' : 'login-equalizer'} aria-hidden="true">
      <i /><i /><i /><i />
    </span>
  )
}

export default function Login() {
  const [redirecting, setRedirecting] = useState(false)
  const authError = new URLSearchParams(window.location.search).get('error')

  useEffect(() => {
    const restoreButton = () => setRedirecting(false)
    window.addEventListener('pageshow', restoreButton)
    return () => window.removeEventListener('pageshow', restoreButton)
  }, [])

  const handleLogin = () => {
    if (redirecting) return
    setRedirecting(true)
    window.location.assign(`${api.baseUrl}/auth/login`)
  }

  const loginButton = (extraClass = '') => (
    <button
      className={`login-spotify-button ${extraClass}`.trim()}
      type="button"
      onClick={handleLogin}
      disabled={redirecting}
      aria-describedby="login-security"
    >
      <span>{redirecting ? 'ABRINDO SPOTIFY…' : 'ENTRAR COM SPOTIFY'}</span>
      <span aria-hidden="true">▶</span>
    </button>
  )

  return (
    <main className="login-shell">
      <header className="product-header login-header">
        <div className="product-brand">
          <Equalizer />
          <div>
            <strong>VIBE CHECK</strong>
            <span>NEGOCIE. VOTE. CURTA JUNTO.</span>
          </div>
        </div>
        <span className="eyebrow">VC-01 · GROUP PLAYLIST SYSTEM</span>
      </header>

      <section className="login-hero">
        <div className="login-hero-copy">
          <p className="eyebrow">[ VC-01 · GROUP PLAYLIST SYSTEM ]</p>
          <h1>A playlist que <em>representa</em> o grupo inteiro.</h1>
          <p className="login-lead">
            Spotify entende o passado musical. O Vibe Check entende o humor do momento e o grupo —
            e negocia uma playlist única que ninguém odeia e todo mundo curte.
          </p>
          <div className="login-action-row">
            {loginButton()}
            <p id="login-security" className="login-security">
              <span aria-hidden="true">▣</span> Tokens criptografados.<br />Nunca saem do servidor.
            </p>
          </div>
          {authError && (
            <p className="login-error" role="alert">
              Não foi possível concluir a autorização do Spotify. Tente novamente.
            </p>
          )}
        </div>

        <aside className="login-playlist-preview" aria-label="Exemplo de uma sala negociada">
          <Equalizer dark />
          <p className="login-preview-code">SALA · X8F7-9Q2L</p>
          <p className="login-preview-context">“Pré-jogo no apê” · 5 pessoas · modo Democrático</p>
          <div className="login-preview-score">
            <span>SATISFAÇÃO</span><strong>87%</strong>
          </div>
          <div className="login-preview-track"><span /></div>
        </aside>
      </section>

      <div className="login-proof" aria-label="Princípios do produto">
        <span>◉ PLAYLISTS JUSTAS</span>
        <span>◉ TODO MUNDO OUVIDO</span>
        <span>◉ ZERO DRAMA</span>
        <span>◉ FEITO PARA GRUPOS</span>
      </div>

      <section className="login-section" aria-labelledby="how-title">
        <p className="eyebrow">[ COMO FUNCIONA ]</p>
        <h2 id="how-title">Do “quem vai escolher a música?” à playlist, em 4 passos.</h2>
        <div className="login-steps-grid">
          {HOW_IT_WORKS.map((step) => (
            <article key={step.number}>
              <strong>{step.number}</strong>
              <h3>{step.title}</h3>
              <p>{step.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="login-section login-features" aria-label="Diferenciais">
        {FEATURES.map((feature) => (
          <article key={feature.title}>
            <span aria-hidden="true">{feature.symbol}</span>
            <h3>{feature.title}</h3>
            <p>{feature.copy}</p>
          </article>
        ))}
      </section>

      <section className="login-final-cta">
        <h2>Chame o grupo. Deixa o motor negociar.</h2>
        {loginButton('final')}
      </section>
    </main>
  )
}
