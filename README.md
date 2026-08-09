# MacMine Lab

A local, transparent Monero (XMR) / RandomX mining laboratory for Apple
Silicon Macs. Built to learn how proof-of-work mining actually works, watch
real hashing happen on your own hardware, and — eventually — earn your
first few cents of real cryptocurrency.

## What this is

- A CLI and a local dashboard that run the real [XMRig](https://xmrig.com)
  miner on **your Mac**, under **your control**, mining to a pool and wallet
  you configure yourself.
- Fully local: no cloud account, no remote database. Nothing leaves your
  machine except the RandomX work you explicitly choose to submit to a pool
  once you've set one up — benchmark mode makes zero network connections.
- Honest about what it shows you. If something isn't measured, MacMine Lab
  displays "Unavailable" — it never fabricates a hashrate, a temperature, or
  an earnings number.

## What this is NOT

- Not cryptojacking, not a background miner, not malware, not a persistence
  mechanism, not a botnet, not hidden in any way.
- Not something that mines on anyone else's computer.
- Not a commercial mining operation, and MacMine Lab takes **0%** of
  anything it ever mines — there is no developer fee beyond whatever
  donation level XMRig itself reports (see "Miner Integrity" below).

## System requirements

- Apple Silicon Mac (M1–M4 and later); this has been built and tested on an
  **Apple M4 Pro** MacBook Pro (12 cores: 8 performance + 4 efficiency),
  24 GB RAM, macOS 15.1.
- macOS with [Homebrew](https://brew.sh) installed (MacMine Lab will not
  install Homebrew for you).
- ~2.3 GB free RAM available at mining time for RandomX's dataset
  (allocated once, shared across all threads).

## Current status: Phase 5 of 7

- ✅ **Phase 1** — Apple Silicon hardware detection, live telemetry, XMRig
  install/verification via Homebrew, fully-offline duration-controlled
  RandomX benchmarking, thread calibration, hard verified STOP.
- ✅ **Phase 2** — local FastAPI backend (127.0.0.1 only) with SQLite
  persistence: benchmark runs, telemetry history, and miner integrity are
  now stored in `data/macmine.db` instead of flat JSON files. A background
  sampler records telemetry every 8 seconds. REST endpoints for hardware,
  live/historical telemetry, miner status/stop, and starting/reading
  benchmarks; a `/ws/live` WebSocket pushes real telemetry + miner + active
  benchmark state once per second.
- ✅ **Phase 3** — the dashboard: Next.js + TypeScript + Tailwind + shadcn/ui
  at `frontend/`. Live hashrate hero metric + chart, system health panel,
  benchmark start/stop controls, a real XMRig log terminal, and recent-runs
  history — all wired to the Phase 2 backend, no mock data anywhere.
- ✅ **Phase 4** — real XMR mining: a Setup page for your wallet address and
  pool config, a network-reachability connection test, and a Real Mining
  panel on the dashboard showing live accepted/rejected shares. MacMine Lab
  never ships a pool preset — you add your own.
- ✅ **Phase 5** — First Penny challenge + earnings estimates: live XMR
  price (CoinGecko) and Monero network difficulty/hashrate (xmrchain.net),
  an Earnings page with a real electricity-cost calculator, and a First
  Penny page with achievements — all built on real, cached, gracefully-
  degrading data, never fabricated numbers.

**Not yet built:** thermal/battery automation, the experiment journal, and
P2Pool. Those are Phases 6–7. This README will be updated as each phase
lands — see `CHANGELOG.md`.

## Quick start

```bash
cd macmine-lab
./setup.sh
./macmine hardware
./macmine benchmark --duration 30

# dashboard (needs Node/npm — run once):
cd frontend && npm install && cd ..
./dev.sh   # starts the backend + dashboard together; Ctrl-C stops both
```

`setup.sh` checks for macOS + Apple Silicon, ensures Python 3.11 (arm64) and
`uv` are available (installing them via Homebrew if missing — Homebrew
itself is never auto-installed), creates an isolated virtualenv at
`backend/.venv`, and installs/verifies XMRig via Homebrew. It does not touch
`frontend/` — run `npm install` there once yourself.

## Commands

```bash
./macmine hardware              # detected chip/cores/RAM + live telemetry
./macmine setup                 # (re)install/verify XMRig via Homebrew
./macmine integrity             # show the recorded XMRig integrity record
./macmine benchmark             # 30s RandomX benchmark, all detected threads
./macmine benchmark --threads 6 --duration 60
./macmine calibrate             # benchmark several thread counts, recommend configs
./macmine status                # is a MacMine-launched xmrig running right now?
./macmine stop                  # hard stop — SIGTERM then SIGKILL, verified
./macmine serve                 # run the local backend API on 127.0.0.1:8834
```

## Local backend (Phase 2)

`./macmine serve` starts a FastAPI server bound to **127.0.0.1 only** —
nothing outside your Mac can reach it.

```
GET  /api/health
GET  /api/hardware
GET  /api/telemetry/live              # one real-time sample, on demand
GET  /api/telemetry/history?minutes=  # from SQLite, sampled every 8s in the background
GET  /api/integrity                   # latest recorded XMRig integrity check
GET  /api/miner/status
POST /api/miner/stop
POST /api/benchmark/start?threads=&duration_seconds=30|60|300
GET  /api/benchmark/live              # progress of whatever benchmark is running now
GET  /api/benchmark/history?limit=
GET  /api/benchmark/{id}
POST /api/wallets/validate            # local format check only, no network, no save
POST /api/wallets                     # {address, label?}
GET  /api/wallets
DELETE /api/wallets/{id}
POST /api/pools                       # {name, host, port, tls, worker_name?, password?, notes?}
GET  /api/pools
DELETE /api/pools/{id}
POST /api/pools/test-connection       # {host, port, tls} — TCP/TLS reachability only
POST /api/mining/start                # {pool_id, wallet_id, threads}
POST /api/mining/stop
GET  /api/mining/live
GET  /api/mining/history?limit=
GET  /api/mining/{id}
GET  /api/economics/price             # cached CoinGecko XMR/USD, 503 if unavailable
GET  /api/economics/network           # cached xmrchain.net difficulty/hashrate, 503 if unavailable
GET  /api/economics/settings          # your saved electricity rate + power draw estimate
POST /api/economics/settings          # {electricity_rate_usd_per_kwh?, power_draw_watts?}
GET  /api/economics/estimate?hashrate_hs=
GET  /api/first-penny                 # cumulative real stats + estimated earnings + achievements
WS   /ws/live                         # telemetry + miner + benchmark + mining state, 1x/second
```

All benchmark/telemetry/integrity data now lives in `data/macmine.db`
(SQLite) rather than the flat JSON files Phase 1 used — the CLI and the API
server read and write the same database, so `./macmine benchmark` and
`./macmine setup` results show up immediately through the API too.

## Dashboard (Phase 3)

`frontend/` is a Next.js + TypeScript + Tailwind + shadcn/ui app. It talks
directly to the backend from your browser (`NEXT_PUBLIC_MACMINE_API_BASE` /
`NEXT_PUBLIC_MACMINE_WS_BASE` env vars override the defaults of
`http://127.0.0.1:8834` / `ws://127.0.0.1:8834` if you run the backend on a
different port). The backend's CORS policy matches any `localhost`/
`127.0.0.1` origin at any port, since Next.js picks whatever port is free
and this never leaves your Mac either way.

The dashboard shows: a hero hashrate metric (live while a benchmark runs,
last-run average when idle), a live chart, a system health panel (CPU,
memory, battery, thermal state), benchmark start/stop controls, a real
XMRig log terminal (tailing the actual log file XMRig writes — see the
buffering note below), and a table of recent runs. It never shows a
"MINING" state or any XMR/USD figures — those require Phase 4's real wallet/
pool mining, so the dashboard is explicit that this is benchmark mode.

**A real bug found and fixed this phase:** XMRig fully-buffers its stdout
once it isn't attached to a terminal, so every log file MacMine Lab wrote by
redirecting XMRig's stdout in Phase 1/2 came out **0 bytes** — the buffered
data was lost when the process was SIGTERM'd rather than exiting normally.
Fixed by using XMRig's own `--log-file` flag, which flushes each line
itself; stderr (used for crash diagnostics) is unbuffered by default and
was never affected.

## Real mining (Phase 4)

**Setup:** open the dashboard and click "Setup →" (or go to `/setup`
directly). Two things are required before you can mine for real:

1. **A public XMR wallet address.** Get one from the official
   [Monero CLI/GUI wallet](https://www.getmonero.org/downloads/) or any
   reputable wallet app. MacMine Lab validates the address's format locally
   (base58 charset, length, and prefix for standard/subaddress/integrated
   addresses) — this catches typos but is **not** a full checksum
   verification. There is a permanent on-screen warning: MacMine Lab never
   asks for a seed phrase, recovery phrase, or private/spend key, and never
   will — only the public address, which is all pool mining ever needs.
2. **A pool.** MacMine Lab ships **no pool preset** — add your own (name,
   host, port, TLS, optional worker name/password). We looked into shipping
   verified defaults for well-known pools (SupportXMR, HashVault) but their
   connection details are served from JS-rendered pages we couldn't fetch
   reliably; rather than hardcode a host:port we couldn't verify as current,
   we shipped the CRUD and left it to you — check the pool's own site for
   its current details before adding it here.

**Connection test** is a plain TCP (and, for TLS, TLS-handshake) reachability
check against the host:port you entered — it does not speak the mining
protocol or send your wallet address, so it can't tell you whether the pool
will accept your address. That's only provable by actually mining, which is
exactly what the dashboard's Real Mining panel shows live: accepted/rejected
share counts, updated once per second over the same WebSocket the benchmark
chart uses.

Real mining has no fixed duration — it runs until you click STOP, which
signals a background loop (checked every ~1s) that then stops XMRig the same
verified way benchmark mode does (SIGTERM → SIGKILL fallback, PID re-checked
before signaling). Every session — pool, wallet, threads, duration, average/
peak hashrate, and final accepted/rejected share counts — is saved to
`mining_sessions` in SQLite, separate from benchmark history.

## First Penny & Earnings (Phase 5)

**`/earnings`** shows real, live data — current XMR/USD price from
[CoinGecko](https://www.coingecko.com/en/api) and current Monero network
difficulty/hashrate/block reward from
[xmrchain.net](https://xmrchain.net), a community block explorer (not the
official Monero project — disclosed on the page). Both are cached in SQLite
(price: 5 min, network: 150s, since network stats move roughly once per
block) so we don't hammer either API, and both show "PRICE DATA
UNAVAILABLE" / "NETWORK DATA UNAVAILABLE" rather than a fabricated number
if the live fetch fails and there's no usable cache. You enter your
hashrate, an electricity rate ($/kWh), and a power-draw estimate — power
draw is **not measured**: macOS doesn't expose real-time power draw
without `sudo powermetrics`, which this project avoids, so it's your own
estimate, clearly labeled as such. Every output (XMR/USD per hour/day,
electricity cost, net) is explicitly an estimate.

**`/first-penny`** tracks progress toward an estimated $0.01 from real
mining, plus achievements. Three numbers here are **real, measured facts**:
total hashes attempted (benchmark + mining combined), total shares actually
accepted by a pool (mining only — benchmark mode never touches a pool), and
total real mining time. The dollar figure is explicitly an **estimate**:
for each finished mining session, it multiplies that session's own real
average hashrate by its real duration, valued at *current* network
difficulty and price (not the conditions at the time the session actually
ran) — the page says so directly. This is never mixed with or presented as
a pool balance or wallet balance, which MacMine Lab has no way to verify in
this version. "First Payout" is a defined achievement that **can never
auto-unlock** here for the same reason — it stays locked with an honest
explanation rather than being faked.

## Benchmarking, explained

XMRig's `--stress` mode dials an external `randomx.xmrig.com` server by
default — we don't use it. MacMine Lab's benchmark mode uses
`xmrig --bench=10M` (the largest hash-count XMRig's benchmark flag accepts)
purely as a ceiling that won't be reached inside a 30s/1min/5min test
window. We enforce the actual duration ourselves and poll XMRig's **local**
HTTP API (127.0.0.1, random per-run access token) once a second for real
hashrate samples, then stop the process. This was verified directly during
development: while a benchmark runs, `lsof -i` shows only the local
listening socket XMRig opens for its own API — no outbound connections.

RandomX allocates a ~2.3 GB dataset shared across all threads (not
per-thread) the first time it runs; that takes a few seconds. The first
~10 seconds of each benchmark run are excluded from the reported average so
this warmup doesn't skew the numbers.

## Miner integrity

XMRig is installed **only** via Homebrew's `homebrew-core` formula, which
builds from the real [xmrig/xmrig](https://github.com/xmrig/xmrig) project
source and ships bottles whose checksums Homebrew validates before
installing. `./macmine integrity` additionally shows the SHA-256 MacMine Lab
computed itself from the binary actually on disk, its architecture, and its
version — so this is auditable, not just asserted.

## Safety model

- MacMine Lab tracks the PID of any xmrig process it launches in
  `data/run/xmrig.pid`. Before signaling anything, it re-checks via `ps`
  that the PID is still actually a process named `xmrig` — it will never
  send a signal to a recycled PID that belongs to something else.
- `./macmine stop` sends `SIGTERM`, waits up to 5 seconds, and falls back to
  `SIGKILL` if needed, then confirms the process is actually gone.
- No LaunchAgent/LaunchDaemon, no autostart, no sudo anywhere in this phase.

## Data & privacy

Everything MacMine Lab writes lives under `data/` in this repo: `data/macmine.db`
(SQLite — benchmark runs, telemetry history, miner integrity records, wallet
addresses, pool configs, and mining sessions), `data/logs/` (raw XMRig
output), `data/run/` (the current PID file, if anything is running),
`data/integrity/` (a human-readable snapshot of the latest integrity check).
Nothing is uploaded anywhere. The wallets table stores only the public
address and an optional label — there is no column for a seed phrase or
private key, so there's nothing sensitive of that kind to leak even
locally. There is no authentication because there is nothing to
authenticate against — the API server only ever binds to 127.0.0.1.

## Troubleshooting

- **"MacMine Lab isn't set up yet"** — run `./setup.sh`.
- **"xmrig is not installed"** — run `./macmine setup`, or `brew install xmrig`
  directly.
- **Benchmark shows "Unavailable" for hashrate** — the run was likely too
  short relative to RandomX's dataset warmup; try `--duration 60`.
- **Homebrew not found** — install it yourself from https://brew.sh; MacMine
  Lab deliberately does not install Homebrew on your behalf.
- **Dashboard shows "Disconnected" / data never loads** — the backend isn't
  running; start it with `./macmine serve` or `./dev.sh`.
- **CORS errors in the browser console** — should not happen (the backend
  matches any localhost/127.0.0.1 origin), but if you've customized
  `NEXT_PUBLIC_MACMINE_API_BASE` to something other than localhost, you'll
  need to add that origin to `allow_origin_regex` in `backend/macmine_lab/api.py`.
- **"Invalid wallet" when saving** — check the address is a real Monero
  standard (starts `4`, 95 chars), subaddress (starts `8`, 95 chars), or
  integrated (starts `4`, 106 chars) address with no typos. This is format
  validation only; if the format looks right but the pool still rejects
  every share, double check you copied the whole address.
- **Connection test succeeds but mining shows 0 shares for a long time** —
  normal at low hashrate: pool difficulty means shares can take minutes to
  hours depending on your hashrate and the pool's configured difficulty.
  Check the log terminal for `new job received` lines to confirm you're
  actually receiving work from the pool.
- **No accepted shares ever, log shows connection errors** — verify host/
  port/TLS match what the pool currently publishes (pools change these
  periodically); re-run the connection test after fixing.
- **"PRICE DATA UNAVAILABLE" / "NETWORK DATA UNAVAILABLE"** — CoinGecko or
  xmrchain.net is unreachable (or rate-limiting) and there's no cached
  value young enough to fall back to; wait and reload, or check your
  network connection.
- **Estimated earnings look tiny / went negative** — that's real math, not
  a bug: at a few kH/s your share of the ~5+ GH/s Monero network is
  minuscule, and electricity cost can easily exceed estimated revenue at
  home electricity rates. This is genuinely how small-scale CPU mining
  economics look; MacMine Lab won't sugarcoat the number.

## Roadmap

See `CHANGELOG.md` for what's shipped. Upcoming, in order: thermal/battery
automation and the experiment journal (Phase 6), then P2Pool (Phase 7).
