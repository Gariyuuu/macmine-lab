"""Safety-critical tests for process tracking and STOP.

The most important property here: MacMine Lab must never signal a PID that
isn't actually an xmrig process, even if that PID happens to be sitting in
our own pidfile (e.g. because it was recycled by the OS after xmrig exited).
"""

import subprocess
import time

import pytest

from macmine_lab import miner, paths


@pytest.fixture
def isolated_pidfile(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUN_DIR", tmp_path)
    monkeypatch.setattr(paths, "XMRIG_PID_FILE", tmp_path / "xmrig.pid")
    return tmp_path / "xmrig.pid"


def test_pidfile_roundtrip(isolated_pidfile):
    miner._write_tracked_pid(4242, "2026-01-01T00:00:00Z")
    pid, started_at = miner._read_tracked_pid()
    assert pid == 4242
    assert started_at == "2026-01-01T00:00:00Z"

    miner._clear_tracked_pid()
    assert miner._read_tracked_pid() is None


def test_read_tracked_pid_when_no_file(isolated_pidfile):
    assert miner._read_tracked_pid() is None


def test_stop_refuses_to_kill_non_xmrig_process(isolated_pidfile):
    """Regression guard: a PID that exists but isn't xmrig must survive."""
    proc = subprocess.Popen(["sleep", "30"])
    try:
        time.sleep(0.3)
        result = miner.stop(proc.pid)
        assert result is True  # "nothing to do" is reported as success
        assert proc.poll() is None  # but the unrelated process is untouched
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_is_tracked_process_alive_clears_stale_pidfile_for_dead_pid(isolated_pidfile):
    # A PID that is essentially guaranteed not to exist.
    miner._write_tracked_pid(999999, "2026-01-01T00:00:00Z")
    assert miner.is_tracked_process_alive() is None
    assert not isolated_pidfile.exists()


def test_stop_on_already_gone_process_is_a_noop_success(isolated_pidfile):
    proc = subprocess.Popen(["sleep", "0.1"])
    proc.wait()
    result = miner.stop(proc.pid)
    assert result is True
