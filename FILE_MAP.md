# MacMine Lab — File Map

Three independent parts in one repo: the local app (`backend/` +
`frontend/`), the deployed showcase site (`showcase/`), and runtime data
(`data/`).

## Local app entry points

- `./macmine` — CLI entry (`hardware`, `setup`, `integrity`, `benchmark`,
  `calibrate`, `status`, `stop`, `serve`).
- `./setup.sh` — one-time environment setup (Python/uv/XMRig via
  Homebrew).
- `./dev.sh` — starts backend + dashboard together.

## Backend (`backend/macmine_lab/`)

- `backend/macmine_lab/api.py` — FastAPI app, all REST + `/ws/live`
  WebSocket routes (full list in README.md).
- `backend/macmine_lab/cli.py` — the `./macmine` CLI, shares logic with
  `backend/macmine_lab/api.py` rather than duplicating it.
- `backend/macmine_lab/db.py` — SQLite access layer for
  `data/macmine.db`. See DATABASE.md.
- `backend/macmine_lab/hardware.py` — Apple Silicon detection, live
  telemetry, thermal-state derivation (`pmset -g therm`).
- `backend/macmine_lab/benchmark.py` — RandomX benchmark orchestration
  (`xmrig --bench=10M`, self-enforced duration, local HTTP API polling).
- `backend/macmine_lab/calibration.py` — thread-count calibration
  logic, shared by `./macmine calibrate` and the `/journal` page's
  recommended configs.
- `backend/macmine_lab/miner.py`, `mining.py`, `mining_runner.py` —
  XMRig process lifecycle for benchmark mode and real mining mode
  respectively.
- `backend/macmine_lab/xmrig_api.py` — client for XMRig's own local
  HTTP API (127.0.0.1, random per-run token).
- `backend/macmine_lab/wallet.py`, `backend/macmine_lab/pools.py` —
  wallet/pool CRUD + format validation (no checksum verification for
  wallets — documented limitation).
- `backend/macmine_lab/economics.py`, `backend/macmine_lab/price.py` —
  CoinGecko price + xmrchain.net network stats, cached in SQLite,
  earnings estimation.
- `backend/macmine_lab/achievements.py` — First Penny achievement logic.
- `backend/macmine_lab/analytics.py` — real-correlation-only chart data
  for `/analytics`.
- `backend/macmine_lab/safety.py` — thermal/battery automation
  (NORMAL/WARM/HOT/CRITICAL), the one hard, non-disableable floor in the
  project.
- `backend/macmine_lab/notifications.py` — local `osascript display
  notification` wrapper, never raises on failure.
- `backend/macmine_lab/monerod.py`, `backend/macmine_lab/p2pool.py` —
  Phase 7 P2Pool: install/verify, process lifecycle, sync status.
- `backend/macmine_lab/network.py` — pool connection-reachability
  testing (TCP/TLS only, not the mining protocol).
- `backend/macmine_lab/integrity.py` — XMRig/monerod/p2pool binary
  integrity records (SHA-256, install source, verification method).
- `backend/macmine_lab/paths.py` — centralizes `data/` subpath
  resolution.
- `backend/macmine_lab/runner.py` — shared subprocess-launch/PID-
  tracking/signal (SIGTERM→SIGKILL) logic reused across
  xmrig/monerod/p2pool.
- `backend/tests/` — 180 tests, one file per module above roughly 1:1
  (e.g. `backend/tests/test_hardware.py`,
  `backend/tests/test_benchmark.py`, `backend/tests/test_p2pool.py`).

## Frontend (`frontend/src/`)

- `app/` — one route folder per dashboard page: root (hero/benchmark),
  `setup`, `earnings`, `first-penny`, `journal`, `analytics`, `p2pool`,
  `changelog` (reads root `CHANGELOG.md` directly off disk — see
  CLAUDE.md).
- `components/ui/` — shadcn/ui primitives.
- `lib/` — API/WebSocket client helpers
  (`NEXT_PUBLIC_MACMINE_API_BASE`/`NEXT_PUBLIC_MACMINE_WS_BASE`).

## Showcase (`showcase/`) — separate deployed static site

- `showcase/index.html`, `showcase/guide.html` — marketing/guide pages,
  live at `macmine-lab.vercel.app` (confirmed 2026-08-17).
- `showcase/api/login.js` — password-gate serverless function
  (`GUIDE_PASSWORD`/`GUIDE_SESSION_TOKEN` env vars, Vercel-side only).
- `showcase/api/guide.js` — serves the gated guide content (cookie-token checked
  against `GUIDE_SESSION_TOKEN`): a hardcoded HTML walkthrough confirming
  the local DB's wallet/pool are synthetic test values ("not a real
  address") and walking through switching to a real wallet/pool via
  `/setup` — corroborates this pass's own database inspection.
- `assets/` — screenshots (`dashboard.png`, `journal.png`, `p2pool.png`).
- `.vercel/` — gitignored, links to Vercel project `macmine-lab`.

## Data (`data/`, gitignored except structure)

- `macmine.db` — SQLite, all persistent state. See DATABASE.md.
- `logs/` — raw XMRig/monerod/p2pool stdout/stderr, `--log-file`-based
  for XMRig (see CLAUDE.md rule 6).
- `run/` — PID files for whatever's currently running.
- `integrity/` — human-readable integrity snapshots.
- `bin/` — downloaded p2pool binary.
- `benchmarks/`, `p2pool-cache/` — supporting runtime artifacts.
- `monerod-chain/` — only created if the user explicitly confirms a
  P2Pool blockchain sync; not present as of this pass.

## Pre-existing documentation (kept as-is)

- `README.md` (482 lines) — the real, comprehensive project doc: every
  command, every REST endpoint, phase-by-phase feature detail,
  troubleshooting. Read it before assuming a gap exists that this memory
  system's shorter files don't mention.
- `CHANGELOG.md` — **user-facing**, rendered live in the dashboard's
  `/changelog` page. Don't add internal doc-audit notes to it.
