"""XMRig process lifecycle: launch, track, and guarantee a clean STOP.

MacMine Lab is only ever allowed to run one XMRig process at a time in v0.1.
Every process it launches is recorded in a PID file so that:
  - `macmine stop` / `macmine status` can find it from a fresh CLI invocation
  - we never send a signal to a PID that has been recycled by an unrelated
    process (we check the process name via `ps` before signaling anything)
  - nothing is left orphaned if MacMine Lab itself exits unexpectedly
"""

from __future__ import annotations

import datetime
import os
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import hardware, paths


class XMRigNotInstalledError(RuntimeError):
    pass


class XMRigAlreadyRunningError(RuntimeError):
    pass


@dataclass
class TrackedProcessStatus:
    running: bool
    pid: int | None
    cpu_percent: float | None
    started_at: str | None
    log_file: str | None


def _xmrig_binary() -> str:
    binary = shutil.which("xmrig")
    if not binary:
        raise XMRigNotInstalledError(
            "xmrig is not installed. Run `./macmine setup` or `brew install xmrig` first."
        )
    return binary


def _process_name(pid: int) -> str | None:
    result = subprocess.run(
        ["ps", "-o", "comm=", "-p", str(pid)], capture_output=True, text=True, check=False
    )
    name = result.stdout.strip()
    return name or None


def _read_tracked_pid() -> tuple[int, str] | None:
    if not paths.XMRIG_PID_FILE.exists():
        return None
    try:
        content = paths.XMRIG_PID_FILE.read_text().strip()
        pid_str, _, started_at = content.partition("|")
        return int(pid_str), started_at
    except (ValueError, OSError):
        return None


def _write_tracked_pid(pid: int, started_at: str) -> None:
    paths.ensure_data_dirs()
    paths.XMRIG_PID_FILE.write_text(f"{pid}|{started_at}")


def _clear_tracked_pid() -> None:
    if paths.XMRIG_PID_FILE.exists():
        paths.XMRIG_PID_FILE.unlink()


def is_tracked_process_alive() -> tuple[int, str] | None:
    """Returns (pid, started_at) if a MacMine-launched xmrig is genuinely still running."""
    tracked = _read_tracked_pid()
    if not tracked:
        return None
    pid, started_at = tracked
    name = _process_name(pid)
    if name and "xmrig" in name:
        return pid, started_at
    # Stale pidfile — the PID is dead or was recycled by something else.
    _clear_tracked_pid()
    return None


def launch(extra_args: list[str], log_name: str) -> tuple[subprocess.Popen, Path]:
    """Launch xmrig with the given args, tracked via PID file. Refuses to
    double-launch if MacMine Lab already has a tracked xmrig running."""
    if is_tracked_process_alive():
        raise XMRigAlreadyRunningError(
            "MacMine Lab already has an xmrig process running. Stop it first."
        )

    binary = _xmrig_binary()
    paths.ensure_data_dirs()
    log_path = paths.LOGS_DIR / log_name
    log_file = open(log_path, "w")

    proc = subprocess.Popen(
        [binary, *extra_args],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _write_tracked_pid(proc.pid, started_at)
    return proc, log_path


def stop(pid: int, timeout: float = 5.0) -> bool:
    """SIGTERM, wait, SIGKILL fallback. Returns True if the process is confirmed gone."""
    name = _process_name(pid)
    if not name or "xmrig" not in name:
        # Nothing to do — already gone, or not actually xmrig.
        _clear_tracked_pid()
        return True

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        _clear_tracked_pid()
        return True

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _process_name(pid) is None:
            _clear_tracked_pid()
            return True
        time.sleep(0.2)

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        _clear_tracked_pid()
        return True

    time.sleep(0.5)
    still_alive = _process_name(pid) is not None
    if not still_alive:
        _clear_tracked_pid()
    return not still_alive


def stop_tracked() -> bool:
    """Used by `macmine stop` — stop whatever MacMine-launched xmrig is running."""
    tracked = is_tracked_process_alive()
    if not tracked:
        return True
    pid, _ = tracked
    return stop(pid)


def get_status() -> TrackedProcessStatus:
    tracked = is_tracked_process_alive()
    if not tracked:
        return TrackedProcessStatus(
            running=False, pid=None, cpu_percent=None, started_at=None, log_file=None
        )
    pid, started_at = tracked
    return TrackedProcessStatus(
        running=True,
        pid=pid,
        cpu_percent=hardware.process_cpu_percent(pid),
        started_at=started_at,
        log_file=None,
    )
