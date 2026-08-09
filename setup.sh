#!/usr/bin/env bash
# MacMine Lab setup — local, visible, no hidden steps.
# This script: checks macOS + Apple Silicon, ensures Python 3.11 (arm64) and
# uv are available, creates an isolated venv, installs MacMine Lab's own
# (dependency-free) backend package, then installs/verifies XMRig via
# Homebrew. It never touches sudo and never installs Homebrew itself.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== MacMine Lab setup ==="

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "MacMine Lab is macOS-only. Detected: $(uname -s)"
  exit 1
fi

ARCH="$(uname -m)"
if [[ "$ARCH" != "arm64" ]]; then
  echo "WARNING: detected architecture '$ARCH', not arm64. MacMine Lab targets"
  echo "Apple Silicon; things may still work but are untested on this arch."
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required (for XMRig and Python) but was not found."
  echo "Install it yourself first: https://brew.sh"
  echo "MacMine Lab will not install Homebrew for you."
  exit 1
fi
echo "Homebrew: found at $(command -v brew)"

if ! brew list --formula python@3.11 >/dev/null 2>&1 && ! command -v python3.11 >/dev/null 2>&1; then
  echo "Installing Python 3.11 (arm64, via Homebrew)..."
  brew install python@3.11
else
  echo "Python 3.11: already available"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv (Python venv/package manager, via Homebrew)..."
  brew install uv
else
  echo "uv: found at $(command -v uv)"
fi

echo "Creating isolated virtual environment at backend/.venv ..."
cd "$SCRIPT_DIR/backend"
uv venv --python 3.11 .venv --allow-existing
uv pip install --python .venv/bin/python -e .

cd "$SCRIPT_DIR"
mkdir -p data/benchmarks data/logs data/run data/integrity

echo
echo "Installing/verifying XMRig via Homebrew..."
./macmine setup

echo
echo "Setup complete. Try:"
echo "  ./macmine hardware"
echo "  ./macmine benchmark --duration 30"
