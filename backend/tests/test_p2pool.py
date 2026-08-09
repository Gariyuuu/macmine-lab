"""Tests for P2Pool install/verify/process-management. The checksums-file
fixture below is the REAL sha256sums.txt.asc content fetched from
SChernykh/p2pool's v4.18 release during development (see CHANGELOG) — not
a made-up format. Real end-to-end download+verify+install was also run
manually against the live GitHub release; these tests mock network calls
to stay fast and to test failure paths (e.g. checksum mismatch) that would
be awkward to trigger against the real server."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from macmine_lab import p2pool, paths

REAL_CHECKSUMS_TEXT = """-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

Name: p2pool-v4.18-freebsd-aarch64.tar.gz
Size: 4508104 bytes : 4402 KiB
SHA256: 40f1191cc2421010f104a9392231e8e58f4177bc651546cfed43873a18019953

Name: p2pool-v4.18-linux-x64.tar.gz
Size: 4869077 bytes : 4754 KiB
SHA256: 893691726b0218fe1883a7a326e2c69db4eb228fc72ba00c8adfa6be85b8a415

Name: p2pool-v4.18-macos-aarch64.tar.gz
Size: 4564774 bytes : 4457 KiB
SHA256: b9b6abae4380fb3adde0696e5a8edc40f88783f685e210668b9386f07ddba856

Name: p2pool-v4.18-macos-x64.tar.gz
Size: 4875535 bytes : 4761 KiB
SHA256: a62be84b6ca4e4e980ab4b1785a6bc191d5eed15621f0777d3e91008457e8532
-----BEGIN PGP SIGNATURE-----

