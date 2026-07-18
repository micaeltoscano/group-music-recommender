// Cliente HTTP mínimo do frontend. A base da API vem de variável de ambiente
// do Vite (VITE_API_BASE_URL), com fallback para o backend local.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function requestJson(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    ...options,
  })
  const body = await res.json().catch(() => ({}))
  return { ok: res.ok, status: res.status, body }
}

export const api = {
  baseUrl: API_BASE_URL,
  health: () => requestJson('/health'),
  healthDb: () => requestJson('/health/db'),
  getMe: () => requestJson('/auth/me'),
  createRoom: () => requestJson('/rooms', { method: 'POST' }),
  joinRoom: (code) => requestJson(`/rooms/${encodeURIComponent(code)}/join`, { method: 'POST' }),
  getRoom: (code) => requestJson(`/rooms/${encodeURIComponent(code)}`),
  getConsensusModes: () => requestJson('/rooms/consensus-modes'),
  updateRoomContext: (code, context) => requestJson(`/rooms/${encodeURIComponent(code)}/context`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(context),
  }),
  updateRoomMode: (code, mode) => requestJson(`/rooms/${encodeURIComponent(code)}/mode`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  }),
  getVibeCheck: (code) => requestJson(`/rooms/${encodeURIComponent(code)}/vibe-check`),
  submitVibeCheck: (code, answers) => requestJson(`/rooms/${encodeURIComponent(code)}/vibe-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(answers),
  }),
  skipVibeCheck: (code) => requestJson(`/rooms/${encodeURIComponent(code)}/vibe-check/skip`, {
    method: 'POST',
  }),
  generatePlaylist: (code) => requestJson(`/rooms/${encodeURIComponent(code)}/generate`, { method: 'POST' }),
  getRoomResult: (code) => requestJson(`/rooms/${encodeURIComponent(code)}/result`),
  submitTrackFeedback: (runId, trackId, feedback) => requestJson(
    `/playlist-runs/${encodeURIComponent(runId)}/tracks/${encodeURIComponent(trackId)}/feedback`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedback),
    },
  ),
  submitPlaylistFeedback: (runId, feedback) => requestJson(
    `/playlist-runs/${encodeURIComponent(runId)}/feedback`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedback),
    },
  ),
}
