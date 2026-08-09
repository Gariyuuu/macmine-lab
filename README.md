# MacMine Lab

A local, transparent Monero (XMR) / RandomX mining laboratory for Apple
Silicon Macs. Built to learn how proof-of-work mining actually works, watch
real hashing happen on your own hardware, and — eventually — earn your
first few cents of real cryptocurrency.

## What this is

- A CLI (and, in later phases, a local dashboard) that runs the real
  [XMRig](https://xmrig.com) miner on **your Mac**, under **your control**.
- Fully local: no cloud account, no remote database, nothing leaves your
  machine except, once real mining is configured, the RandomX work you
  choose to submit to a pool you configure yourself.
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

## Current status: Phase 2 of 7

- ✅ **Phase 1** — Apple Silicon hardware detection, live telemetry, XMRig
  install/verification via Homebrew, fully-offline duration-controlled
  RandomX benchmarking, thread calibration, hard verified STOP.
- ✅ **Phase 2** — local FastAPI backend (127.0.0.1 only) with SQLite
  persistence: benchmark runs, telemetry history, and miner integrity are
  now stored in `data/macmine.db` instead of flat JSON files. A background
  sampler records telemetry every 8 seconds. REST endpoints for hardware,
  live/historical telemetry, miner status/stop, and starting/reading
  benchmarks; a `/ws/live` WebSocket pushes real telemetry + miner + active
  benchmark state once per second for whatever frontend eventually connects.

**Not yet built:** the Next.js dashboard, real pool/wallet mining, First
Penny tracking, and thermal/battery automation. Those are Phases 3–7. This
README will be updated as each phase lands — see `CHANGELOG.md`.

## Quick start

```bash
cd macmine-lab
./setup.sh
./macmine hardware
./macmine benchmark --duration 30
```

`setup.sh` checks for macOS + Apple Silicon, ensures Python 3.11 (arm64) and
`uv` are available (installing them via Homebrew if missing — Homebrew
itself is never auto-installed), creates an isolated virtualenv at
`backend/.venv`, and installs/verifies XMRig via Homebrew.

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
WS   /ws/live                         # telemetry + miner + benchmark state, 1x/second
```

All benchmark/telemetry/integrity data now lives in `data/macmine.db`
(SQLite) rather than the flat JSON files Phase 1 used — the CLI and the API
server read and write the same database, so `./macmine benchmark` and
`./macmine setup` results show up immediately through the API too.

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
(SQLite — benchmark runs, telemetry history, miner integrity records),
`data/logs/` (raw XMRig output), `data/run/` (the current PID file, if
anything is running), `data/integrity/` (a human-readable snapshot of the
latest integrity check). Nothing is uploaded anywhere. There is no
authentication because there is nothing to authenticate against — the API
server only ever binds to 127.0.0.1.

## Troubleshooting

- **"MacMine Lab isn't set up yet"** — run `./setup.sh`.
- **"xmrig is not installed"** — run `./macmine setup`, or `brew install xmrig`
  directly.
- **Benchmark shows "Unavailable" for hashrate** — the run was likely too
  short relative to RandomX's dataset warmup; try `--duration 60`.
- **Homebrew not found** — install it yourself from https://brew.sh; MacMine
  Lab deliberately does not install Homebrew on your behalf.

## Roadmap

See `CHANGELOG.md` for what's shipped. Upcoming, in order: the Next.js
dashboard (Phase 3), real wallet/pool mining with accepted/rejected shares
(Phase 4), First Penny tracking and live price/earnings estimates (Phase 5),
thermal/battery automation and the experiment journal (Phase 6), then
P2Pool (Phase 7).
