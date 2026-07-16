import { useState } from 'react'
import { api } from './apiClient'

function userInitials(name) {
  const parts = (name || 'Usuário').trim().split(/\s+/).filter(Boolean)
  return parts.slice(0, 2).map((part) => part[0]).join('').toUpperCase()
}

function EqualizerMark() {
  return (
    <span className="equalizer-mark" aria-hidden="true">
      <i />
      <i />
      <i />
      <i />
    </span>
  )
}

export default function Home({ user }) {
  const [room, setRoom] = useState(null)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  const createRoom = async () => {
    setCreating(true)
    setError('')
    try {
      const response = await api.createRoom()
      if (!response.ok) {
        setError(response.body?.detail || 'Não foi possível criar a sala. Tente novamente.')
        return
      }
      setRoom(response.body)
    } catch {
      setError('O backend não respondeu. Verifique sua conexão e tente novamente.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <main className="home-shell">
      <header className="product-header">
        <div className="product-brand">
          <EqualizerMark />
          <div>
            <strong>VIBE CHECK</strong>
            <span>NEGOCIE. VOTE. CURTA JUNTO.</span>
          </div>
        </div>
        <span className="eyebrow">VC-01 · GROUP PLAYLIST SYSTEM</span>
      </header>

      <section className="home-content">
        <div className="greeting-row">
          {user?.image_url ? (
            <img className="user-avatar" src={user.image_url} alt="" />
          ) : (
            <span className="user-avatar user-initials">{userInitials(user?.display_name)}</span>
          )}
          <div>
            <h1>Bom te ver, {user?.display_name || 'Usuário'}.</h1>
            <p>Conectado via Spotify · pronto para criar uma sessão</p>
          </div>
        </div>

        <section className="create-room-card" aria-labelledby="create-room-title">
          <p className="card-kicker">01 · CRIAR SALA</p>
          <h2 id="create-room-title">Comece uma sessão para o seu grupo</h2>
          <p className="card-copy">
            Você será o host: compartilhe o código e reúna o grupo. A sessão expira
            automaticamente em 24h.
          </p>

          {room ? (
            <div className="room-created" role="status" aria-live="polite">
              <span>SALA CRIADA · CÓDIGO</span>
              <strong>{room.code}</strong>
              <small>Você já está registrado como host.</small>
            </div>
          ) : (
            <button
              className="btn btn-primary create-room-button"
              type="button"
              onClick={createRoom}
              disabled={creating}
            >
              <span>{creating ? 'CRIANDO SALA…' : 'CRIAR SALA'}</span>
              <span aria-hidden="true">▶</span>
            </button>
          )}

          {error && <p className="form-error" role="alert">{error}</p>}
        </section>
      </section>
    </main>
  )
}
