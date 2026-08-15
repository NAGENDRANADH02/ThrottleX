import { useState, useCallback, useRef, useEffect } from 'react'
import { callRoute, getHealth, getMetrics } from './api'

const ROUTES = [
  { path: '/login', label: 'POST /login', hint: '5/60s', cls: 'route-login' },
  { path: '/posts', label: 'GET /posts', hint: '200/60s', cls: 'route-posts' },
  { path: '/profile', label: 'GET /profile', hint: '50/60s', cls: 'route-profile' },
]

let nextId = 1

export default function App() {
  const [userId, setUserId] = useState('demo-user')
  const [plan, setPlan] = useState('FREE')
  const [entries, setEntries] = useState([])
  const [online, setOnline] = useState(null) // null = unknown, true/false once checked
  const logRef = useRef(null)

  // Ping /health once on load so the status dot reflects reality instead
  // of always claiming "online".
  useEffect(() => {
    getHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false))
  }, [])

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [entries])

  const addEntry = useCallback((line, kind) => {
    setEntries((prev) => [...prev, { id: nextId++, line, kind }])
  }, [])

  const fireOnce = useCallback(
    async (path) => {
      const method = path === '/login' ? 'POST' : 'GET'
      try {
        const result = await callRoute(path, { userId, plan })
        const kind = result.status === 429 ? 'blocked' : 'ok'
        addEntry(
          `${method} ${path} -> ${result.status} | limit=${result.limit} remaining=${result.remaining} reset=${result.reset}s`,
          kind,
        )
      } catch (err) {
        addEntry(`${method} ${path} -> network error: ${err.message}`, 'blocked')
      }
    },
    [userId, plan, addEntry],
  )

  const burst = useCallback(
    async (path, n) => {
      for (let i = 0; i < n; i++) {
        // eslint-disable-next-line no-await-in-loop
        await fireOnce(path)
      }
    },
    [fireOnce],
  )

  const clearLog = useCallback(() => setEntries([]), [])

  return (
    <div className="frame">
      <div className="eyebrow">
        <span
          className="dot"
          style={{
            background: online === false ? 'var(--crimson)' : 'var(--teal)',
            boxShadow: `0 0 0 3px ${online === false ? 'var(--crimson-dim)' : 'var(--teal-dim)'}`,
          }}
        />
        {online === false ? 'backend unreachable' : 'system online'} · sliding window · redis + lua
      </div>

      <h1>
        ThrottleX <span className="accent">/</span> Control Panel
      </h1>
      <p className="sub">
        Sends live requests to your Django API and reads back{' '}
        <code>X-RateLimit-*</code> headers in real time. Push a route past its
        limit to watch it trip.
      </p>

      <fieldset>
        <legend>Identity</legend>
        <div className="row">
          <div className="field">
            <label htmlFor="userId">X-User-Id</label>
            <input
              id="userId"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="plan">X-User-Plan</label>
            <select id="plan" value={plan} onChange={(e) => setPlan(e.target.value)}>
              <option value="FREE">FREE</option>
              <option value="PRO">PRO</option>
              <option value="ENTERPRISE">ENTERPRISE</option>
            </select>
          </div>
        </div>
      </fieldset>

      <fieldset>
        <legend>Fire requests</legend>
        <div className="btn-grid">
          {ROUTES.map((r) => (
            <button key={r.path} className={r.cls} onClick={() => fireOnce(r.path)}>
              {r.label} <span className="dim">— {r.hint}</span>
            </button>
          ))}
        </div>
        <div className="divider" />
        <div className="btn-grid">
          <button className="burst" onClick={() => burst('/login', 8)}>
            ⚡ burst 8× /login
          </button>
          <button className="ghost" onClick={clearLog}>
            clear log
          </button>
        </div>
      </fieldset>

      <div className="log-frame">
        <div className="log-label">
          <span>readout</span>
          <span className="live">● live</span>
        </div>
        <div id="log" ref={logRef}>
          {entries.length === 0 && <div className="empty">awaiting requests…</div>}
          {entries.map((e) => (
            <div key={e.id} className={e.kind}>
              {e.line}
            </div>
          ))}
        </div>
      </div>

      <div className="key">
        <span className="k-ok">
          <i /> 200 allowed
        </span>
        <span className="k-blocked">
          <i /> 429 blocked
        </span>
      </div>
    </div>
  )
}
