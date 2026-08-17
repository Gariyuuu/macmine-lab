# MacMine Lab — Session Log

Append-only. This file starts with this memory system's first pass — the
project's real phase-by-phase history already lives in the (user-facing)
`CHANGELOG.md`. Don't re-derive that history here.

## 2026-08-17 — Repo-memory init pass (documentation only, no application code touched)

Batch repo-memory sweep across several portfolio repos; this entry covers
only this repo. No prior memory files existed at all except README.md and
CHANGELOG.md — no CLAUDE.md, no core five. Cold read, no prior session
notes available for this project.

What was done:
- Wrote CLAUDE.md (new — this repo had none before), TASKS.md,
  PROJECT_STATE.md, HANDOFF.md, this file, FILE_MAP.md, ARCHITECTURE.md,
  DATABASE.md, DECISIONS.md, FEATURES.md, API_REFERENCE.md, UI_SYSTEM.md,
  SECURITY_REVIEW.md (not `SECURITY.md` — repo is public), TESTING.md,
  DEPLOYMENT.md, `.env.example` — all new.
- Gave the current task a stable ID (`T-001`: idle, no active task) and
  cross-referenced it from TASKS.md/PROJECT_STATE.md/HANDOFF.md/
  CLAUDE.md.
- Ran `cd backend && python -m pytest -q`: **180 passed**, 48.67s.
- Read `data/macmine.db` directly (read-only) to ground DATABASE.md/
  PROJECT_STATE.md in real data rather than the schema alone: confirmed
  1 wallet, 1 pool ("Local Test Pool," 127.0.0.1, no password), 1 mining
  session (13.7s, 0 shares), 8 benchmark runs. Cross-checked against
  `showcase/api/guide.js`'s own hardcoded text, which independently
  confirms the wallet/pool are "synthetic test values ... not a real
  address" — consistent with the DB read.
- Confirmed `showcase/` is a separate, live Vercel deployment
  (`curl` → 200 on both the root page and the guide page at
  `macmine-lab.vercel.app`)
  distinct from the local-only backend/frontend app — flagged clearly in
  CLAUDE.md/ARCHITECTURE.md/HANDOFF.md since it's easy to miss from the
  file tree alone.
- Confirmed via `gh repo view` the repo is public, and via
  `git log --oneline origin/main` that it's pushed and up to date at
  `918fc7f`.
- Did not add a doc-audit entry to CHANGELOG.md — confirmed it's
  user-facing (rendered live by `frontend/src/app/changelog/page.tsx`),
  which this memory system's own rules say to treat as off-limits for
  internal notes.
- Did not run `npm install`/`npm run build`/`npm run dev` for the
  frontend, and did not launch `./macmine serve` or `./dev.sh` — out of
  scope for a documentation-only, unattended pass.
- No application code, dependencies, or runtime behavior changed;
  `data/macmine.db` was only read, never written.
- `verify_docs.py`'s path check has one residual, deliberately unfixed
  category: 25 bare-filename references inside pre-existing CHANGELOG.md
  (e.g. `monerod.py`, `safety.py` without their `backend/macmine_lab/`
  prefix). Left alone rather than edited, since CHANGELOG.md is
  user-facing (rendered live in the dashboard) and this memory system's
  own rule is to keep it in end-user voice, not retrofit internal-doc
  path conventions into it. Every other file this pass touched or
  created passes the path check cleanly.
