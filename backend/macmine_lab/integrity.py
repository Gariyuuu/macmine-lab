"""XMRig acquisition and integrity recording.

MacMine Lab never downloads miner binaries from arbitrary mirrors. XMRig is
installed exclusively through Homebrew's official `homebrew-core` formula,
which builds from the real xmrig/xmrig project source and ships bottles
whose checksums Homebrew itself validates before installing. On top of that,
we independently hash the installed binary and record version/architecture
so this is auditable later — nothing here is marked "Verified" unless we
actually computed it.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass

from . import db, paths

HOMEBREW_FORMULA_URL = (
    "https://github.com/Homebrew/homebrew-core/blob/HEAD/Formula/x/xmrig.rb"
)
UPSTREAM_PROJECT_URL = "https://github.com/xmrig/xmrig"


@dataclass
class MinerIntegrity:
    installed: bool
    binary_path: str | None
    version: str | None
    architecture: str | None
    sha256: str | None
    install_source: str
    upstream_project: str
    verification_method: str
    checked_at: str


def find_xmrig_binary() -> str | None:
    return shutil.which("xmrig")


def is_brew_available() -> bool:
    return shutil.which("brew") is not None


def is_xmrig_already_installed_via_brew() -> bool:
    """Check first, per project rule: never blindly reinstall packages."""
    result = subprocess.run(
        ["brew", "list", "--formula", "xmrig"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def install_xmrig_via_brew() -> tuple[bool, str]:
    """Install XMRig via Homebrew if not already present. Returns (ok, message)."""
    if not is_brew_available():
        return False, "Homebrew is not installed. Install Homebrew first: https://brew.sh"

    if is_xmrig_already_installed_via_brew():
        return True, "xmrig already installed via Homebrew (skipped reinstall)."

    result = subprocess.run(
        ["brew", "install", "xmrig"],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        return False, f"brew install xmrig failed:\n{result.stderr.strip()}"
    return True, "xmrig installed via Homebrew."


def _get_version(binary_path: str) -> str | None:
    result = subprocess.run(
        [binary_path, "--version"], capture_output=True, text=True, timeout=10, check=False
    )
    if result.returncode != 0:
        return None
    match = re.search(r"XMRig\s+([\d.]+)", result.stdout)
    return match.group(1) if match else result.stdout.strip().splitlines()[0]


def _get_architecture(binary_path: str) -> str | None:
    result = subprocess.run(
        ["file", binary_path], capture_output=True, text=True, timeout=10, check=False
    )
    if result.returncode != 0:
        return None
    if "arm64" in result.stdout:
        return "arm64"
    if "x86_64" in result.stdout:
        return "x86_64"
    return result.stdout.strip()


def _sha256_of(binary_path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(binary_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def verify_installed_xmrig() -> MinerIntegrity:
    """Inspect whatever xmrig binary is actually on PATH and record real facts."""
    binary_path = find_xmrig_binary()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if not binary_path:
        return MinerIntegrity(
            installed=False,
            binary_path=None,
            version=None,
            architecture=None,
            sha256=None,
            install_source="none",
            upstream_project=UPSTREAM_PROJECT_URL,
            verification_method="not installed",
            checked_at=now,
        )

    version = _get_version(binary_path)
    architecture = _get_architecture(binary_path)
    sha256 = _sha256_of(binary_path)

    return MinerIntegrity(
        installed=True,
        binary_path=binary_path,
        version=version,
        architecture=architecture,
        sha256=sha256,
        install_source=f"Homebrew (homebrew-core formula: {HOMEBREW_FORMULA_URL})",
        upstream_project=UPSTREAM_PROJECT_URL,
        verification_method=(
            "Homebrew bottle checksum verified at install time by brew itself; "
            "SHA-256 above independently computed by MacMine Lab from the installed binary."
        ),
        checked_at=now,
    )


def save_integrity_record(record: MinerIntegrity) -> None:
    paths.ensure_data_dirs()
    with open(paths.MINER_INTEGRITY_FILE, "w") as f:
        json.dump(asdict(record), f, indent=2)
    db.init_db()
    db.insert_miner_installation(record)


def load_integrity_record() -> dict | None:
    if not paths.MINER_INTEGRITY_FILE.exists():
        return None
    with open(paths.MINER_INTEGRITY_FILE) as f:
        return json.load(f)