iQIzBAEBCgAdFiEEH8qrTT3DMQ0Wy9UIxH+CtU2oet8FAmpzCLkACgkQxH+CtU2o
-----END PGP SIGNATURE-----
"""


@pytest.fixture
def isolated_pidfile(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUN_DIR", tmp_path)
    monkeypatch.setattr(paths, "P2POOL_PID_FILE", tmp_path / "p2pool.pid")
    return tmp_path / "p2pool.pid"


def test_expected_sha256_parses_real_checksums_format():
    result = p2pool._expected_sha256(REAL_CHECKSUMS_TEXT, "p2pool-v4.18-macos-aarch64.tar.gz")
    assert result == "b9b6abae4380fb3adde0696e5a8edc40f88783f685e210668b9386f07ddba856"


def test_expected_sha256_returns_none_for_unknown_asset():
    result = p2pool._expected_sha256(REAL_CHECKSUMS_TEXT, "p2pool-v4.18-solaris-sparc64.tar.gz")
    assert result is None


def test_expected_sha256_does_not_confuse_similarly_named_assets():
    # macos-x64 vs macos-aarch64 share a prefix — must not cross-match.
    result = p2pool._expected_sha256(REAL_CHECKSUMS_TEXT, "p2pool-v4.18-macos-x64.tar.gz")
    assert result == "a62be84b6ca4e4e980ab4b1785a6bc191d5eed15621f0777d3e91008457e8532"


def test_fetch_latest_release_parses_real_github_api_shape():
    fake_api_response = {
        "tag_name": "v4.18",
        "assets": [
            {"name": "p2pool-v4.18-linux-x64.tar.gz", "browser_download_url": "https://x/linux", "size": 100},
            {"name": "p2pool-v4.18-macos-aarch64.tar.gz", "browser_download_url": "https://x/macos-arm", "size": 4564774},
            {"name": "sha256sums.txt.asc", "browser_download_url": "https://x/sums", "size": 10},
        ],
    }
    mock_resp = MagicMock()
    import json
    mock_resp.read.return_value = json.dumps(fake_api_response).encode()
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        release = p2pool.fetch_latest_release()

    assert release.version == "v4.18"
    assert release.asset_name == "p2pool-v4.18-macos-aarch64.tar.gz"
    assert release.asset_url == "https://x/macos-arm"
    assert release.checksums_url == "https://x/sums"


def test_fetch_latest_release_returns_none_on_network_failure():
    with patch("urllib.request.urlopen", side_effect=OSError("no network")):
        assert p2pool.fetch_latest_release() is None


def test_install_rejects_checksum_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "BIN_DIR", tmp_path / "bin")
    monkeypatch.setattr(paths, "P2POOL_BINARY", tmp_path / "bin" / "p2pool")

    fake_release = p2pool.ReleaseInfo(
        version="v4.18", asset_name="p2pool-v4.18-macos-aarch64.tar.gz",
        asset_url="https://x/asset", checksums_url="https://x/sums", asset_size_bytes=100,
    )

    archive_resp = MagicMock()
    archive_resp.read.return_value = b"not the real binary content"
    archive_resp.__enter__.return_value = archive_resp
    checksums_resp = MagicMock()
    checksums_resp.read.return_value = REAL_CHECKSUMS_TEXT.encode()
    checksums_resp.__enter__.return_value = checksums_resp

    with patch.object(p2pool, "fetch_latest_release", return_value=fake_release), \
         patch("urllib.request.urlopen", side_effect=[archive_resp, checksums_resp]):
        ok, message = p2pool.install()

    assert ok is False
    assert "mismatch" in message.lower()
    assert not paths.P2POOL_BINARY.exists()


def test_install_fails_cleanly_when_release_lookup_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "BIN_DIR", tmp_path / "bin")
    with patch.object(p2pool, "fetch_latest_release", return_value=None):
        ok, message = p2pool.install()
    assert ok is False
    assert "GitHub" in message or "release" in message.lower()


def test_is_tracked_process_alive_none_when_no_pidfile(isolated_pidfile):
    assert p2pool.is_tracked_process_alive() is None


def test_is_tracked_process_alive_clears_stale_pidfile(isolated_pidfile):
    isolated_pidfile.write_text("999999")
    assert p2pool.is_tracked_process_alive() is None
    assert not isolated_pidfile.exists()


def test_stop_refuses_to_kill_non_p2pool_process(isolated_pidfile):
    proc = subprocess.Popen(["sleep", "30"])
    isolated_pidfile.write_text(str(proc.pid))
    try:
        result = p2pool.stop()
        assert result is True
        assert proc.poll() is None
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_is_tracked_process_alive_reaps_exited_child_promptly(tmp_path, isolated_pidfile):
    """Regression test: a real process (named 'p2pool' so it passes the
    name-match check) that exits almost immediately after launch must be
    detected as not-alive right away — not eventually. This is the exact
    bug found manually: is_tracked_process_alive() reported a crashed
    p2pool process as "running" because nothing reaped its zombie, and
    `ps` kept reporting the zombie's command name as still matching."""
    fake_binary = tmp_path / "p2pool"
    fake_binary.write_text("#!/bin/sh\nexit 1\n")
    fake_binary.chmod(0o755)

    proc = subprocess.Popen([str(fake_binary)])
    proc.wait(timeout=5)  # ensure it has genuinely exited before we check
    isolated_pidfile.write_text(str(proc.pid))

    assert p2pool.is_tracked_process_alive() is None
    assert not isolated_pidfile.exists()


def test_pidfile_roundtrip_includes_stratum_port(isolated_pidfile):
    paths.P2POOL_PID_FILE.write_text("12345|4444")
    assert p2pool._read_pidfile() == (12345, 4444)


def test_pidfile_roundtrip_handles_legacy_bare_pid_format(isolated_pidfile):
    # Backward-compat: a pidfile written before stratum-port tracking existed.
    paths.P2POOL_PID_FILE.write_text("12345")
    assert p2pool._read_pidfile() == (12345, None)


def test_get_status_reports_real_stratum_port_after_launch(isolated_pidfile):
    with patch.object(p2pool, "is_tracked_process_alive", return_value=4242):
        paths.P2POOL_PID_FILE.write_text("4242|4444")
        status = p2pool.get_status()
    assert status.running is True
    assert status.pid == 4242
    assert status.stratum_port == 4444


def test_launch_rejects_invalid_mode():
    with pytest.raises(ValueError):
        p2pool.launch("4" + "x" * 94, "invalid-mode", "/tmp/x", 18081, 18083)


def test_verify_installed_when_binary_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "P2POOL_BINARY", tmp_path / "does-not-exist")
    record = p2pool.verify_installed()
    assert record.installed is False


def test_get_status_not_running(isolated_pidfile):
    status = p2pool.get_status()
    assert status.running is False
