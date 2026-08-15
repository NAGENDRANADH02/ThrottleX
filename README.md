# Rate Limiter — Django + React

A full-stack rate limiting system. Django + Redis handle the actual sliding-window enforcement; React is a control-panel style client that fires live requests at the API and reads back the rate-limit headers in real time.

```
fullstack/
├── backend/     # Django API — the rate limiter engine
└── frontend/    # React (Vite) client
```

## How it works

- **Backend**: sliding-window rate limiting via Redis Sorted Sets + an atomic Lua script. Plan-based limits (FREE/PRO/ENTERPRISE) with route-specific overrides. Exposes `/health`, `/check`, `/metrics`, and demo protected routes `/login`, `/posts`, `/profile`.
- **Frontend**: a control-panel UI where you set an identity (user ID + plan), fire requests at any route, and watch the live readout — every response includes `X-RateLimit-Limit/Remaining/Reset` headers which the UI renders directly.

See `backend/` for the full API details (rate limit table, algorithm explanation, deployment notes).

## Running locally

You need two terminals (backend + frontend) and Redis running.

**1. Start Redis**
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

**2. Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```
Runs on `http://localhost:8000`.

**3. Frontend**
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173`. The Vite dev server proxies `/login`, `/posts`, `/profile`, `/health`, `/check`, `/metrics` straight to `localhost:8000`, so there's no CORS friction in dev — just open `http://localhost:5173` and start firing requests.

## Production

The two halves deploy independently:

- **Backend** → Render (free tier) + Redis Cloud (free tier). See `backend/README.md` for the step-by-step.
- **Frontend** → Vercel or Netlify (both free for static sites). Set the build command to `npm run build`, output directory to `dist`, and add an environment variable `VITE_API_URL=https://your-backend.onrender.com` so the built app calls your live backend instead of `localhost`.

Also set `CORS_ALLOWED_ORIGINS` on the backend to your deployed frontend's URL (e.g. `https://your-app.vercel.app`), since in production the frontend and backend live on different domains and the Vite proxy no longer applies.
