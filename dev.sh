#!/usr/bin/env bash
# Runs the local backend and the dashboard together for development.
# Ctrl-C stops both. Neither ever binds beyond 127.0.0.1/localhost.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

cleanup() {
  echo
  echo "Stopping backend + dashboard..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

./macmine serve &
BACKEND_PID=$!

(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "Backend:   http://127.0.0.1:8834"
echo "Dashboard: http://localhost:3000 (or whatever port Next.js picks if 3000 is busy)"
wait
