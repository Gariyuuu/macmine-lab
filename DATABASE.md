# MacMine Lab — Database

SQLite, single file at `data/macmine.db`, gitignored (real local user
data, not fixtures). Accessed through `backend/macmine_lab/db.py`. No
ORM — direct SQL. No migrations tooling; schema changes are applied by
editing `db.py`'s `CREATE TABLE` statements (confirmed by reading the
schema directly, not inferred).

## Tables [Verified 2026-08-17, read directly from `data/macmine.db`]

- **`benchmark_runs`** — one row per benchmark: threads, target/actual
  duration, avg/peak/low hashrate, hashes-per-thread, final thermal
  state, stop reason, full hashrate/telemetry sample arrays as JSON text
  columns. 8 real rows as of this pass.
- **`telemetry_samples`** — background sampler output (every 8s): CPU
  user/sys/idle, load average, memory, battery, AC power, thermal state,
  whether a miner was running and its CPU%.
- **`miner_installations`** — XMRig integrity record: installed flag,
  binary path, version, architecture, SHA-256, install source, upstream
  project, verification method, checked-at timestamp.
- **`app_settings`** — generic key/value store (electricity rate, power
  draw estimate, safety automation toggles, etc. — inferred from
  README's settings endpoints, not enumerated key-by-key here).
- **`wallets`** — `address`, optional `label`, `address_kind`
  (standard/subaddress/integrated). No seed/private/spend key column —
  deliberate, per CLAUDE.md rule 8. 1 real row (synthetic test address
  per `showcase/api/guide.js`'s own description — not a live payout
  wallet as of this pass).
- **`pools`** — `name`, `host`, `port`, `tls`, optional `worker_name`/
  `password`/`notes`. 1 real row, "Local Test Pool" at
  `127.0.0.1:19999`, no password set — a local test stratum, not a real
  pool.
- **`mining_sessions`** — real-mining runs: `pool_id`/`wallet_id`
  (FKs), threads, start/end, duration, avg/peak hashrate, good/total
  shares, total hashes, stop reason, hashrate samples JSON. 1 row: 12
  threads, 13.7s, 0/0 shares (too short/local to register any).
- **`price_snapshots`** — cached CoinGecko XMR/USD price + source +
  fetch time (5 min cache per README).
- **`network_snapshots`** — cached xmrchain.net difficulty/hash rate/
  block reward/block time/height + source + fetch time (150s cache).
- **`achievements`** — `key` (PK) + `unlocked_at`. First Penny
  achievement system.

No user accounts, no auth-related tables — the API has no authentication
at all (binds to 127.0.0.1 only, nothing to authenticate against, per
README's "Data & privacy" section).
