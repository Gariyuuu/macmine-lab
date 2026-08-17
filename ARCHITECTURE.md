# MacMine Lab — Architecture

Three independent pieces; see FILE_MAP.md for the file-level breakdown.

## 1. Local app (the actual product)

```
./macmine (CLI) ──┐
                   ├──> backend/macmine_lab/  ──> data/macmine.db (SQLite)
frontend/ (Next.js)┘         │
   (browser, talks              ├─> XMRig (subprocess, local HTTP API)
   directly to backend)         ├─> monerod (subprocess, JSON-RPC)
                                └─> p2pool (subprocess)
```

- **Backend**: FastAPI, bound to `127.0.0.1` only — no auth, because
  nothing outside the Mac can reach it. REST for CRUD/control, one
  WebSocket (`/ws/live`) pushing telemetry + miner + benchmark + mining +
  safety state once per second. A background thread samples telemetry
  every 8s regardless of whether anything is running
  (`backend/macmine_lab/db.py`/`backend/macmine_lab/hardware.py`).
- **Frontend**: Next.js + TypeScript + Tailwind + shadcn/ui, talks
  directly to the backend from the browser via `fetch`/WebSocket (not
  through Next's own server) — `NEXT_PUBLIC_MACMINE_API_BASE`/
  `NEXT_PUBLIC_MACMINE_WS_BASE` env vars override the 127.0.0.1:8834
  default.
- **Subprocess management**: `backend/macmine_lab/runner.py` centralizes
  the launch/PID-track/signal (SIGTERM→SIGKILL, identity-reverified
  before signaling) pattern shared by XMRig, monerod, and p2pool — see
  CLAUDE.md rules 4-5.
- **Data**: single SQLite file, no ORM, direct SQL in
  `backend/macmine_lab/db.py`. See DATABASE.md.
- **External network calls** (the only ones this app makes, all
  documented and cached): CoinGecko (XMR/USD price), xmrchain.net
  (Monero network stats), the user's own configured mining pool (once
  real mining starts), Homebrew (installing XMRig/monerod),
  GitHub releases (downloading the p2pool binary).

## 2. Showcase site (separate, deployed)

Static HTML (`showcase/index.html`, `showcase/guide.html`) plus two Vercel
serverless functions (`showcase/api/login.js`, `showcase/api/guide.js`) implementing a
simple password-gated guide page. Deployed independently to
`macmine-lab.vercel.app` — has nothing to do with the local app's runtime
and doesn't talk to it. See FILE_MAP.md and CLAUDE.md.

## 3. Data directory (runtime state, not source)

`data/` — see FILE_MAP.md's breakdown. Everything here is either derived
(logs, PID files, integrity snapshots) or the one real database file.
Nothing under `data/` is uploaded anywhere; the app makes no calls that
send this data off the Mac (README's "Data & privacy" section, and this
pass didn't find anything contradicting it).

## Process safety model

Every subprocess this project launches (XMRig, monerod, p2pool) is
tracked by PID, re-verified via `ps` to still be the expected process
name before any signal is sent (never blindly signal a possibly-recycled
PID), and explicitly reaped (`os.waitpid(..., os.WNOHANG)`) rather than
relying on `ps` alone to reflect liveness — the last point was a real bug
found and fixed in Phase 7 (see DECISIONS.md D-004). No LaunchAgent/
LaunchDaemon, no autostart, no `sudo` anywhere in the project as of this
pass.
