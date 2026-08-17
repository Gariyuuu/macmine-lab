# CLAUDE.md — MacMine Lab

Operating manual. Read HANDOFF.md first for onboarding; this file is
conventions and hard rules for future sessions.

## Current task

**T-001 — idle, no active task queued.** [Verified 2026-08-17] All 7
planned phases are complete and committed (README.md's own "Current
status" section confirms this, matching `git log`). See TASKS.md.

## What this is (one line)

A local, transparent Monero (XMR)/RandomX mining laboratory for Apple
Silicon Macs — CLI + FastAPI backend + Next.js dashboard, fully local, no
cloud account, honest about what it measures vs. estimates. Full detail:
README.md (482 lines, comprehensive and current — read it, don't assume
this file duplicates it).

## Repo facts that are easy to get wrong

- **This is three separate things in one repo**, each with its own
  purpose: `backend/` + `frontend/` are the actual local mining app
  (never deployed anywhere, binds to 127.0.0.1 only, by design). `showcase/`
  is a **separate, static, deployed** marketing/docs site
  (macmine-lab.vercel.app, confirmed live via curl 2026-08-17) — don't
  confuse "the app is local-only" with "nothing about this project is on
  the internet."
- **`showcase/api/login.js` and `showcase/api/guide.js`** are real Vercel serverless
  functions gating a password-protected guide page (`GUIDE_PASSWORD`/
  `GUIDE_SESSION_TOKEN` env vars, set in Vercel, not in this repo) — uses
  `crypto.timingSafeEqual`, no hardcoded secret found in the file.
- **CHANGELOG.md is user-facing**, not an internal dev log —
  `frontend/src/app/changelog/page.tsx` reads it directly from disk and
  renders it in the live dashboard. Don't add a doc-audit entry to it
  (this memory system's own convention); if you need to note this
  documentation pass happened, use SESSION_LOG.md instead.
- **Real user data exists in `data/macmine.db`** as of this pass: 1
  wallet (standard address), 1 pool (`Local Test Pool`, 127.0.0.1:19999 —
  a local test stratum, not a real payout pool), 1 mining session (13.7s,
  0 shares — too short/local to register), 8 benchmark runs. This is real
  usage evidence, not fixture data — don't reset or modify `data/` without
  being asked.
- **180 backend tests pass** (`cd backend && python -m pytest -q`,
  re-run 2026-08-17, 48.67s). **Zero frontend tests exist** — no test
  script in `frontend/package.json`, no `*.test.tsx` files found.
- Public GitHub repo (confirmed via `gh repo view`) — this is why
  security findings live in `SECURITY_REVIEW.md`, not `SECURITY.md` (the
  latter has a GitHub-reserved meaning for public repos).

## Rules that exist for a reason

1. **Never add a hardcoded pool preset.** README explains why: pool
   connection details are served from JS-rendered pages the project
   couldn't reliably verify as current, so shipping a guessed host:port
   was rejected in favor of user-entered CRUD. Don't "helpfully" add
   SupportXMR/HashVault defaults without re-verifying this reasoning
   still holds.
2. **Never auto-start the P2Pool blockchain sync.** `/p2pool`'s "Start
   Node" flow requires an explicit restated-cost confirmation
   (tens–hundreds of GB) before syncing `monerod`. This is the one
   deliberately-gated action in the whole project — don't remove or
   soften that gate.
3. **CRITICAL thermal state always stops mining/benchmarking, no
   exception, not configurable.** `backend/macmine_lab/safety.py`'s hard
   floor. Don't add a
   way to disable it.
4. **PID-based process control always re-verifies identity before
   signaling.** `./macmine stop` and the monerod/p2pool equivalents
   re-check via `ps` that the PID is still actually the expected process
   name before sending a signal — never send a signal to a PID you
   haven't just re-verified.
5. **Reap child processes explicitly.** A real bug (README, Phase 7):
   `monerod`/`p2pool` weren't reaped via `os.waitpid(pid, os.WNOHANG)`,
   so a crashed process looked "running" forever to a `ps`-based check.
   Any new subprocess this project launches needs the same reaping
   discipline XMRig already gets from Phase 1's active `proc.poll()`
   loop.
6. **XMRig log files must use `--log-file`, never redirected stdout.**
   Real bug (README, Phase 3): XMRig fully buffers stdout once detached
   from a terminal, so redirected logs were silently 0 bytes on
   SIGTERM. `--log-file` flushes per-line; stderr is unbuffered by
   default and was never affected.
7. **Never fabricate a measurement.** The project's own stated design
   principle, applied throughout: "Unavailable"/"not enough data" instead
   of a fake number, for hashrate, temperature, power draw, earnings,
   correlations. Keep this invariant in any new feature.
8. **Never ask for or store a seed phrase / private / spend key.** Only
   public wallet addresses are ever collected (`wallets.address`,
   format-validated, not checksum-verified).

## Where to look next

- **README.md** — the real, comprehensive operating doc: full command
  list, full REST API list, phase-by-phase feature detail, troubleshooting.
  This file does not duplicate it.
- **CHANGELOG.md** — user-facing (see above), full phase-by-phase history.
- **TASKS.md** / **PROJECT_STATE.md** — this memory system's queue and
  snapshot.
- **FILE_MAP.md**, **DATABASE.md**, **DECISIONS.md** — this pass's
  additions, real detail not already in README.md.
