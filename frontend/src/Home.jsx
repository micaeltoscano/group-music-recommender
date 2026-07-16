import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
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

function formatRoomCode(value) {
  const raw = value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8)
  return raw.length > 4 ? `${raw.slice(0, 4)}-${raw.slice(4)}` : raw
}

export default function Home({ user }) {
  const navigate = useNavigate()
  const [roomCode, setRoomCode] = useState('')
  const [creating, setCreating] = useState(false)
  const [joining, setJoining] = useState(false)
  const [createError, setCreateError] = useState('')
  const [joinError, setJoinError] = useState('')

  const createRoom = async () => {
    setCreating(true)
    setCreateError('')
    try {
      const response = await api.createRoom()
      if (!response.ok) {
        setCreateError(response.body?.detail || 'Não foi possível criar a sala. Tente novamente.')
        return
      }
      navigate(`/rooms/${response.body.code}`)
    } catch {
      setCreateError('O backend não respondeu. Verifique sua conexão e tente novamente.')
    } finally {
      setCreating(false)
    }
  }

  const joinRoom = async (event) => {
    event.preventDefault()
    if (roomCode.length !== 9) {
      setJoinError('Digite os oito caracteres do código da sala.')
      return
    }

    setJoining(true)
    setJoinError('')
    try {
      const response = await api.joinRoom(roomCode)
      if (!response.ok) {
        setJoinError(response.body?.detail || 'Não foi possível entrar nesta sala.')
        return
      }
      navigate(`/rooms/${response.body.code}`)
    } catch {
      setJoinError('O backend não respondeu. Verifique sua conexão e tente novamente.')
    } finally {
      setJoining(false)
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

        <div className="room-actions-grid">
          <section className="room-action-card" aria-labelledby="create-room-title">
            <p className="card-kicker">01 · CRIAR SALA</p>
            <h2 id="create-room-title">Comece uma sessão para o seu grupo</h2>
            <p className="card-copy">
              Você será o host: compartilhe o código e reúna o grupo. A sessão expira
              automaticamente em 24h.
            </p>

            <button
              className="btn btn-primary create-room-button"
              type="button"
              onClick={createRoom}
              disabled={creating}
            >
              <span>{creating ? 'CRIANDO SALA…' : 'CRIAR SALA'}</span>
              <span aria-hidden="true">▶</span>
            </button>

            {createError && <p className="form-error" role="alert">{createError}</p>}
          </section>

          <section className="room-action-card" aria-labelledby="join-room-title">
            <p className="card-kicker card-kicker-secondary">02 · ENTRAR COM CÓDIGO</p>
            <h2 id="join-room-title">O grupo já começou?</h2>
            <p className="card-copy">
              Digite o código compartilhado pelo host para acompanhar quem já entrou.
            </p>

            <form className="join-room-form" onSubmit={joinRoom}>
              <label htmlFor="room-code">CÓDIGO DA SALA</label>
              <input
                id="room-code"
                value={roomCode}
                onChange={(event) => setRoomCode(formatRoomCode(event.target.value))}
                placeholder="XXXX-XXXX"
                autoComplete="off"
                spellCheck="false"
                inputMode="text"
                maxLength="9"
                aria-describedby={joinError ? 'join-error' : undefined}
              />
              <button
                className="btn btn-outline join-room-button"
                type="submit"
                disabled={joining}
              >
                <span>{joining ? 'ENTRANDO…' : 'ENTRAR NA SALA'}</span>
                <span aria-hidden="true">▶</span>
              </button>
            </form>

            {joinError && <p id="join-error" className="form-error" role="alert">{joinError}</p>}
          </section>
        </div>
      </section>
    </main>
  )
}
