import { useEffect, useState } from 'react'
import { api } from './apiClient'

function StatusRow({ label, state }) {
  const color = state === 'ok' ? '#1db954' : state === 'erro' ? '#e22134' : '#888'
  return (
    <div className="status-row">
      <span className="status-dot" style={{ backgroundColor: color }} />
      <span className="status-label">{label}</span>
      <span className="status-value">{state}</span>
    </div>
  )
}

export default function Home({ user }) {
  const [backend, setBackend] = useState('verificando…')
  const [database, setDatabase] = useState('verificando…')

  useEffect(() => {
    api
      .health()
      .then((r) => setBackend(r.ok ? 'ok' : 'erro'))
      .catch(() => setBackend('erro'))

    api
      .healthDb()
      .then((r) => setDatabase(r.ok ? 'ok' : 'erro'))
      .catch(() => setDatabase('erro'))
  }, [])

  return (
    <main className="app">
      <h1>Vibe Check</h1>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', marginBottom: '2rem' }}>
        {user?.image_url && (
          <img 
            src={user.image_url} 
            alt="Perfil" 
            style={{ width: '64px', height: '64px', borderRadius: '50%', objectFit: 'cover' }} 
          />
        )}
        <p className="subtitle" style={{ margin: 0 }}>Olá, {user?.display_name || 'Usuário'}!</p>
      </div>

      <section className="card">
        <h2>Status do ambiente (PB-01)</h2>
        <StatusRow label="Frontend (Vite)" state="ok" />
        <StatusRow label="Backend (FastAPI)" state={backend} />
        <StatusRow label="Banco (PostgreSQL)" state={database} />
        <p className="hint">API base: {api.baseUrl}</p>
      </section>
    </main>
  )
}
