"""Monero daemon (monerod) installation, verification, and process
management — the local node P2Pool requires to validate shares.

Storage note: monerod's blockchain data is the one genuinely large
download in this project. Real, sourced estimates as of this writing
(community sources — see requirements_info() for citations, since these
numbers grow over time and MacMine Lab won't pretend a single hardcoded
figure stays accurate): a pruned node currently needs roughly 60-100+ GB,
a full node roughly 190+ GB. MacMine Lab NEVER starts a sync automatically
— launch() is only ever called in response to an explicit user action, and
the setup UI shows these numbers before any button that could trigger one.

monerod itself (the ~94 MB binary) is installed via Homebrew's official
`monero` formula — same trust model as XMRig in Phase 1.
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
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from . import paths

MIN_VERSION = "0.18.0.0"  # P2Pool's documented minimum
DEFAULT_RPC_PORT = 18081
DEFAULT_ZMQ_PORT = 18083
DEFAULT_P2P_PORT = 18080

STORAGE_ESTIMATE_SOURCES = [
    "https://docs.getmonero.org/running-node/introduction/",
    "https://blog.monerica.com/articles/monero-node-requirements",
]


@dataclass
class StorageEstimate:
    pruned_gb_low: int
    pruned_gb_high: int
    full_gb_low: int
    full_gb_high: int
    sources: list[str]
    note: str


def requirements_info() -> StorageEstimate:
    """Real, sourced (not fabricated-precision) storage estimates. These
    numbers grow as the Monero blockchain grows — check the sources
    yourself for the current figure before committing to a sync."""
    return StorageEstimate(
        pruned_gb_low=60,
        pruned_gb_high=120,
        full_gb_low=190,
        full_gb_high=250,
        sources=STORAGE_ESTIMATE_SOURCES,
        note=(
            "Blockchain size grows continuously — these are community estimates "
            "at the time this was written, not a live-fetched figure. Check the "
            "sources above for the current number before starting a sync."
        ),
    )


@dataclass
class MonerodIntegrity:
    installed: bool
    binary_path: str | None
    version: str | None
    architecture: str | None
    sha256: str | None
    install_source: str
    upstream_project: str
    verification_method: str
    checked_at: str


def find_monerod_binary() -> str | None:
    return shutil.which("monerod")


def is_already_installed_via_brew() -> bool:
    result = subprocess.run(
        ["brew", "list", "--formula", "monero"], capture_output=True, text=True, check=False
    )
    return result.returncode == 0


def install_via_brew() -> tuple[bool, str]:
    if not shutil.which("brew"):
        return False, "Homebrew is not installed. Install it first: https://brew.sh"
    if is_already_installed_via_brew():
        return True, "monerod already installed via Homebrew (skipped reinstall)."
    result = subprocess.run(
        ["brew", "install", "monero"], capture_output=True, text=True, timeout=300, check=False
    )
    if result.returncode != 0:
        return False, f"brew install monero failed:\n{result.stderr.strip()}"
    return True, "monerod installed via Homebrew (the 'monero' formula)."


def _sha256_of(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def verify_installed() -> MonerodIntegrity:
    binary_path = find_monerod_binary()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not binary_path:
        return MonerodIntegrity(
            installed=False, binary_path=None, version=None, architecture=None, sha256=None,
            install_source="none", upstream_project="https://github.com/monero-project/monero",
            verification_method="not installed", checked_at=now,
        )

    version_result = subprocess.run(
        [binary_path, "--version"], capture_output=True, text=True, timeout=10, check=False
    )
    version = None
    match = re.search(r"Monero '.+?' \(v([\d.]+)", version_result.stdout)
    if match:
        version = match.group(1)

    file_result = subprocess.run(["file", binary_path], capture_output=True, text=True, timeout=10, check=False)
    architecture = "arm64" if "arm64" in file_result.stdout else ("x86_64" if "x86_64" in file_result.stdout else None)

    return MonerodIntegrity(
        installed=True,
        binary_path=binary_path,
        version=version,
        architecture=architecture,
        sha256=_sha256_of(binary_path),
        install_source="Homebrew (homebrew-core formula 'monero')",
        upstream_project="https://github.com/monero-project/monero",
        verification_method=(
            "Homebrew bottle checksum verified at install time by brew itself; "
            "SHA-256 above independently computed by MacMine Lab from the installed binary."
        ),
        checked_at=now,
    )


def save_integrity_record(record: MonerodIntegrity) -> None:
    paths.ensure_data_dirs()
    with open(paths.MONEROD_INTEGRITY_FILE, "w") as f:
        json.dump(asdict(record), f, indent=2)


def load_integrity_record() -> dict | None:
    if not paths.MONEROD_INTEGRITY_FILE.exists():
        return None
    with open(paths.MONEROD_INTEGRITY_FILE) as f:
        return json.load(f)


# --- Process management -----------------------------------------------
# Independent of miner.py's XMRig tracking — monerod runs concurrently
# with (not instead of) whatever XMRig is doing.

def _process_name(pid: int) -> str | None:
    result = subprocess.run(["ps", "-o", "comm=", "-p", str(pid)], capture_output=True, text=True, check=False)
    return result.stdout.strip() or None


def is_tracked_process_alive() -> int | None:
    if not paths.MONEROD_PID_FILE.exists():
        return None
    try:
        pid = int(paths.MONEROD_PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None

    # We spawned this process ourselves — reap it via waitpid or it can
    # sit as a zombie that `ps` still reports as "alive" until reaped.
    # See p2pool.py's is_tracked_process_alive() for how this was found.
    try:
        reaped_pid, _ = os.waitpid(pid, os.WNOHANG)
        if reaped_pid == pid:
            paths.MONEROD_PID_FILE.unlink(missing_ok=True)
            return None
    except ChildProcessError:
        pass

    name = _process_name(pid)
    if name and "monerod" in name:
        return pid
    paths.MONEROD_PID_FILE.unlink(missing_ok=True)
    return None


def launch(
    data_dir: str, pruned: bool, rpc_port: int = DEFAULT_RPC_PORT,
    zmq_port: int = DEFAULT_ZMQ_PORT, p2p_port: int = DEFAULT_P2P_PORT,
    bandwidth_limit_kbps: int | None = None,
) -> int:
    """Starts monerod. Caller is responsible for having already shown the
    user the real storage/bandwidth estimate and gotten explicit
    confirmation — this function itself does not gate on that, by design:
    it's a pure mechanism, the consent gate lives in the API layer."""
    if is_tracked_process_alive():
        raise RuntimeError("monerod is already running (tracked).")

    binary = find_monerod_binary()
    if not binary:
        raise RuntimeError("monerod is not installed. Install it first.")

    paths.ensure_data_dirs()
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    args = [
        binary,
        "--data-dir", data_dir,
        "--rpc-bind-port", str(rpc_port),
        "--p2p-bind-port", str(p2p_port),
        "--zmq-pub", f"tcp://127.0.0.1:{zmq_port}",
        "--non-interactive",
    ]
    if pruned:
        args.append("--prune-blockchain")
    if bandwidth_limit_kbps:
        args += ["--limit-rate-down", str(bandwidth_limit_kbps)]

    log_path = paths.LOGS_DIR / "monerod.log"
    stderr_path = paths.LOGS_DIR / "monerod.log.stderr"
    with open(stderr_path, "w") as stderr_file:
        proc = subprocess.Popen(
            args + ["--log-file", str(log_path)],
            stdout=subprocess.DEVNULL,
            stderr=stderr_file,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    paths.MONEROD_PID_FILE.write_text(str(proc.pid))
    return proc.pid


def stop(timeout: float = 10.0) -> bool:
    pid = is_tracked_process_alive()
    if not pid:
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        paths.MONEROD_PID_FILE.unlink(missing_ok=True)
        return True

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _process_name(pid) is None:
            paths.MONEROD_PID_FILE.unlink(missing_ok=True)
            return True
        time.sleep(0.3)

    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    time.sleep(0.5)
    still_alive = _process_name(pid) is not None
    if not still_alive:
        paths.MONEROD_PID_FILE.unlink(missing_ok=True)
    return not still_alive


@dataclass
class MonerodStatus:
    running: bool
    pid: int | None
    height: int | None
    target_height: int | None
    synchronized: bool | None
    sync_progress_percent: float | None
    database_size_gb: float | None
    free_space_gb: float | None


def get_status(rpc_port: int = DEFAULT_RPC_PORT) -> MonerodStatus:
    pid = is_tracked_process_alive()
    if not pid:
        return MonerodStatus(False, None, None, None, None, None, None, None)

    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{rpc_port}/json_rpc",
            data=json.dumps({"jsonrpc": "2.0", "id": "0", "method": "get_info"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            result = json.loads(resp.read())["result"]
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError, OSError):
        # Running but RPC not ready yet (still starting up) — real, honest state.
        return MonerodStatus(True, pid, None, None, None, None, None, None)

    height = result.get("height")
    target_height = result.get("target_height") or height
    progress = round(100 * height / target_height, 2) if height and target_height else None

    return MonerodStatus(
        running=True,
        pid=pid,
        height=height,
        target_height=target_height,
        synchronized=result.get("synchronized"),
        sync_progress_percent=progress,
        database_size_gb=round(result["database_size"] / 1e9, 2) if result.get("database_size") else None,
        free_space_gb=round(result["free_space"] / 1e9, 2) if result.get("free_space") else None,
    )
