# MacMine Lab — Tasks

Status legend: Done / In Progress / Planned / Blocked.

## Current task

**T-001 — idle, no active task queued.** [Verified 2026-08-17] All 7
planned phases (README.md's "Current status" section) are complete and
committed. There is no in-progress work; the tree is clean. Next session
should ask the repo owner what they want next rather than inventing
scope — see "Also outstanding" below and README's own "Roadmap" section
for the honest list of possible future directions (not committed to): a
packaged `.app` build, additional coins beyond Monero, and P2Pool's
`--local-api` stats once verified against a real running instance with a
real wallet address.

## Also outstanding (real gaps, not phase work)

- **Zero frontend tests.** `frontend/package.json` has no `test` script,
  no `*.test.tsx` files exist. Backend has 180 passing tests
  (`cd backend && python -m pytest -q`); frontend has none.
- **Real mining has only been exercised against a local test pool**
  (`Local Test Pool`, 127.0.0.1:19999), one 13.7s session, 0 shares —
  README's Phase 4/First Penny features are implemented and this proves
  the plumbing works end-to-end, but no real payout-pool mining or actual
  earned XMR has happened yet in this environment's data.
- The PGP signature on P2Pool's release checksums is not independently
  verified (no `gpg` dependency added) — the integrity record says so
  honestly, per README, but it remains a real (documented, accepted)
  verification gap.
- `showcase/` (the deployed marketing/guide site) is a separate Vercel
  project from the local app — if the guide content or screenshots drift
  from the actual app, nothing currently catches that automatically.
