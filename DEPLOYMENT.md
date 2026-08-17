# MacMine Lab — Deployment

**The actual application is never deployed anywhere, by design.** It's a
local tool: `./setup.sh` once, then `./dev.sh` or `./macmine serve` +
`cd frontend && npm run dev`, all on `127.0.0.1`. There is no production
build/hosting story for `backend/`/`frontend/` and there shouldn't be one
— see README's "What this is NOT" and "Data & privacy" sections for why
(no cloud account, nothing leaves the machine except pool traffic the
user explicitly configures).

## What IS deployed: `showcase/`

A separate static marketing/guide site, deployed to Vercel as its own
project (`showcase/.vercel/project.json` → project `macmine-lab`).
Confirmed live 2026-08-17: `curl` returned `200` for both the root page
and the guide page at `https://macmine-lab.vercel.app/`.

- Two serverless functions: `showcase/api/login.js` (password check,
  sets an HttpOnly session cookie), `showcase/api/guide.js` (returns
  gated guide HTML if the session cookie matches
  `GUIDE_SESSION_TOKEN`).
- Required env vars (set in Vercel, not in this repo — no `.env` file
  exists for `showcase/`): `GUIDE_PASSWORD`, `GUIDE_SESSION_TOKEN`. See
  `.env.example` at repo root for placeholders.
- Deploy mechanism (`vercel --prod`, or GitHub-connected auto-deploy) —
  [Needs confirmation]; not determined from files in this repo alone.

## Local-app env vars (not secrets — public defaults, overridable)

`frontend/.env.local` (not present/tracked in this repo — the frontend
runs with README's stated defaults unless someone creates one):
`NEXT_PUBLIC_MACMINE_API_BASE` (default `http://127.0.0.1:8834`),
`NEXT_PUBLIC_MACMINE_WS_BASE` (default `ws://127.0.0.1:8834`).
