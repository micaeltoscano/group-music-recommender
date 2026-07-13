import { api } from './apiClient'

export default function Login() {
  const handleLogin = () => {
    window.location.href = `${api.baseUrl}/auth/login`
  }

  return (
    <main className="app">
      <h1>Vibe Check</h1>
      <p className="subtitle">Sua playlist, do jeito de todo mundo.</p>

      <section className="card" style={{ textAlign: 'center', padding: '2rem' }}>
        <h2>Bem-vindo(a)</h2>
        <p>Faça login para criar salas ou participar do Vibe Check.</p>
        <button 
          onClick={handleLogin}
          style={{
            marginTop: '1.5rem',
            padding: '12px 24px',
            backgroundColor: '#1db954',
            color: '#fff',
            border: 'none',
            borderRadius: '24px',
            fontSize: '1rem',
            fontWeight: 'bold',
            cursor: 'pointer'
          }}
        >
          Entrar com Spotify
        </button>
      </section>
    </main>
  )
}
