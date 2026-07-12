// Cliente HTTP mínimo do frontend. A base da API vem de variável de ambiente
// do Vite (VITE_API_BASE_URL), com fallback para o backend local.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function getJson(path) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
  })
  const body = await res.json().catch(() => ({}))
  return { ok: res.ok, status: res.status, body }
}

export const api = {
  baseUrl: API_BASE_URL,
  health: () => getJson('/health'),
  healthDb: () => getJson('/health/db'),
}
