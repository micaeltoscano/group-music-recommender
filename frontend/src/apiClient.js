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
}
