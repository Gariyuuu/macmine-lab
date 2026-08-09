"""Tests for monerod process management and status parsing. Real install/
verify against the actual brew-installed binary was run manually (see
CHANGELOG) — these tests mock subprocess/network calls to stay fast and
deterministic, plus cover the safety-critical PID-tracking guarantees."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from macmine_lab import monerod, paths


@pytest.fixture
def isolated_pidfile(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUN_DIR", tmp_path)
    monkeypatch.setattr(paths, "MONEROD_PID_FILE", tmp_path / "monerod.pid")
    return tmp_path / "monerod.pid"


def test_requirements_info_is_a_real_range_not_a_single_fake_number():
    info = monerod.requirements_info()
    assert info.pruned_gb_low < info.pruned_gb_high
    assert info.full_gb_low < info.full_gb_high
    assert info.pruned_gb_high < info.full_gb_low  # pruned genuinely smaller than full
    assert len(info.sources) >= 1


def test_is_tracked_process_alive_none_when_no_pidfile(isolated_pidfile):
    assert monerod.is_tracked_process_alive() is None


def test_is_tracked_process_alive_clears_stale_pidfile(isolated_pidfile):
    isolated_pidfile.write_text("999999")
    assert monerod.is_tracked_process_alive() is None
    assert not isolated_pidfile.exists()


def test_stop_refuses_to_kill_non_monerod_process(isolated_pidfile):
    proc = subprocess.Popen(["sleep", "30"])
    isolated_pidfile.write_text(str(proc.pid))
    try:
        result = monerod.stop()
        assert result is True  # "nothing to do" reported as success
        assert proc.poll() is None  # unrelated process untouched
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_stop_when_nothing_tracked_is_a_noop_success(isolated_pidfile):
    assert monerod.stop() is True


def test_is_tracked_process_alive_reaps_exited_child_promptly(tmp_path, isolated_pidfile):
    """Same bug class as p2pool's regression test: a real 'monerod'-named
    process that exits immediately must be detected as not-alive right
    away, not left as a zombie that `ps` still reports as running."""
    fake_binary = tmp_path / "monerod"
    fake_binary.write_text("#!/bin/sh\nexit 1\n")
    fake_binary.chmod(0o755)

    proc = subprocess.Popen([str(fake_binary)])
    proc.wait(timeout=5)
    isolated_pidfile.write_text(str(proc.pid))

    assert monerod.is_tracked_process_alive() is None
    assert not isolated_pidfile.exists()


def test_get_status_not_running_when_nothing_tracked(isolated_pidfile):
    status = monerod.get_status()
    assert status.running is False
    assert status.height is None


def test_get_status_running_but_rpc_not_ready(isolated_pidfile):
    proc = subprocess.Popen(["sleep", "30"])
    isolated_pidfile.write_text(str(proc.pid))
    try:
        with patch.object(monerod, "_process_name", return_value="monerod"):
            # Nothing listening on this port -> RPC call fails -> honest "running, no data yet"
            status = monerod.get_status(rpc_port=1)
        assert status.running is True
        assert status.pid == proc.pid
        assert status.height is None
        assert status.synchronized is None
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_get_status_parses_real_rpc_shape():
    fake_response = {
        "result": {
            "height": 9828,
            "target_height": 3736291,
            "synchronized": False,
            "database_size": 29196288,
            "free_space": 179747921920,
        }
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response).encode()
    mock_resp.__enter__.return_value = mock_resp

    with patch.object(monerod, "is_tracked_process_alive", return_value=1234), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        status = monerod.get_status()

    assert status.running is True
    assert status.height == 9828
    assert status.target_height == 3736291
    assert status.synchronized is False
    assert status.sync_progress_percent == round(100 * 9828 / 3736291, 2)
    assert status.database_size_gb == round(29196288 / 1e9, 2)


def test_verify_installed_when_binary_missing():
    with patch.object(monerod, "find_monerod_binary", return_value=None):
        record = monerod.verify_installed()
    assert record.installed is False
    assert record.version is None


def test_verify_installed_parses_real_version_string():
    version_output = "Monero 'Fluorine Fermi' (v0.18.5.1-unknown)"
    version_result = MagicMock(stdout=version_output, returncode=0)
    file_result = MagicMock(stdout="monerod: Mach-O 64-bit executable arm64", returncode=0)

    with patch.object(monerod, "find_monerod_binary", return_value="/opt/homebrew/bin/monerod"), \
         patch("subprocess.run", side_effect=[version_result, file_result]), \
         patch.object(monerod, "_sha256_of", return_value="abc123"):
        record = monerod.verify_installed()

    assert record.installed is True
    assert record.version == "0.18.5.1"
    assert record.architecture == "arm64"
    assert record.sha256 == "abc123"
