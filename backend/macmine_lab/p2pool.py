"""P2Pool installation, verification, and process management.

P2Pool has no Homebrew formula, so it's installed by downloading the
official macOS ARM64 binary directly from SChernykh/p2pool's GitHub
releases and verifying its SHA-256 against the project's GPG-signed
checksums file (sha256sums.txt.asc). We don't independently verify the PGP
signature itself (no `gpg` dependency added for this) — that's disclosed
honestly in the integrity record rather than overclaiming full signature
verification.

The p2pool binary itself is tiny (~5 MB) — nothing here downloads a large
blockchain. That's monerod's job (see monerod.py), which P2Pool needs a
synced instance of to actually validate shares.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from . import paths

GITHUB_REPO = "SChernykh/p2pool"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
ASSET_NAME = "macos-aarch64"  # this project targets Apple Silicon only
DEFAULT_STRATUM_PORT = 3335  # distinct from the pool-CRUD default of 3333


@dataclass
class ReleaseInfo:
    version: str
    asset_name: str
    asset_url: str
    checksums_url: str
    asset_size_bytes: int


def fetch_latest_release() -> ReleaseInfo | None:
    try:
        req = urllib.request.Request(GITHUB_API_LATEST, headers={"User-Agent": "MacMineLab/1.0"})
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            data = json.loads(resp.read())
        asset = next(a for a in data["assets"] if ASSET_NAME in a["name"] and a["name"].endswith(".tar.gz"))
        checksums = next(a for a in data["assets"] if a["name"] == "sha256sums.txt.asc")
        return ReleaseInfo(
            version=data["tag_name"],
            asset_name=asset["name"],
            asset_url=asset["browser_download_url"],
            checksums_url=checksums["browser_download_url"],
            asset_size_bytes=asset["size"],
        )
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError, StopIteration, OSError):
        return None


def _expected_sha256(checksums_text: str, asset_name: str) -> str | None:
    """Parses the clearsigned 'Name: X\\nSize: Y\\nSHA256: Z' block format
    real-verified against SChernykh/p2pool's actual release assets."""
    block_match = re.search(
        rf"Name: {re.escape(asset_name)}\n.*?\nSHA256: ([0-9a-f]{{64}})", checksums_text
    )
    return block_match.group(1) if block_match else None


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def install() -> tuple[bool, str]:
    """Downloads, verifies, and extracts the official p2pool binary. Small
    (~5 MB) — safe to run without a separate confirmation gate, unlike
    monerod's blockchain sync."""
    release = fetch_latest_release()
    if not release:
        return False, "Could not reach GitHub to find the latest P2Pool release."

    paths.ensure_data_dirs()
    tmp_dir = paths.BIN_DIR / "_p2pool_download"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    archive_path = tmp_dir / release.asset_name

    try:
        req = urllib.request.Request(release.asset_url, headers={"User-Agent": "MacMineLab/1.0"})
        with urllib.request.urlopen(req, timeout=30.0) as resp, open(archive_path, "wb") as f:
            f.write(resp.read())

        checksums_req = urllib.request.Request(release.checksums_url, headers={"User-Agent": "MacMineLab/1.0"})
        with urllib.request.urlopen(checksums_req, timeout=10.0) as resp:
            checksums_text = resp.read().decode()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False, f"Download failed: {e}"

    expected = _expected_sha256(checksums_text, release.asset_name)
    actual = _sha256_of(archive_path)
    if not expected or actual != expected:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False, (
            f"SHA-256 mismatch for {release.asset_name} — expected {expected}, got {actual}. "
            "Refusing to install a binary that doesn't match the signed checksum."
        )

    with tarfile.open(archive_path) as tar:
        tar.extractall(tmp_dir)

    extracted = next(tmp_dir.rglob("p2pool"), None)
    if not extracted or not extracted.is_file():
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False, "Downloaded archive did not contain a 'p2pool' binary."

    shutil.move(str(extracted), str(paths.P2POOL_BINARY))
    paths.P2POOL_BINARY.chmod(0o755)
    shutil.rmtree(tmp_dir, ignore_errors=True)

    return True, f"P2Pool {release.version} installed and SHA-256 verified."


@dataclass
class P2PoolIntegrity:
    installed: bool
    binary_path: str | None
    version: str | None
    architecture: str | None
    sha256: str | None
    install_source: str
    upstream_project: str
    verification_method: str
    checked_at: str


def find_p2pool_binary() -> str | None:
    return str(paths.P2POOL_BINARY) if paths.P2POOL_BINARY.exists() else None


def verify_installed() -> P2PoolIntegrity:
    binary_path = find_p2pool_binary()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not binary_path:
        return P2PoolIntegrity(
            installed=False, binary_path=None, version=None, architecture=None, sha256=None,
            install_source="none", upstream_project=f"https://github.com/{GITHUB_REPO}",
            verification_method="not installed", checked_at=now,
        )

    version_result = subprocess.run([binary_path, "--version"], capture_output=True, text=True, timeout=10, check=False)
    match = re.search(r"P2Pool (v[\d.]+)", version_result.stdout)
    version = match.group(1) if match else None

    file_result = subprocess.run(["file", binary_path], capture_output=True, text=True, timeout=10, check=False)
    architecture = "arm64" if "arm64" in file_result.stdout else ("x86_64" if "x86_64" in file_result.stdout else None)

    return P2PoolIntegrity(
        installed=True,
        binary_path=binary_path,
        version=version,
        architecture=architecture,
        sha256=_sha256_of(Path(binary_path)),
        install_source=f"Direct download from official GitHub releases (github.com/{GITHUB_REPO})",
        upstream_project=f"https://github.com/{GITHUB_REPO}",
        verification_method=(
            "SHA-256 verified against the project's GPG-signed sha256sums.txt.asc at install time. "
            "The PGP signature itself was not independently verified (no gpg dependency) — download "
            "only from the official GitHub releases page if you want to verify it yourself."
        ),
        checked_at=now,
    )


