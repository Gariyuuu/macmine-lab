# Changelog

## v0.4.0 — Real Mining (Phase 4)

Real XMR pool mining: wallet configuration, pool configuration, and live
accepted/rejected shares. MacMine Lab still never touches a seed phrase or
private key, and takes 0% of anything mined.

Added:
- `wallet.py`: local Monero address format validation (base58 charset,
  length, standard/subaddress/integrated prefix) — format-only, not a full
  checksum verification, and documented as such everywhere it's shown.
- `pools.py`: pool connection testing — a plain TCP (and TLS-handshake for
  TLS pools) reachability check against a host:port. Deliberately does not
  speak the Stratum mining protocol or send a wallet address; whether a
  wallet+pool combination actually works is only provable by mining, which
  is what the live accepted/rejected share counts show.
- `mining.py` / `mining_runner.py`: real, indefinite-duration XMRig pool
  mining (mirrors `benchmark.py`/`runner.py`'s structure, but driven by a
  `threading.Event` instead of a fixed duration). Tracks live hashrate and
  `results.shares_good`/`shares_total` from XMRig's HTTP API, same as
  benchmark mode's polling approach.
- SQLite: `wallets`, `pools`, `mining_sessions` tables + full CRUD.
- `xmrig_api.py`: extracted the local-HTTP-API polling helpers (free port,
  token, fetch summary) that benchmark.py had inline, so mining.py reuses
  them instead of duplicating.
- REST: `/api/wallets*`, `/api/pools*`, `/api/mining*` (see README for the
  full list). `/ws/live` now also streams mining state.
- Frontend: `/setup` page (permanent seed-phrase warning, live-validated
  wallet form, pool form with a connection-test button) and a "Real Mining"
  panel on the dashboard (wallet/pool/thread selection, start/stop, live
  accepted/rejected shares). The hero metric and top bar now distinguish
  MINING from BENCHMARKING from IDLE.
- 32 new backend tests (wallet validation against real address-shape edge
  cases, pool connection tests against a real local TCP server — not
  mocked, mining-session DB lifecycle, and the new API endpoints) — 73
  total, all passing.

Findings from this phase:
- Tried to ship verified real pool presets (SupportXMR, HashVault) with
  current fee/host/port — both pools' sites are JS-rendered and WebFetch
  couldn't extract reliable connection details, and secondary sources
  disagreed on ports. Rather than hardcode something unverified, shipped
  full pool CRUD with **no preset** — exactly the "provide a mechanism to
  add/edit pools, don't hardcode credentials" behavior the project's own
  ground rules call for.
- `xmrig --dry-run` (initially planned for the connection test) turned out
  to be pure local config validation — confirmed by timing it against both
  a real pool hostname and a nonexistent one: both returned in ~14ms,
  meaning it never touches the network. Switched the connection test to a
  real socket-level check instead.
- Real Base UI gotcha (this project's shadcn `Select` uses `@base-ui/react`,
  not Radix): `Select.Value` does **not** auto-resolve to the matching
  `SelectItem`'s label the way Radix's does — it needs an explicit
  `children` render-prop (`(value) => label`). Found by actually reading
  the dashboard's rendered text in a browser test, where every dropdown
  (including ones from Phase 3) was silently showing the raw stored value
  ("1", "30") instead of its label. Fixed in all four dropdowns.
