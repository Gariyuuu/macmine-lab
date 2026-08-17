# MacMine Lab — Decisions

Reconstructed from README.md/CHANGELOG.md, which already document most of
this project's real engineering decisions inline — collected here as a
scannable log rather than duplicated in full prose. Decision text is
`[Verified]` (README states it directly); reasoning is `[Inferred]` where
this pass is reading intent rather than an explicit stated "why."

## D-001 — No shipped pool presets
**Decision:** MacMine Lab never ships a default pool (SupportXMR,
HashVault, etc.) — users add their own via CRUD. **Reason** [Verified,
README]: candidate pools' connection details are served from JS-rendered
pages that couldn't be fetched reliably, so a hardcoded host:port
couldn't be verified as current. Shipping the CRUD and leaving it to the
user was chosen over hardcoding a value that might already be stale.

## D-002 — Wallet validation is format-only, not checksum
**Decision:** Address validation checks base58 charset/length/prefix,
not a full checksum. **Reason** [Inferred]: catches typos cheaply without
needing Monero's actual checksum algorithm implemented client-side; the
gap is disclosed on-screen rather than silently overclaiming
verification.

## D-003 — XMRig logs must use `--log-file`, not redirected stdout
**Decision:** Switched from redirecting XMRig's stdout to a file, to
using its own `--log-file` flag. **Reason** [Verified, README Phase 3]:
XMRig fully buffers stdout once detached from a terminal, so every
redirected log came out 0 bytes on SIGTERM (buffered data lost before
flush). `--log-file` flushes per-line.

## D-004 — Explicit reaping for monerod/p2pool child processes
**Decision:** Added `os.waitpid(pid, os.WNOHANG)` reaping for
monerod/p2pool. **Reason** [Verified, README Phase 7]: unlike XMRig
(actively polled via `proc.poll()` in the benchmark loop), nothing
reaped these processes, so a crashed process still showed "running" to a
`ps`-based liveness check indefinitely — found by deliberately triggering
a P2Pool crash with an invalid wallet address during testing.

## D-005 — P2Pool blockchain sync requires an explicit, restated-cost gate
**Decision:** The only action in the project that requires a dedicated
confirmation step beyond a normal button click. **Reason** [Verified,
README]: it's a real tens-to-hundreds-of-GB download that "may take hours
to days" — every other action in the project was judged not to warrant
this friction, making this a deliberate, singular exception rather than a
project-wide pattern.

## D-006 — CRITICAL thermal stop cannot be disabled
**Decision:** The CRITICAL thermal-safety stop is a hard floor,
independent of the general safety-automation toggle. **Reason**
[Verified, README]: stated project stance "against ever bypassing thermal
protection" — a deliberate, non-negotiable line even for a project that
otherwise gives the user configuration control (battery threshold,
automation on/off, allow-mining-on-battery).

## D-007 — Benchmark mode never adjusts thread count live on HOT
**Decision:** HOT thermal state auto-reduces thread count for real
mining, but is notification-only for benchmarks. **Reason** [Verified,
README]: a benchmark's fixed short duration and single-shot API contract
made live reconfiguration "more engineering risk than it was worth" — an
explicit scope limit, not an oversight.

## D-008 — No power-draw-vs-hashrate chart in Analytics
**Decision:** `/analytics` deliberately omits this one correlation.
**Reason** [Verified, README]: power draw is a single user-entered
constant, not a per-run measurement — plotting it against hashrate would
imply a measured relationship that doesn't exist.

## D-009 — "First Payout" achievement can never auto-unlock
**Decision:** Stays permanently locked with an explanation rather than
being inferred from mining-session data. **Reason** [Verified, README]:
MacMine Lab has no way to verify an actual pool balance/wallet balance in
this version — the estimated-earnings dollar figure is explicitly not
the same thing as a confirmed payout, and the project chose not to blur
that line even at the cost of a permanently-locked achievement.

## D-010 — PGP signature on P2Pool release not independently verified
**Decision:** Only SHA-256 is checked against the project's checksums
file; the GPG signature on that file is not verified. **Reason**
[Verified, README]: no `gpg` dependency was added for this — the
integrity record says so honestly rather than overclaiming full chain-of-
trust verification.
