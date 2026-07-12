import { useEffect, useState } from 'react'
import { api } from './apiClient'

// Tela de fundação (PB-01): verifica a conectividade frontend -> backend -> DB.
// Não implementa login, salas, motor, etc. (histórias futuras).
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

export default function App() {
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
      <p className="subtitle">Fundação técnica (PB-01)</p>

      <section className="card">
        <h2>Status do ambiente</h2>
        <StatusRow label="Frontend (Vite)" state="ok" />
        <StatusRow label="Backend (FastAPI)" state={backend} />
        <StatusRow label="Banco (PostgreSQL)" state={database} />
        <p className="hint">API base: {api.baseUrl}</p>
      </section>
    </main>
  )
}