- Full end-to-end proof, verified manually: ran the real Setup → Dashboard
  flow in a browser (Playwright), validated an intentionally-bad address
  and a correctly-shaped one, ran a real connection test against a local
  test TCP server, saved a wallet and pool, then clicked **Start Mining**
  for real — XMRig launched with the saved pool/wallet (log confirms
  `POOL #1 127.0.0.1:<port>` and `DONATE 1%`, the real mining-mode donate
  level vs. benchmark mode's 0%), STOP cleanly terminated it, and the
  session landed in `mining_sessions` with `stopped_reason: "manual"` and
  accurate (zero, since the test pool never issued a job) share counts. No
  orphaned process afterward. A real pool was intentionally *not* used for
  this test, to avoid mining real value to an address invented for testing
  rather than provided by the user — real pool/wallet mining is a
  user-initiated action with the user's own address.

Not yet built: First Penny tracking, live price/earnings estimates,
thermal/battery automation, P2Pool. Phases 5–7.

## v0.3.0 — Mining Dashboard (Phase 3)

Added the Next.js + TypeScript + Tailwind + shadcn/ui dashboard at
`frontend/`, wired to the Phase 2 backend with no mock/placeholder data
anywhere.

Added:
- `frontend/`: dark command-center dashboard — hero hashrate metric (live
  during a benchmark, last-run average when idle), a live recharts hashrate
  chart, a system health panel (CPU, memory, battery, thermal state via the
  `ThermalBadge` component), benchmark start/stop controls (thread + duration
  selects), a real XMRig log terminal, and a recent-runs history table.
  Explicitly never shows a "MINING" state or XMR/USD figures — that's
  Phase 4; this dashboard is honest that it's benchmark mode only.
- `useLiveSocket` hook: reconnecting-with-backoff WebSocket client for
  `/ws/live`. Callers pass an `onPayload` callback invoked inside the real
  `onmessage` handler (not a `useEffect` reacting to state) so derived state
  like chart-point accumulation doesn't trigger React's
  cascading-render lint warnings — this is a real fix, not a suppression.
- `GET /api/logs/latest` (backend): tails the most recently written XMRig
  log file.
- `./dev.sh`: runs the backend and dashboard together for local development.

Fixed (found via actually driving the dashboard in a real browser with
Playwright, not just unit tests):
- **CORS**: the backend originally only allowlisted `localhost:3000`, but
  Next.js silently falls back to another port whenever 3000 is taken (it
  was, by an unrelated project on this Mac) — every REST call from the
  browser failed with no visible error banner (hardware/history/logs
  silently stayed empty). Fixed by matching any `localhost`/`127.0.0.1`
  origin/port via `allow_origin_regex`, which is safe here since neither
  end of this app ever leaves the Mac.
- **Silent log loss (real bug, present since Phase 1)**: every XMRig log
  file MacMine Lab ever wrote came out **0 bytes**. XMRig fully-buffers
  stdout once it isn't a TTY, and `miner.stop()`'s SIGTERM discards
  whatever was still buffered instead of flushing it. Fixed by using
  XMRig's own `--log-file` flag (which flushes each line itself) instead of
  redirecting stdout to a file; stderr, used for crash diagnostics, was
  never affected since C's stderr is unbuffered by default. Verified with a
  direct before/after comparison: the old approach produced a 0-byte file
  after a live run, the new one produced real, readable XMRig output
  mid-run.

Verified manually this phase: installed Playwright into an isolated
scratch directory, drove a real headless Chromium against the dev server,
confirmed zero console errors, screenshotted both the idle and
actively-benchmarking states, and watched real hashrate/CPU/log data flow
through the full stack (backend → SQLite/WebSocket → browser) end to end.

Not yet built: real wallet/pool mining, First Penny tracking,
thermal/battery automation, P2Pool. Phases 4–7.

## v0.2.0 — Local Backend & SQLite (Phase 2)

Added a local-only FastAPI backend and moved persistence from flat JSON
files to SQLite so the CLI and a future dashboard share one source of truth.

Added:
- `data/macmine.db` (SQLite): `benchmark_runs`, `telemetry_samples`,
  `miner_installations`, `app_settings` tables. `benchmark.py` and
  `integrity.py` now write here instead of per-run JSON files.
- Background telemetry sampler (`api.py`): records CPU/memory/battery/thermal
  + miner status every 8 seconds while the server runs, with a 7-day
  retention prune on every insert so the table doesn't grow unbounded.
- `./macmine serve` (default `127.0.0.1:8834`, chosen after discovering an
  unrelated process on this machine already using 8765): REST endpoints for
  hardware, live/historical telemetry, miner status/stop, and starting/
  reading benchmark runs, plus a `/ws/live` WebSocket pushing real telemetry
  + miner + benchmark state once per second.
- `benchmark.run_benchmark` gained an `on_sample` callback so a running
  benchmark's live hashrate is observable in real time (via
  `/api/benchmark/live` or the WebSocket), not just after it finishes.
