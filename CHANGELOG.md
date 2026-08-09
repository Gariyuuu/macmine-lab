# Changelog

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
