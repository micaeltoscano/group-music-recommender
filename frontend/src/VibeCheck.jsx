import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from './apiClient'

export function VibeCheck() {
  const { code } = useParams()
  const navigate = useNavigate()

  const [questions, setQuestions] = useState([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers, setAnswers] = useState({})
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    async function load() {
      const res = await api.getVibeCheck(code)
      if (res.ok) {
        setQuestions(res.body.questions)
      } else {
        setError(res.body?.detail || 'Erro ao carregar Vibe Check.')
      }
      setLoading(false)
    }
    load()
  }, [code])

  const currentQ = questions[currentIdx]

  const handlePick = async (opt) => {
    if (!currentQ) return

    const newAnswers = { ...answers, [currentQ.id]: opt.value }
    setAnswers(newAnswers)

    if (currentIdx < questions.length - 1) {
      setCurrentIdx((prev) => prev + 1)
    } else {
      await submitAnswers(newAnswers)
    }
  }

  const skipVibe = () => {
    navigate(`/rooms/${code}`)
  }

  const submitAnswers = async (finalAnswers) => {
    setIsSubmitting(true)
    // Se faltar alguma resposta, preenche com 0.5 (neutro)
    const payload = {
      energy: finalAnswers.energy !== undefined ? finalAnswers.energy : 0.5,
      valence: finalAnswers.valence !== undefined ? finalAnswers.valence : 0.5,
      popularity: finalAnswers.popularity !== undefined ? finalAnswers.popularity : 0.5,
    }

    const res = await api.submitVibeCheck(code, payload)
    if (res.ok) {
      setDone(true)
    } else {
      setError(res.body?.detail || 'Erro ao enviar respostas.')
      setIsSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="layout-content">
        <div style={{ padding: '72px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Carregando Vibe Check...
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

  if (done) {
    return (
      <div className="layout-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '56px 24px 120px' }}>
        <div style={{ fontSize: '11px', letterSpacing: '0.2em', color: 'var(--text-subtle)', marginBottom: '18px' }}>[ VC-01 · FEEDBACK MODULE ]</div>
        <div style={{ width: '520px', maxWidth: '100%', background: 'var(--bg-card)', border: '1px solid var(--success)', borderRadius: '20px', padding: '48px', textAlign: 'center' }}>
          <div style={{ fontFamily: '"Chakra Petch", sans-serif', fontWeight: 700, fontSize: '40px', color: 'var(--success)' }}>✓</div>
          <div style={{ fontFamily: '"Chakra Petch", sans-serif', fontWeight: 600, fontSize: '26px', marginTop: '12px' }}>Tudo pronto!</div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.6, marginTop: '10px' }}>
            Seu feedback alimenta a negociação da playlist do grupo.
          </div>
          <button 
            onClick={() => navigate(`/rooms/${code}`)}
            className="btn btn-primary" 
            style={{ marginTop: '28px' }}
          >
            VOLTAR PARA O LOBBY
          </button>
        </div>
      </div>
    )
  }

  if (!currentQ) return null

  return (
    <div className="layout-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '72px 24px 120px' }}>
      <div style={{ fontSize: '11px', letterSpacing: '0.2em', color: 'var(--text-subtle)', marginBottom: '18px' }}>[ VC-01 · VIBE CHECK MODULE ]</div>
      <div style={{ width: '620px', maxWidth: '100%', background: 'var(--bg-card)', border: '1px solid var(--border-dark)', borderRadius: '20px', padding: '44px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
          <div style={{ fontSize: '12px', letterSpacing: '0.14em', color: 'var(--success)' }}>
            PERGUNTA {currentIdx + 1}/{questions.length}
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            {questions.map((_, i) => (
              <div 
                key={i} 
                style={{ 
                  width: '6px', height: '6px', borderRadius: '3px', 
                  background: i === currentIdx ? 'var(--success)' : (i < currentIdx ? 'var(--success)' : 'var(--border-dark)'),
                  opacity: i === currentIdx ? 1 : 0.5 
                }} 
              />
            ))}
          </div>
        </div>
        
        <div style={{ fontFamily: '"Chakra Petch", sans-serif', fontWeight: 600, fontSize: '26px', lineHeight: 1.3 }}>
          {currentQ.text}
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '32px' }}>
          {currentQ.options.map((op) => (
            <button 
              key={op.id}
              onClick={() => handlePick(op)}
              disabled={isSubmitting}
              style={{
                display: 'flex', alignItems: 'center', gap: '16px', width: '100%',
                textAlign: 'left', padding: '18px 20px', background: 'var(--bg-darker)',
                border: '1px solid var(--border-light)', borderRadius: '12px',
                color: 'var(--text-main)', fontFamily: '"IBM Plex Mono", monospace',
                fontSize: '13.5px', lineHeight: 1.5, cursor: isSubmitting ? 'wait' : 'pointer',
                transition: 'border-color 0.2s, background 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent)'
                e.currentTarget.style.background = 'var(--bg-hover)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-light)'
                e.currentTarget.style.background = 'var(--bg-darker)'
              }}
            >
              <span style={{
                width: '32px', height: '32px', flex: 'none', borderRadius: '8px',
                background: 'var(--border-dark)', color: 'var(--accent)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 600
              }}>
                {op.letter}
              </span>
              <span>{op.text}</span>
            </button>
          ))}
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '28px', fontSize: '12px' }}>
          <button 
            onClick={skipVibe}
            disabled={isSubmitting}
            style={{ 
              background: 'transparent', border: 'none', color: 'var(--accent)', 
              textDecoration: 'underline', cursor: 'pointer', fontFamily: '"IBM Plex Mono", monospace',
              padding: 0
            }}
          >
            pular o vibe check →
          </button>
          <span style={{ color: 'var(--text-subtle)' }}>suas respostas viram variáveis do algoritmo</span>
        </div>
      </div>
    </div>
  )
}
