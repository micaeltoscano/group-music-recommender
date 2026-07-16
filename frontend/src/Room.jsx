import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from './apiClient'

const POLLING_INTERVAL_MS = 4000

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

function userInitials(name) {
  const parts = (name || 'Usuário').trim().split(/\s+/).filter(Boolean)
  return parts.slice(0, 2).map((part) => part[0]).join('').toUpperCase()
}

function formatRemaining(expiresAt, now) {
  const remaining = Math.max(0, new Date(expiresAt).getTime() - now)
  if (remaining === 0) return 'EXPIRADA'
  const hours = Math.floor(remaining / 3_600_000)
  const minutes = Math.floor((remaining % 3_600_000) / 60_000)
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

export default function Room({ user }) {
  const { code } = useParams()
  const [room, setRoom] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [now, setNow] = useState(Date.now())
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    let active = true

    const pollRoom = async () => {
      try {
        const response = await api.getRoom(code)
        if (!active) return
        if (!response.ok) {
          setError(response.body?.detail || 'Não foi possível atualizar a sala.')
          return
        }
        setRoom(response.body)
        setError('')
        setLastUpdated(new Date())
      } catch {
        if (active) setError('Conexão perdida. Tentaremos atualizar novamente em instantes.')
      } finally {
        if (active) setLoading(false)
      }
    }

    pollRoom()
    const pollingId = window.setInterval(pollRoom, POLLING_INTERVAL_MS)
    return () => {
      active = false
      window.clearInterval(pollingId)
    }
  }, [code])

  useEffect(() => {
    const clockId = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(clockId)
  }, [])

  const currentMember = useMemo(
    () => room?.members.find((member) => member.user_id === user?.id),
    [room, user],
  )

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(room.code)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopied(false)
    }
  }

  return (
    <main className="room-shell">
      <header className="product-header">
        <div className="product-brand">
          <EqualizerMark />
          <div>
            <strong>VIBE CHECK</strong>
            <span>NEGOCIE. VOTE. CURTA JUNTO.</span>
          </div>
        </div>
        <span className="room-header-code pill">
          <i aria-hidden="true" /> SALA <strong>{room?.code || code?.toUpperCase()}</strong>
        </span>
        <span className="eyebrow">VC-01 · GROUP PLAYLIST SYSTEM</span>
      </header>

      <section className="room-content">
        <div className="room-title-row">
          <p className="eyebrow">[ VC-01 · ROOM MODULE ]</p>
          <Link className="room-back-link" to="/">← VOLTAR AO INÍCIO</Link>
        </div>

        {loading && !room && <div className="room-loading">SINCRONIZANDO SALA…</div>}

        {!loading && !room && (
          <section className="room-access-error" role="alert">
            <p className="card-kicker">ACESSO À SALA</p>
            <h1>Não foi possível abrir esta sala.</h1>
            <p>{error}</p>
            <Link className="btn btn-outline" to="/">VOLTAR</Link>
          </section>
        )}

        {room && (
          <div className="room-lobby-grid">
            <div className="room-lobby-column">
              <section className="room-code-card">
                <div className="room-code-meta">
                  <span>SALA ATIVA</span>
                  <span>EXPIRA EM {formatRemaining(room.expires_at, now)}</span>
                </div>
                <strong>{room.code}</strong>
                <button className="copy-code-button" type="button" onClick={copyCode}>
                  {copied ? 'CÓDIGO COPIADO ✓' : 'COPIAR CÓDIGO ⧉'}
                </button>
              </section>

              <section className="members-card" aria-live="polite">
                <div className="members-card-header">
                  <span>MEMBROS ATIVOS</span>
                  <strong>{room.members.length}/5</strong>
                </div>
                <ul className="member-list">
                  {room.members.map((member, index) => (
                    <li key={member.user_id}>
                      {member.image_url ? (
                        <img className="member-avatar" src={member.image_url} alt="" />
                      ) : (
                        <span
                          className="member-avatar member-initials"
                          style={{ '--member-color': `var(--avatar-${(index % 5) + 1})` }}
                        >
                          {userInitials(member.display_name)}
                        </span>
                      )}
                      <span className="member-name">
                        {member.display_name || 'Usuário Spotify'}
                        {member.user_id === user?.id && <small>VOCÊ</small>}
                      </span>
                      {member.role === 'host' && <span className="host-badge">HOST</span>}
                      <span className="online-dot" aria-label="online" />
                    </li>
                  ))}
                </ul>
              </section>
            </div>

            <section className="waiting-card">
              <p className="card-kicker">GRUPO EM FORMAÇÃO</p>
              <h1>{currentMember?.role === 'host' ? 'Compartilhe o código.' : 'Você entrou na sala.'}</h1>
              <p>
                {currentMember?.role === 'host'
                  ? 'Convide até quatro pessoas. A lista ao lado acompanha automaticamente cada entrada.'
                  : 'Aguarde o restante do grupo. Esta tela acompanha automaticamente quem já chegou.'}
              </p>

              <div className="polling-status" role={error ? 'alert' : 'status'}>
                <span className={error ? 'polling-dot polling-dot-error' : 'polling-dot'} />
                <div>
                  <strong>{error ? 'RECONECTANDO' : 'SALA SINCRONIZADA'}</strong>
                  <small>
                    {error || (lastUpdated
                      ? `Atualizada às ${lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} · polling a cada 4s`
                      : 'Primeira atualização em andamento')}
                  </small>
                </div>
              </div>

              <div className="room-capacity-track" aria-label={`${room.members.length} de 5 membros`}>
                {Array.from({ length: 5 }, (_, index) => (
                  <span key={index} className={index < room.members.length ? 'filled' : ''} />
                ))}
              </div>
              <p className="waiting-note">
                O contexto e o modo de consenso serão definidos pelo host na próxima etapa.
              </p>
            </section>
          </div>
        )}
      </section>
    </main>
  )
}
