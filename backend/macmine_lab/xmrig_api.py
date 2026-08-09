"""Shared helpers for talking to a locally-launched XMRig's HTTP API.

Used by both benchmark.py (offline --bench mode) and mining.py (real pool
mining) — the API shape is identical in both cases, only the pool field
differs ("benchmark:3333" vs. the real configured pool).
"""

from __future__ import annotations

import json
import secrets
import socket
import urllib.error
import urllib.request


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def new_token() -> str:
    return secrets.token_hex(16)


def fetch_summary(port: int, token: str) -> dict | None:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/2/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, ValueError, ConnectionError):
        return None