- 19 new tests: SQLite CRUD/retention (`test_db.py`) and API endpoints
  including a live WebSocket round-trip (`test_api.py`) — 39 total, all
  passing. Automated tests mock the actual XMRig launch; the real
  launch-through-API path was verified manually (see below).

Verified manually this phase:
- Started the real server, drove every REST endpoint with `curl` against
  live data, and connected a real `websockets` client to `/ws/live` and
  printed real per-second payloads.
- Triggered a real 30s/4-thread benchmark through `POST /api/benchmark/start`
  (not mocked): watched live hashrate appear mid-run via
  `/api/benchmark/live` (~2.3 kH/s), confirmed the finished run persisted to
  SQLite and was retrievable via `/api/benchmark/history` and
  `/api/benchmark/{id}`, and confirmed zero orphaned `xmrig` processes
  afterward.
- Confirmed the CLI and the API server share the same live database: running
  `./macmine setup` in a separate process was immediately visible via
  `GET /api/integrity`.

Not yet built: the Next.js dashboard, real wallet/pool mining, First Penny
tracking, thermal/battery automation, P2Pool. Phases 3–7.

## v0.1.0 — Benchmark Engine (Phase 1)

Initial release. Proves genuine RandomX hashing works end-to-end on Apple
Silicon before any dashboard or real mining is built.

Added:
- Apple Silicon hardware detection (`macmine hardware`): chip, performance/
  efficiency core split, RAM, macOS version, architecture, Rosetta detection.
- Live telemetry: CPU usage, load average, memory, battery %/charging/AC
  power, thermal state (derived from `pmset -g therm`'s real
  `CPU_Speed_Limit` field — macOS exposes no numeric temperature, so we
  don't invent one).
- XMRig installation via Homebrew (`macmine setup`) with independent SHA-256
  verification recorded to `data/integrity/miner_integrity.json`
  (`macmine integrity`).
- Fully offline, duration-controlled RandomX benchmarking (`macmine
  benchmark --duration 30|60|300`) using `xmrig --bench` + local HTTP API
  polling — verified to make zero outbound network connections during a run.
- Thread calibration (`macmine calibrate`): benchmarks multiple thread
  counts and recommends Eco/Balanced/Performance configs from measured
  results only (never assumes more threads = better).
- Process management with a hard, verified STOP (`macmine status`,
  `macmine stop`): PID-tracked, re-verifies the process is actually `xmrig`
  before signaling, SIGTERM → SIGKILL fallback, no orphaned processes.
- 20 unit tests covering telemetry parsing (real captured `pmset`/`top`
  output as fixtures), benchmark aggregation math, and the STOP safety
  guarantee (refuses to signal a non-xmrig process even if a stale PID file
  points at one).

Verified manually during this phase (see README for details):
- `xmrig --bench=10M` is genuinely offline; `xmrig --stress` is not (it dials
  `randomx.xmrig.com` by default) — `--stress` is excluded from MacMine
  Lab's benchmark mode for that reason.
- A real 30s benchmark on an Apple M4 Pro (12 threads) measured ~4.9 kH/s
  average, with the process fully and cleanly stopped afterward (no orphan
  `xmrig` process left running).

Not yet built: FastAPI backend, SQLite persistence, Next.js dashboard, real
wallet/pool mining, First Penny tracking, thermal/battery automation,
P2Pool. These are Phases 2–7.
