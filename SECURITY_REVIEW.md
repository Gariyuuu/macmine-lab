# MacMine Lab — Security Review

Named `SECURITY_REVIEW.md`, not `SECURITY.md`, because this repo is
public (confirmed via `gh repo view`, 2026-08-17) and `SECURITY.md` at
root has a reserved GitHub meaning (vulnerability-disclosure policy).
This file is a documentation-pass review, kept at a level safe to
publish — no exploitation roadmap.

## Real, verified security-relevant facts

- Backend binds to `127.0.0.1` only, no authentication layer — README
  states this is intentional (nothing to authenticate against on a
  loopback-only server). Reasonable for a genuinely local-only tool;
  would need real auth if ever bound to `0.0.0.0`.
- No secrets found in the tracked backend/frontend code during this
  pass. `showcase/api/login.js`/`showcase/api/guide.js` read
  `GUIDE_PASSWORD`/`GUIDE_SESSION_TOKEN` from `process.env` only — no
  hardcoded value in the file; `showcase/api/login.js` uses
  `crypto.timingSafeEqual` for the password comparison (avoids a timing
  side-channel).
- Wallet storage has no seed/private/spend-key column — by design
  (CLAUDE.md rule 8) — only public addresses are ever collected.
- Process control (XMRig/monerod/p2pool) always re-verifies PID identity
  via `ps` before signaling, and explicitly reaps child processes — see
  DECISIONS.md D-004. No `sudo` usage found anywhere in this pass.
- P2Pool's binary integrity check is SHA-256-only; the GPG signature on
  the checksums file is not independently verified (DECISIONS.md D-010)
  — an accepted, disclosed gap, not a hidden one.
- XMRig is installed exclusively via Homebrew's official formula
  (bottle checksums validated by Homebrew itself), not a custom binary
  download.

## Not independently verified this pass

- Whether the FastAPI app has any route missing appropriate input
  validation beyond what Pydantic/FastAPI provides by default — this
  pass did not read every handler body.
- Whether `showcase/`'s serverless functions have rate limiting on the
  login endpoint (a brute-force guard on `GUIDE_PASSWORD`) —
  [Needs confirmation], not found in the two files read this pass.
