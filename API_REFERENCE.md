# MacMine Lab — API Reference

The full, real endpoint list already lives in README.md's "Local backend
(Phase 2)" section (every REST route + the `/ws/live` WebSocket) — not
duplicated here to avoid drift between two copies. Read it there.

## What's not in README (the auth/network model)

- No authentication anywhere — the FastAPI server binds to `127.0.0.1`
  only (`backend/macmine_lab/api.py`), so there's nothing to
  authenticate against. Confirmed no auth middleware/dependency exists
  by reading `FILE_MAP.md`'s module list; not re-verified line-by-line
  in `backend/macmine_lab/api.py` this pass.
- CORS matches any `localhost`/`127.0.0.1` origin at any port (README) —
  intentional, since this never leaves the Mac either way and Next.js
  picks a free port.
- The one separate API surface is `showcase/api/` (Vercel serverless
  functions, `showcase/api/login.js` + `showcase/api/guide.js`) — a
  completely different system, password-gated, unrelated to the local
  backend. See ARCHITECTURE.md.

## Not independently re-verified this pass

Whether every documented endpoint's actual behavior (status codes, error
shapes, exact auth/validation per route) matches README's one-line
descriptions — this pass read the file tree and README's list, not every
handler body in `backend/macmine_lab/api.py`. [Needs confirmation] for
anything more specific than what README already states.
