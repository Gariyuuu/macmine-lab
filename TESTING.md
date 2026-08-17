# MacMine Lab — Testing

## Backend

```bash
cd backend && source .venv/bin/activate && python -m pytest -q
```

Re-run 2026-08-17: **180 passed** in 48.67s (one deprecation warning
about `httpx` under `starlette.testclient`, not a failure). 17 test
files, roughly one per `macmine_lab/` module (`backend/tests/`).
`backend/pyproject.toml`'s `[tool.pytest.ini_options]` sets
`testpaths = ["tests"]`.

Real integration-style tests exist alongside unit tests — e.g. P2Pool's
checksum-verification test uses the actual `sha256sums.txt.asc` content
fetched from a real v4.18 release (per CHANGELOG.md), not a synthetic
fixture.

## Frontend

**No automated tests exist.** No `test` script in `frontend/package.json`,
no `*.test.tsx`/`*.spec.tsx` files found. Only `npm run lint` (eslint) is
available as an automated check.

```bash
cd frontend && npm run lint
```

Not run this pass (would need `npm install` first, which writes to the
tree — out of scope for a documentation-only sweep).

## What's verified by manual testing, not automation

Real hardware/process behavior — thermal automation triggers, P2Pool
process reaping, XMRig log buffering — was found and fixed via actual
live testing during development (see DECISIONS.md), not caught by the
pytest suite alone. This is real, valuable verification, but it isn't
repeatable/regression-proof the way a test file would be.