def save_integrity_record(record: P2PoolIntegrity) -> None:
    paths.ensure_data_dirs()
    with open(paths.P2POOL_INTEGRITY_FILE, "w") as f:
        json.dump(asdict(record), f, indent=2)


def load_integrity_record() -> dict | None:
    if not paths.P2POOL_INTEGRITY_FILE.exists():
        return None
    with open(paths.P2POOL_INTEGRITY_FILE) as f:
        return json.load(f)


# --- Process management -----------------------------------------------

def _process_name(pid: int) -> str | None:
    result = subprocess.run(["ps", "-o", "comm=", "-p", str(pid)], capture_output=True, text=True, check=False)
    return result.stdout.strip() or None


def _read_pidfile() -> tuple[int, int | None] | None:
    """Returns (pid, stratum_port) — stratum_port is recorded at launch
    time since it's not otherwise recoverable from a bare PID."""
    if not paths.P2POOL_PID_FILE.exists():
        return None
    try:
        content = paths.P2POOL_PID_FILE.read_text().strip()
        pid_str, _, port_str = content.partition("|")
        return int(pid_str), (int(port_str) if port_str else None)
    except (ValueError, OSError):
        return None


def is_tracked_process_alive() -> int | None:
    tracked = _read_pidfile()
    if not tracked:
        return None
    pid, _ = tracked

    # We spawned this process ourselves (in this server's lifetime) — it's
    # our responsibility to reap it via waitpid, or it sits as a zombie
    # that `ps` still reports as "alive" until reaped. Found by actually
    # launching p2pool with a bad argument and watching the status
    # endpoint report "running" seconds after the process had already
    # exited (see CHANGELOG). ChildProcessError means it's not our direct
    # child (e.g. the server restarted since it was launched) — fall back
    # to the ps-based check below for that case.
    try:
        reaped_pid, _ = os.waitpid(pid, os.WNOHANG)
        if reaped_pid == pid:
            paths.P2POOL_PID_FILE.unlink(missing_ok=True)
            return None
    except ChildProcessError:
        pass

    name = _process_name(pid)
    if name and "p2pool" in name:
        return pid
    paths.P2POOL_PID_FILE.unlink(missing_ok=True)
    return None


def launch(
    wallet_address: str, mode: str, data_dir: str,
    monerod_rpc_port: int, monerod_zmq_port: int,
    stratum_port: int = DEFAULT_STRATUM_PORT, light_mode: bool = False,
) -> int:
    if mode not in ("main", "mini", "nano"):
        raise ValueError("mode must be 'main', 'mini', or 'nano'")
    if is_tracked_process_alive():
        raise RuntimeError("p2pool is already running (tracked).")

    binary = find_p2pool_binary()
    if not binary:
        raise RuntimeError("p2pool is not installed. Install it first.")

    paths.ensure_data_dirs()
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    args = [
        binary,
        "--wallet", wallet_address,
        "--host", "127.0.0.1",
        "--rpc-port", str(monerod_rpc_port),
        "--zmq-port", str(monerod_zmq_port),
        "--stratum", f"127.0.0.1:{stratum_port}",
        "--data-dir", data_dir,
        "--no-dns",
    ]
    if mode == "mini":
        args.append("--mini")
    elif mode == "nano":
        args.append("--nano")
    if light_mode:
        args.append("--light-mode")

    log_path = paths.LOGS_DIR / "p2pool.log"
    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(
            args,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    paths.P2POOL_PID_FILE.write_text(f"{proc.pid}|{stratum_port}")
    return proc.pid


def stop(timeout: float = 10.0) -> bool:
    pid = is_tracked_process_alive()
    if not pid:
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        paths.P2POOL_PID_FILE.unlink(missing_ok=True)
        return True

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _process_name(pid) is None:
            paths.P2POOL_PID_FILE.unlink(missing_ok=True)
            return True
        time.sleep(0.3)

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    time.sleep(0.5)
    still_alive = _process_name(pid) is not None
    if not still_alive:
        paths.P2POOL_PID_FILE.unlink(missing_ok=True)
    return not still_alive


@dataclass
class P2PoolStatus:
    running: bool
    pid: int | None
    stratum_port: int | None


def get_status() -> P2PoolStatus:
    """PID-alive check only. p2pool's --local-api JSON schema was not
    verified against a real running instance (needs a real checksummed
    Monero wallet address to start, which we don't fabricate — see
    README) — this deliberately doesn't guess at parsing it."""
    pid = is_tracked_process_alive()
    if not pid:
        return P2PoolStatus(False, None, None)
    tracked = _read_pidfile()
    stratum_port = tracked[1] if tracked else None
    return P2PoolStatus(True, pid, stratum_port)
