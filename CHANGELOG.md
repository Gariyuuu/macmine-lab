# Changelog

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
