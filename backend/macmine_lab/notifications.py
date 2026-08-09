"""Local macOS notifications via `osascript display notification` — no
third-party notification service, nothing leaves this Mac.

Rate-limited per (kind) so repeated triggers (e.g. staying in WARM thermal
state for many consecutive checks) don't spam the user — same kind won't
re-fire within COOLDOWN_S.

Note: on first use, macOS may require the terminal/app that launched
`./macmine serve` to be granted notification permission in System
Settings → Notifications. `send()` returns False (silently, never raises)
if osascript fails for any reason — a missing notification is not treated
as a fatal error anywhere that calls this.
"""

from __future__ import annotations

import subprocess
import time

COOLDOWN_S = 300  # 5 minutes between repeats of the same notification kind

_last_sent: dict[str, float] = {}


def send(title: str, message: str, kind: str, subtitle: str | None = None) -> bool:
    """`kind` is a stable identifier used for rate-limiting (e.g.
    "thermal_warm", "mining_started") — distinct from the human-readable
    title/message, which can vary."""
    now = time.monotonic()
    last = _last_sent.get(kind)
    if last is not None and (now - last) < COOLDOWN_S:
        return False

    script = f'display notification {_osa_string(message)} with title {_osa_string(title)}'
    if subtitle:
        script += f' subtitle {_osa_string(subtitle)}'

    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=5.0, check=False
        )
    except (subprocess.SubprocessError, OSError, TimeoutError):
        return False

    if result.returncode == 0:
        _last_sent[kind] = now
        return True
    return False


def _osa_string(value: str) -> str:
    """Quote a string for embedding in an AppleScript command."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
