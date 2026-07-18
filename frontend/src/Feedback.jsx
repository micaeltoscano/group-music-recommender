import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from './apiClient'

const EMPTY_TRACK_FEEDBACK = {
  liked: false,
  disliked: false,
  more_like_this: false,
  never_again: false,
}

const TRACK_ACTIONS = [
  { key: 'liked', label: 'CURTI', glyph: '+' },
  { key: 'disliked', label: 'NÃO CURTI', glyph: '−' },
  { key: 'more_like_this', label: 'MAIS ASSIM', glyph: '↗' },
  { key: 'never_again', label: 'NUNCA MAIS', glyph: '×' },
]

function ScoreScale({ label, value, onChange }) {
  return (
    <fieldset className="feedback-scale">
      <legend>{label}</legend>
      <div className="feedback-scale-options">
        {[0, 1, 2, 3, 4, 5].map((score) => (
          <button
            key={score}
            type="button"
            className={value === score ? 'selected' : ''}
            aria-pressed={value === score}
            onClick={() => onChange(score)}
          >
            {score}
          </button>
        ))}
      </div>
      <div className="feedback-scale-labels">
        <span>NADA</span>
        <span>MUITO</span>
      </div>
    </fieldset>
  )
}

export function Feedback({ user }) {
  const { code } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [trackFeedback, setTrackFeedback] = useState({})
  const [representation, setRepresentation] = useState(null)
  const [satisfaction, setSatisfaction] = useState(null)
  const [comments, setComments] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    api.getRoomResult(code).then((response) => {
      if (!active) return
      if (response.ok) setResult(response.body)
      else setError(response.body?.detail || 'Não foi possível carregar a playlist.')
      setLoading(false)
    })
    return () => { active = false }
  }, [code])

  const answeredTracks = useMemo(
    () => Object.values(trackFeedback).filter((item) => Object.values(item).some(Boolean)).length,
    [trackFeedback],
  )

  function toggleTrack(trackId, key) {
    setTrackFeedback((current) => {
      const item = current[trackId] || EMPTY_TRACK_FEEDBACK
      return { ...current, [trackId]: { ...item, [key]: !item[key] } }
    })
  }

  async function submit(event) {
    event.preventDefault()
    if (representation === null || satisfaction === null) {
      setError('Escolha as notas de representação e satisfação antes de enviar.')
      return
    }

    setSending(true)
    setError(null)
    const trackRequests = Object.entries(trackFeedback)
      .map(([trackId, feedback]) => api.submitTrackFeedback(result.run_id, trackId, feedback))

    const responses = await Promise.all([
      ...trackRequests,
      api.submitPlaylistFeedback(result.run_id, {
        representation_score: representation,
        satisfaction_score: satisfaction,
        comments: comments.trim() || null,
      }),
    ])
    const failed = responses.find((response) => !response.ok)
    if (failed) {
      setError(failed.body?.detail || 'Não foi possível enviar todo o feedback. Tente novamente.')
      setSending(false)
      return
    }
    setSent(true)
    setSending(false)
  }

  if (loading) {
    return <main className="feedback-shell feedback-centered">CARREGANDO FEEDBACK...</main>
  }

  if (!result) {
    return (
      <main className="feedback-shell feedback-centered">
        <section className="feedback-state-card">
          <p>{error}</p>
          <button className="btn btn-outline" onClick={() => navigate(`/rooms/${code}/result`)}>
            VOLTAR AO RESULTADO
          </button>
        </section>
      </main>
    )
  }

  if (sent) {
    return (
      <main className="feedback-shell feedback-centered">
        <section className="feedback-state-card feedback-success-card">
          <div className="feedback-success-mark" aria-hidden="true">✓</div>
          <p className="eyebrow">[ VC-01 · FEEDBACK RECEBIDO ]</p>
          <h1>Valeu, {user?.display_name || 'integrante'}!</h1>
          <p>
            Seu feedback será usado em evoluções futuras do Vibe Check e não altera o ranking do MVP.
          </p>
          <button className="btn btn-primary" onClick={() => navigate(`/rooms/${code}/result`)}>
            VOLTAR AO RESULTADO <span>▶</span>
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="feedback-shell">
      <form className="feedback-card" onSubmit={submit}>
        <header className="feedback-heading">
          <p className="eyebrow">[ VC-01 · FEEDBACK MODULE ]</p>
          <button type="button" onClick={() => navigate(`/rooms/${code}/result`)}>
            FECHAR ×
          </button>
          <h1>Como foi a playlist?</h1>
          <p>
            Marque faixa a faixa. O feedback será usado em evoluções futuras e ainda não altera o
            ranking do MVP.
          </p>
        </header>

        <section className="feedback-section">
          <div className="feedback-section-title">
            <span>FAIXA A FAIXA</span>
            <small>{answeredTracks}/{result.tracks.length} AVALIADAS</small>
          </div>
          <div className="feedback-track-list">
            {result.tracks.map((track, index) => (
              <article className="feedback-track" key={track.track_id || `${track.name}-${index}`}>
                <span className="feedback-track-number">{String(index + 1).padStart(2, '0')}</span>
                <div className="feedback-track-art" aria-hidden="true" />
                <div className="feedback-track-copy">
                  <strong>{track.name}</strong>
                  <span>{track.artist}</span>
                </div>
                <div className="feedback-track-actions">
                  {TRACK_ACTIONS.map((action) => {
                    const active = Boolean(trackFeedback[track.track_id]?.[action.key])
                    return (
                      <button
                        key={action.key}
                        type="button"
                        disabled={!track.track_id}
                        className={active ? 'selected' : ''}
                        aria-pressed={active}
                        onClick={() => toggleTrack(track.track_id, action.key)}
                      >
                        <span>{action.glyph}</span>{action.label}
                      </button>
                    )
                  })}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="feedback-section feedback-overall">
          <div className="feedback-section-title"><span>SUA EXPERIÊNCIA</span></div>
          <div className="feedback-score-grid">
            <ScoreScale
              label="A playlist te representou?"
              value={representation}
              onChange={setRepresentation}
            />
            <ScoreScale
              label="Qual foi sua satisfação?"
              value={satisfaction}
              onChange={setSatisfaction}
            />
          </div>
          <label className="feedback-comment">
            <span>QUER CONTAR MAIS? <small>(OPCIONAL)</small></span>
            <textarea
              value={comments}
              maxLength={2000}
              onChange={(event) => setComments(event.target.value)}
              placeholder="O que funcionou — e o que você mudaria?"
            />
          </label>
        </section>

        {error && <p className="feedback-error" role="alert">{error}</p>}
        <button className="feedback-submit" type="submit" disabled={sending}>
          <span>{sending ? 'ENVIANDO...' : 'ENVIAR FEEDBACK'}</span>
          <span>▶</span>
        </button>
      </form>
    </main>
  )
}
