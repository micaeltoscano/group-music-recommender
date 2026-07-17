import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from './apiClient'

export function Result() {
  const { code } = useParams()
  const navigate = useNavigate()

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [whyOpen, setWhyOpen] = useState(false)

  useEffect(() => {
    async function load() {
      const res = await api.getRoomResult(code)
      if (res.ok) {
        setResult(res.body)
      } else {
        setError(res.body?.detail || 'Erro ao carregar resultados.')
      }
      setLoading(false)
    }
    load()
  }, [code])

  if (loading) {
    return (
      <div className="layout-content">
        <div style={{ padding: '72px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Carregando resultado...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="layout-content">
        <div style={{ padding: '72px 24px', textAlign: 'center', color: 'var(--error)' }}>
          {error}
          <div style={{ marginTop: '20px' }}>
            <button className="btn" onClick={() => navigate(`/rooms/${code}`)}>VOLTAR PARA SALA</button>
          </div>
        </div>
      </div>
    )
  }

  const {
    playlist_url,
    compatibility_score,
    fairness_score,
    representation,
    tracks,
    why_items
  } = result

  // Cores dinâmicas para a representação
  const colors = ['#a8ae6d', '#ff5b1c', '#f2ecdb', '#5b5945', '#8b8871']

  const metrics = [
    { label: 'COMPATIBILIDADE', value: `${compatibility_score}%`, note: 'Alinhamento geral' },
    { label: 'FAIRNESS SCORE', value: `${fairness_score}%`, note: 'Justiça na distribuição' },
    { label: 'TAMANHO', value: `${tracks.length}`, note: 'Faixas selecionadas' },
    { label: 'MEMBROS', value: `${representation.length}`, note: 'Representados na playlist' }
  ]

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '48px 24px 120px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '28px', marginBottom: '32px' }}>
        <div style={{ width: '96px', height: '96px', background: 'var(--accent)', borderRadius: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: '"Chakra Petch", sans-serif', fontWeight: 700, fontSize: '44px', color: 'var(--bg-main)' }}>A−</div>
        <div>
          <div style={{ fontFamily: '"Chakra Petch", sans-serif', fontWeight: 700, fontSize: '34px', lineHeight: 1 }}>ÓTIMO VIBE!</div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>Grupo alinhado e satisfeito. Playlist criada no Spotify.</div>
        </div>
        <div style={{ flex: 1 }}></div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn-outline" onClick={() => navigate(`/rooms/${code}/vibe-check`)}>DAR FEEDBACK</button>
          {playlist_url && (
            <a href={playlist_url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
              <button className="btn" style={{ fontWeight: 600 }}>ABRIR NO SPOTIFY ▶</button>
            </a>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '28px' }}>
        {metrics.map((mt, i) => (
          <div key={i} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '14px', padding: '22px' }}>
            <div style={{ fontSize: '10px', letterSpacing: '0.16em', color: 'var(--text-subtle)' }}>{mt.label}</div>
            <div style={{ fontFamily: '"Chakra Petch", sans-serif', fontWeight: 700, fontSize: '34px', color: 'var(--text-main)', marginTop: '8px' }}>{mt.value}</div>
            <div style={{ fontSize: '11px', color: 'var(--success)', marginTop: '4px' }}>{mt.note}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '24px', alignItems: 'start' }}>
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '18px', padding: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ fontSize: '11px', letterSpacing: '0.18em', color: 'var(--text-subtle)' }}>PLAYLIST FINAL · {tracks.length} FAIXAS</div>
            <div style={{ fontSize: '11px', color: 'var(--success)' }}>SEQUENCIADA POR FLUXO</div>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {tracks.map((t, idx) => {
              const cBy = t.contributed_by.length > 0 ? t.contributed_by.join(', ') : 'Grupo';
              return (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '12px 14px', background: 'var(--bg-main)', borderRadius: '10px' }}>
                  <span style={{ width: '22px', fontSize: '12px', color: 'var(--text-subtle)' }}>{idx + 1}</span>
                  <div style={{ width: '38px', height: '38px', flex: 'none', borderRadius: '8px', background: 'repeating-linear-gradient(45deg, var(--accent) 0px, var(--accent) 4px, var(--bg-main) 4px, var(--bg-main) 8px)', opacity: 0.9 }}></div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '13.5px', fontWeight: 500 }}>{t.name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-subtle)', marginTop: '2px' }}>{t.artist} · via {cBy}</div>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '180px', textAlign: 'right', lineHeight: 1.4 }}>{t.reason}</div>
                </div>
              )
            })}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '18px', padding: '28px' }}>
            <div style={{ fontSize: '11px', letterSpacing: '0.18em', color: 'var(--text-subtle)', marginBottom: '20px' }}>REPRESENTAÇÃO POR MEMBRO</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {representation.map((r, i) => {
                const color = colors[i % colors.length];
                return (
                  <div key={r.user_id}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span>{r.display_name}</span>
                      <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{r.percentage}%</span>
                    </div>
                    <div style={{ height: '7px', background: 'var(--bg-main)', borderRadius: '99px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', background: color, borderRadius: '99px', width: `${r.percentage}%` }}></div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
          
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '18px', padding: '28px' }}>
            <button 
              onClick={() => setWhyOpen(!whyOpen)} 
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', background: 'transparent', border: 'none', color: 'var(--text-main)', fontFamily: '"IBM Plex Mono", monospace', fontSize: '13px', fontWeight: 600, cursor: 'pointer', padding: 0, letterSpacing: '0.04em' }}
            >
              <span>POR QUE ESSA PLAYLIST É JUSTA?</span>
              <span style={{ color: 'var(--accent)' }}>{whyOpen ? '−' : '+'}</span>
            </button>
            
            {whyOpen && why_items && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '20px' }}>
                {why_items.map((w, i) => (
                  <div key={i} style={{ display: 'flex', gap: '10px', fontSize: '12px', lineHeight: 1.6, color: 'var(--text-main)' }}>
                    <span style={{ color: 'var(--success)' }}>✓</span><span>{w}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <button className="btn-outline" style={{ padding: '16px', borderStyle: 'dashed', fontSize: '12px' }} onClick={() => navigate(`/rooms/${code}`)}>
            ↻ VOLTAR PARA SALA
          </button>
        </div>
      </div>
    </div>
  )
}
