// In dev, requests go through the Vite proxy (see vite.config.js) so this
// can stay empty (same-origin, e.g. "/login"). In production, point
// VITE_API_URL at your deployed Django backend, e.g.
// https://your-app.onrender.com — set it in a .env.production file or
// as a build-time environment variable on your hosting platform.
const API_BASE = import.meta.env.VITE_API_URL || ''

/**
 * Calls a protected demo route (/login, /posts, /profile) and returns a
 * normalized result the UI can render, including the rate-limit headers.
 */
export async function callRoute(path, { userId, plan }) {
  const method = path === '/login' ? 'POST' : 'GET'

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'X-User-Id': userId || 'anonymous',
      'X-User-Plan': plan || 'FREE',
    },
  })

  let body = null
  try {
    body = await res.json()
  } catch {
    // some 429 responses may not have a JSON body in edge cases - ignore
  }

  return {
    status: res.status,
    ok: res.ok,
    limit: res.headers.get('X-RateLimit-Limit'),
    remaining: res.headers.get('X-RateLimit-Remaining'),
    reset: res.headers.get('X-RateLimit-Reset'),
    body,
  }
}

/** GET /health */
export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`)
  return res.json()
}

/** GET /metrics */
export async function getMetrics() {
  const res = await fetch(`${API_BASE}/metrics`)
  return res.json()
}
