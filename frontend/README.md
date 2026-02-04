# ATEMS React Frontend (Phase 7)

Vite + React + TypeScript + Tailwind. Talks to Flask API.

## Develop

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173/app/ — Vite proxies `/api` to Flask (port 5000). Log in at http://localhost:5000/login first so the session cookie is set.

## Build for Production

```bash
npm run build
```

Outputs to `../static/app/`. Flask serves the SPA at `/app` (login required).

## Run with Flask

1. Start Flask: `python atems.py` or double-click desktop icon
2. Log in at http://localhost:5000/login
3. Go to http://localhost:5000/app
