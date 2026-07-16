import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from './apiClient'

const POLLING_INTERVAL_MS = 4000
const OCCASIONS = ['Pré-jogo no apê', 'Festa', 'Churrasco', 'Viagem', 'Estudo', 'Academia']
const CONSENSUS_MODES = [
  { name: 'Democrático', description: 'todo mundo com o mesmo peso' },
  { name: 'Festa Segura', description: 'hits conhecidos, baixa rejeição' },
]

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
  const [contextDraft, setContextDraft] = useState({ occasion: '', description: '' })
  const [contextDirty, setContextDirty] = useState(false)
  const [savingContext, setSavingContext] = useState(false)
  const [savingMode, setSavingMode] = useState(false)
  const [settingsFeedback, setSettingsFeedback] = useState(null)

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
  const isHost = currentMember?.role === 'host'

  useEffect(() => {
    if (!room || contextDirty) return
    setContextDraft({
      occasion: room.occasion || '',
      description: room.description || '',
    })
  }, [room?.occasion, room?.description, contextDirty])

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(room.code)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopied(false)
    }
  }

  const selectOccasion = (occasion) => {
    if (!isHost) return
    setContextDraft((current) => ({ ...current, occasion }))
    setContextDirty(true)
    setSettingsFeedback(null)
  }

  const changeDescription = (event) => {
    setContextDraft((current) => ({ ...current, description: event.target.value }))
    setContextDirty(true)
    setSettingsFeedback(null)
  }

  const saveContext = async (event) => {
    event.preventDefault()
    if (!isHost || savingContext) return

    const payload = {
      occasion: contextDraft.occasion.trim() || null,
      description: contextDraft.description.trim() || null,
    }
    if (!payload.occasion && !payload.description) {
      setSettingsFeedback({ type: 'error', message: 'Escolha uma ocasião ou descreva a vibe.' })
      return
    }

    setSavingContext(true)
    setSettingsFeedback(null)
    try {
      const response = await api.updateRoomContext(code, payload)
      if (!response.ok) {
        setSettingsFeedback({
          type: 'error',
          message: response.body?.detail || 'Não foi possível salvar o contexto.',
        })
        return
      }
      setRoom(response.body)
      setContextDraft({
        occasion: response.body.occasion || '',
        description: response.body.description || '',
      })
      setContextDirty(false)
      setSettingsFeedback({ type: 'success', message: 'Contexto salvo para todo o grupo.' })
    } catch {
      setSettingsFeedback({ type: 'error', message: 'Conexão perdida ao salvar o contexto.' })
    } finally {
      setSavingContext(false)
    }
  }

  const saveMode = async (mode) => {
    if (!isHost || savingMode || room.mode === mode) return
    setSavingMode(true)
    setSettingsFeedback(null)
    try {
      const response = await api.updateRoomMode(code, mode)
      if (!response.ok) {
        setSettingsFeedback({
          type: 'error',
          message: response.body?.detail || 'Não foi possível salvar o modo.',
        })
        return
      }
      setRoom(response.body)
      setSettingsFeedback({ type: 'success', message: `Modo ${mode} selecionado.` })
    } catch {
      setSettingsFeedback({ type: 'error', message: 'Conexão perdida ao salvar o modo.' })
    } finally {
      setSavingMode(false)
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

            <div className="room-settings-column">
              <section className="room-setting-card context-card">
                <div className="setting-heading-row">
                  <span>OCASIÃO</span>
                  <small>{isHost ? 'VOCÊ CONTROLA' : 'DEFINIDO PELO HOST'}</small>
                </div>
                <form onSubmit={saveContext}>
                  <div className="occasion-options" aria-label="Ocasião da sala">
                    {OCCASIONS.map((occasion) => (
                      <button
                        className={contextDraft.occasion === occasion ? 'occasion-chip selected' : 'occasion-chip'}
                        type="button"
                        key={occasion}
                        disabled={!isHost || savingContext}
                        aria-pressed={contextDraft.occasion === occasion}
                        onClick={() => selectOccasion(occasion)}
                      >
                        {occasion}
                      </button>
                    ))}
                  </div>
                  <label className="context-description-label">
                    <span className="eyebrow">DESCRIÇÃO LIVRE</span>
                    <input
                      type="text"
                      value={contextDraft.description}
                      maxLength={1000}
                      readOnly={!isHost}
                      disabled={savingContext}
                      onChange={changeDescription}
                      placeholder="Descreva a vibe: 'pré-jogo no apê, clima descontraído…'"
                    />
                  </label>
                  {isHost && (
                    <button
                      className="save-context-button"
                      type="submit"
                      disabled={savingContext || !contextDirty}
                    >
                      <span>{savingContext ? 'SALVANDO…' : contextDirty ? 'SALVAR CONTEXTO' : 'CONTEXTO SALVO'}</span>
                      <span aria-hidden="true">{contextDirty ? '▶' : '✓'}</span>
                    </button>
                  )}
                </form>
              </section>

              <section className="room-setting-card mode-card">
                <div className="setting-heading-row">
                  <span>MODO DE CONSENSO</span>
                  {savingMode && <small>SALVANDO…</small>}
                </div>
                <div className="mode-options">
                  {CONSENSUS_MODES.map((mode) => (
                    <button
                      className={room.mode === mode.name ? 'mode-option selected' : 'mode-option'}
                      type="button"
                      key={mode.name}
                      disabled={!isHost || savingMode}
                      aria-pressed={room.mode === mode.name}
                      onClick={() => saveMode(mode.name)}
                    >
                      <strong>{mode.name}</strong>
                      <span>{mode.description}</span>
                    </button>
                  ))}
                </div>
              </section>

              {settingsFeedback && (
                <p
                  className={`settings-feedback ${settingsFeedback.type}`}
                  role={settingsFeedback.type === 'error' ? 'alert' : 'status'}
                >
                  {settingsFeedback.message}
                </p>
              )}

              <div className="polling-status compact" role={error ? 'alert' : 'status'}>
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
            </div>
          </div>
        )}
      </section>
    </main>
  )
}
