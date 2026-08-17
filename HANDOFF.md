# MacMine Lab — Handoff

Start here. Read in this order:

1. **This file** — onboarding.
2. **README.md** (482 lines) — the real, comprehensive project doc:
   what this is, every command, every REST endpoint, phase-by-phase
   feature detail, troubleshooting. Genuinely worth reading in full; this
   memory system's files add process/state, not competing narrative.
3. **CLAUDE.md** — operating manual, hard rules (never a pool preset,
   never auto-start the P2Pool sync, thermal CRITICAL floor, PID-reaping
   discipline, never store a seed phrase).
4. **TASKS.md** — current task (`T-001`, idle) and real outstanding gaps.
5. **PROJECT_STATE.md** — git state + real data-state snapshot from this
   pass (what's actually in `data/macmine.db`, what's actually live on
   Vercel).
6. Everything else as needed: FILE_MAP.md, ARCHITECTURE.md, DATABASE.md,
   DECISIONS.md, FEATURES.md, API_REFERENCE.md, SECURITY_REVIEW.md,
   TESTING.md, DEPLOYMENT.md, `.env.example`, and CHANGELOG.md (**this
   one is user-facing** — it's rendered live in the dashboard's
   `/changelog` page, don't add internal notes to it).

## What this project is

A local, transparent Monero/RandomX mining laboratory for Apple Silicon
Macs: real XMRig mining under the user's own control, fully local (no
cloud account), honest about what's measured vs. estimated ("Unavailable"
instead of a fabricated number). All 7 planned phases are complete.

## What's committed vs. not

Pushed and up to date (`origin/main` matches local `main` at `918fc7f`).
Public repo. Tree was clean before this documentation pass.

## The one thing worth knowing that isn't obvious from the file tree

This repo contains **two unrelated deployables**: the local-only app
(never hosted anywhere, by design) and `showcase/`, a completely separate
static site + two serverless functions that IS deployed to Vercel
(`macmine-lab.vercel.app`, confirmed live). Don't assume "local-only" 
applies to the whole repo.

## What NOT to do without explicit confirmation

- Don't add a hardcoded pool preset — see DECISIONS.md D-001.
- Don't auto-start or soften the confirmation gate on P2Pool's blockchain
  sync — it's the one deliberately-gated, tens-of-GB action in the
  project.
- Don't weaken or make the CRITICAL thermal stop configurable.
- Don't reset or modify `data/macmine.db` — it has real (if
  test/synthetic wallet/pool) usage history, not disposable fixtures.
- Don't write real secret values into any doc — `GUIDE_PASSWORD`/
  `GUIDE_SESSION_TOKEN` live in Vercel env vars only; none found
  hardcoded anywhere during this pass.

## Prompt for the next Claude Code account

Copy-paste this to start the next session:

```
Read HANDOFF.md, then README.md, then CLAUDE.md, then TASKS.md and
PROJECT_STATE.md, in this local Monero-mining-lab project
(~/Projects/macmine-lab).

Before doing anything else:
1. Run `git status` and `git log --oneline` yourself.
2. Run `cd backend && source .venv/bin/activate && python -m pytest -q`
   and confirm the count matches PROJECT_STATE.md (180 as of 2026-08-17).
3. Remember this repo has two unrelated deployables: the local-only app
   (backend/frontend, never hosted) and showcase/ (a separate static
   site + two serverless functions, live on Vercel). Don't conflate them.
4. Before ending your session: update PROJECT_STATE.md, TASKS.md, and
   append to SESSION_LOG.md. If you touch CHANGELOG.md, remember it's
   user-facing (rendered live in the dashboard) — write it for end users,
   not as an internal dev log.

Do not commit anything you haven't personally verified (tests at
minimum), don't modify data/macmine.db, and don't add a pool preset or
weaken the P2Pool sync confirmation gate without the repo owner's
explicit say-so.
```
