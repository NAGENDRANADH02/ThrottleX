# Rate Limiter — Backend (Django API)

Sliding-window rate limiting using Redis Sorted Sets and an atomic Lua script, exposed as a JSON API. This is the backend half of the full-stack project — see the top-level `README.md` for how it pairs with the React frontend.

## How it works

1. Every request is stored as a timestamp in a Redis Sorted Set (`ZSET`), keyed by `user + IP + route`.
2. On each new request, three operations run **atomically** in a single Lua script on Redis:
   - `ZREMRANGEBYSCORE` — drop timestamps outside the current window
   - `ZCARD` — count requests remaining inside the window
   - `ZADD` — record the new request if still under the limit
3. Redis returns `allowed` + `remaining` in one round trip; the key auto-expires so idle users don't leak memory.

## Endpoints

| Endpoint | Method | Rate limited? | Purpose |
|---|---|---|---|
| `/health` | GET | No | Liveness check |
| `/check` | POST | No (it *is* the limiter) | Ask "is this request allowed?" from any external service — body: `{"userId","ip","route","plan"}` |
| `/metrics` | GET | No | In-memory counters: total/allowed/blocked requests, failover counts |
| `/login` | POST | Yes | Demo protected route |
| `/posts` | GET | Yes | Demo protected route |
| `/profile` | GET | Yes | Demo protected route |

Every rate-limited response carries `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `Retry-After` (on 429) headers.

## Rate limit configuration

| Plan       | Default limit  | Window |
|------------|-----------------|--------|
| FREE       | 100 requests    | 15 min |
| PRO        | 1,000 requests  | 15 min |
| ENTERPRISE | 10,000 requests | 15 min |

| Route          | Limit | Window |
|----------------|-------|--------|
| `POST /login`  | 5     | 60 sec |
| `GET /posts`   | 200   | 60 sec |
| `GET /profile` | 50    | 60 sec |

Route-specific limits always take priority over plan-based defaults. Edit `ratelimiter/config.py` to change these.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # set REDIS_URL, FAILOVER_MODE, CORS_ALLOWED_ORIGINS

docker run -d --name redis -p 6379:6379 redis:7-alpine

python manage.py migrate
python manage.py runserver
```

## Deploying for free (Render + Redis Cloud)

1. **Push to GitHub.**
2. **Redis Cloud** — sign up at redis.io/cloud (free, no card), create a database on the 30MB free plan, copy the connection string as `REDIS_URL`.
3. **Render** — sign up at render.com (free, no card), New → Web Service, connect your repo, set **Root Directory** to `backend`, Build Command to `./build.sh`, Start Command to `gunicorn ratelimiter_project.wsgi:application`.
4. **Environment variables** on Render: `DJANGO_SECRET_KEY` (long random string), `DJANGO_DEBUG=False`, `REDIS_URL` (from step 2), `FAILOVER_MODE=open`, `CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app`.
5. Deploy. Render runs `build.sh` (installs deps, collects static files, migrates) then starts gunicorn.
6. Test: `curl https://your-app.onrender.com/health`.

Render's free tier spins the service down after 15 minutes idle — the first request after a quiet spell takes ~30s to wake up. Fine for a portfolio demo, worth a heads-up if you're sharing the link live.

## Notes

- `metrics.py` uses in-process counters — fine for a single worker; for multi-worker production, swap to Redis `INCR`-based counters.
- `CORS_ALLOWED_ORIGINS` must include your deployed frontend's exact origin (scheme + domain, no trailing slash) or the browser will block the requests.
