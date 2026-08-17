# MacMine Lab — Features

README.md's "Current status: Phase 7 of 7 — complete" section already
gives the real, detailed, phase-by-phase breakdown — this file adds only
a top-level classification, not a duplicate narrative.

| Feature | Status | Note |
|---|---|---|
| Hardware detection + telemetry | Verified complete | Live, real `pmset`/CPU/RAM reads. |
| RandomX benchmarking | Verified complete | Real XMRig, self-enforced duration, no external network calls during a run (verified via `lsof -i`). |
| SQLite persistence + REST/WebSocket API | Verified complete | 180 backend tests pass. |
| Dashboard (Next.js) | Verified complete, mechanism | Wired to real backend data; no automated tests. |
| Real XMR mining (wallet/pool/mining control) | Mechanism verified, real payout unverified | Only exercised against a local test pool so far — see PROJECT_STATE.md. |
| First Penny / Earnings estimates | Verified complete | Real cached price/network data; dollar figures explicitly labeled estimates. |
| Thermal/battery safety automation | Verified complete | CRITICAL stop is a non-disableable hard floor. |
| Experiment Journal / Analytics | Verified complete | Real-correlation-only; "not enough data" is a real state, not a placeholder. |
| P2Pool decentralized mining | Mechanism verified, full sync unverified | `monerod`/`p2pool` install+control real; no full blockchain sync has run in this environment (`data/monerod-chain/` absent). |
| Showcase/guide site | Verified live | Separate Vercel deploy, confirmed 200 via curl 2026-08-17. |
| Automated frontend tests | Not built | Zero test files, no `test` script. |
| Packaged `.app` build | Planned, not started | Listed in README's Roadmap as a possible future direction. |
| Additional coins beyond Monero | Planned, not started | Same. |
