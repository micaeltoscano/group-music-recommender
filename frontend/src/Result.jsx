import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from './apiClient'

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

function phaseAt(index, total) {
  if (index === 0) return 'AQUECIMENTO'
  if (index === Math.max(1, Math.floor(total * 0.34))) return 'PICO'
  if (index === Math.max(2, Math.floor(total * 0.72))) return 'FECHAMENTO'
  return null
}

function gradeFor(score) {
  if (score >= 95) return 'A+'
  if (score >= 85) return 'A−'
  if (score >= 75) return 'B+'
  if (score >= 65) return 'B'
  return 'C'
}

export function Result() {
  const { code } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [whyOpen, setWhyOpen] = useState(true)

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const response = await api.getRoomResult(code)
        if (!active) return
        if (response.ok) {
          setResult(response.body)
          setError(null)
        } else {
          setError(response.body?.detail || 'Erro ao carregar resultados.')
        }
      } catch {
        if (active) setError('Conexão perdida ao carregar o resultado.')
      } finally {
        if (active) setLoading(false)
      }
    }

    load()
    return () => { active = false }
  }, [code])

  const minimumRepresentation = useMemo(() => {
    if (!result?.representation?.length) return 0
    return Math.min(...result.representation.map((member) => member.percentage))
  }, [result])

  const returnToRoom = () => {
    navigate(`/rooms/${code}`, {
      state: { stayForRunId: String(result?.run_id || '') },
    })
  }

  if (loading || error) {
    return (
      <main className="result-shell">
        <header className="product-header">
          <div className="product-brand">
            <EqualizerMark />
            <div>
              <strong>VIBE CHECK</strong>
              <span>NEGOCIE. VOTE. CURTA JUNTO.</span>
            </div>
          </div>
          <span className="room-header-code pill">SALA <strong>{code?.toUpperCase()}</strong></span>
          <span className="eyebrow">VC-01 · GROUP PLAYLIST SYSTEM</span>
        </header>
        <section className={`result-state ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}>
          <p>{error || 'CARREGANDO RESULTADO…'}</p>
          {error && <button className="btn btn-outline" onClick={returnToRoom}>VOLTAR PARA SALA</button>}
        </section>
      </main>
    )
  }

  const {
    playlist_url: playlistUrl,
    compatibility_score: compatibilityScore,
    fairness_score: fairnessScore,
    discovery_percentage: discoveryPercentage,
    representation,
    tracks,
    why_items: whyItems,
  } = result
  const grade = gradeFor(fairnessScore)
  const metrics = [
    { label: 'SATISFAÇÃO DO GRUPO', value: `${compatibilityScore}%`, note: 'afinidade compartilhada' },
    { label: 'REPRESENTAÇÃO MÍNIMA', value: `${minimumRepresentation}%`, note: 'ninguém fica invisível' },
    { label: 'DESCOBERTAS', value: `${discoveryPercentage}%`, note: 'faixas fora dos Tops' },
    { label: 'JUSTIÇA DO GRUPO', value: `${fairnessScore}%`, note: 'distribuição equilibrada' },
  ]

  return (
    <main className="result-shell">
      <header className="product-header">
        <div className="product-brand">
          <EqualizerMark />
          <div>
            <strong>VIBE CHECK</strong>
            <span>NEGOCIE. VOTE. CURTA JUNTO.</span>
          </div>
        </div>
        <span className="room-header-code pill">
          <i aria-hidden="true" /> SALA <strong>{code?.toUpperCase()}</strong>
        </span>
        <span className="eyebrow">VC-01 · GROUP PLAYLIST SYSTEM</span>
      </header>

      <section className="result-content">
        <button className="result-back-link" type="button" onClick={returnToRoom}>
          ← VOLTAR PARA SALA
        </button>

        <div className="result-hero">
          <div className="result-grade" aria-label={`Nota de justiça ${grade}`}>{grade}</div>
          <div className="result-hero-copy">
            <h1>ÓTIMO VIBE!</h1>
            <p>Grupo alinhado. Playlist criada no Spotify com contexto e justiça.</p>
          </div>
          <div className="result-actions">
            <button
              className="result-feedback-button"
              type="button"
              onClick={() => navigate(`/rooms/${code}/feedback`)}
            >
              DAR FEEDBACK
            </button>
            {playlistUrl && (
              <a className="result-spotify-button" href={playlistUrl} target="_blank" rel="noreferrer">
                ABRIR NO SPOTIFY <span aria-hidden="true">▶</span>
              </a>
            )}
          </div>
        </div>

        <div className="result-metrics" aria-label="Métricas da playlist">
          {metrics.map((metric) => (
            <article className="result-metric-card" key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.note}</small>
            </article>
          ))}
        </div>

        <div className="result-grid">
          <section className="result-playlist-card">
            <div className="result-section-heading">
              <span>PLAYLIST FINAL · {tracks.length} FAIXAS</span>
              <strong>SEQUENCIADA POR FLUXO</strong>
            </div>
            <div className="result-track-list">
              {tracks.map((track, index) => {
                const phase = phaseAt(index, tracks.length)
                const contributors = track.contributed_by.length > 0
                  ? track.contributed_by.join(', ')
                  : 'descoberta contextual'
                return (
                  <div key={`${track.track_id || track.name}-${index}`}>
                    {phase && <p className="result-phase">▙ {phase}</p>}
                    <article className="result-track">
                      <span className="result-track-number">{String(index + 1).padStart(2, '0')}</span>
                      <span className={`result-track-art art-${(index % 4) + 1}`} aria-hidden="true" />
                      <div className="result-track-copy">
                        <strong>{track.name}</strong>
                        <span>{track.artist} · via {contributors}</span>
                      </div>
                      <p>{track.reason}</p>
                      <span className={track.is_bridge ? 'result-track-tag bridge' : 'result-track-tag'}>
                        {track.is_bridge ? 'PONTE' : 'SELECIONADA'}
                      </span>
                    </article>
                  </div>
                )
              })}
            </div>
          </section>

          <aside className="result-sidebar">
            <section className="result-side-card">
              <h2>REPRESENTAÇÃO POR MEMBRO</h2>
              <div className="result-representation-list">
                {representation.map((member, index) => (
                  <div className={`result-representation member-color-${(index % 5) + 1}`} key={member.user_id}>
                    <div>
                      <span>{member.display_name || 'Integrante'}</span>
                      <strong>{member.percentage}%</strong>
                    </div>
                    <span className="result-representation-track">
                      <i style={{ width: `${member.percentage}%` }} />
                    </span>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-side-card result-why-card">
              <button type="button" onClick={() => setWhyOpen((open) => !open)} aria-expanded={whyOpen}>
                <span>POR QUE ESSA PLAYLIST É JUSTA?</span>
                <strong>{whyOpen ? '−' : '+'}</strong>
              </button>
              {whyOpen && (
                <ul>
                  {(whyItems || []).map((item) => <li key={item}>{item}</li>)}
                </ul>
              )}
            </section>

            <button className="result-return-button" type="button" onClick={returnToRoom}>
              <span aria-hidden="true">↻</span> VOLTAR PARA SALA
            </button>
          </aside>
        </div>
      </section>
    </main>
  )
}
