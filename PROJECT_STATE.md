# MacMine Lab — Project State

**Current task:** T-001 — idle, no active task queued. See TASKS.md.

**Last verified:** 2026-08-17 (this documentation pass). README.md (482
lines) and CHANGELOG.md (user-facing, rendered live in the dashboard's
`/changelog` page) are the project's own comprehensive, current
documentation — this file adds the memory-system fields (current task ID,
verified git/test/data state) without duplicating them.

## Git / repo state [Verified 2026-08-17]

- Branch `main`, latest commit `918fc7f` "Visual polish pass on the
  dashboard and showcase page" (2026-08-11).
- `origin` → `https://github.com/Gariyuuu/macmine-lab.git`, **public**.
  `git log --oneline origin/main` matches local `main` — pushed, up to
  date.
- Working tree clean before this pass.

## What's real and running

- Backend: FastAPI on 127.0.0.1:8834 (no auth — nothing outside the Mac
  can reach it, by design). 180/180 tests pass (`cd backend &&
  python -m pytest -q`, re-run this pass, 48.67s).
- Frontend: Next.js dashboard at `frontend/`, no automated tests.
- `data/macmine.db` (SQLite) has real, non-fixture data: 1 wallet
  (standard-format address), 1 pool (`Local Test Pool`,
  127.0.0.1:19999 — a local test stratum target, not a live payout pool),
  1 mining session (12 threads, 13.7s, 0 shares — too short/local to
  register any), 8 benchmark runs. See DATABASE.md for the schema.
- `showcase/` — a **separate** static site, deployed to Vercel
  (`macmine-lab.vercel.app`, confirmed HTTP 200 on both the root page and
  the guide page via curl during this pass). Vercel project `macmine-lab`
  (`showcase/.vercel/project.json`, correctly gitignored). Has two real
  serverless functions (`showcase/api/login.js`, `showcase/api/guide.js`) gating a
  password-protected guide page via `GUIDE_PASSWORD`/
  `GUIDE_SESSION_TOKEN` env vars (set in Vercel, not found anywhere in
  this repo — no leak).

## What does not work / is unverified

- No real payout-pool mining has happened — only a local test-pool
  session exists in the data. Whether the whole real-mining path works
  end-to-end against an actual pool (SupportXMR, etc.) is therefore
  **[Needs confirmation]** by the repo owner, not proven by this pass.
- P2Pool's PGP signature verification is intentionally not implemented
  (SHA-256 only) — an accepted, documented gap, not a bug.
- Frontend has no automated tests — any UI regression would only be
  caught by manual use.

## Verification performed this pass

- `git log`, `git remote -v`, `git log --oneline origin/main` — pushed,
  up to date, public.
- `cd backend && python -m pytest -q` → 180 passed.
- Queried `data/macmine.db` directly (read-only) to confirm real vs.
  fixture data — did not modify it.
- `curl -s -o /dev/null -w "%{http_code}"` against
  `macmine-lab.vercel.app` and its guide page → both 200.
- `gh repo view Gariyuuu/macmine-lab --json visibility` → PUBLIC.
- Did not run `npm install`/`npm run build`/`npm run dev` for the
  frontend, and did not launch `./macmine serve` or `./dev.sh` — out of
  scope for a documentation-only pass (installs/builds write to the tree;
  launching the real app touches a live mining process).

## Immediate next step for whoever picks this up

None queued — this project is feature-complete per its own roadmap. If
the repo owner wants to resume real mining, README's own "Real mining"
section is the accurate procedure; if they want new scope, start there
rather than guessing from this file.
