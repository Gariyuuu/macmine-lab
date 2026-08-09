"""Local, self-contained data locations for MacMine Lab.

Everything MacMine Lab writes lives under <repo>/data — nothing goes to
~/Library, no cloud account, no hidden state elsewhere on disk. This makes
"clean uninstall" as simple as removing the project directory.
"""

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
BENCHMARKS_DIR = DATA_DIR / "benchmarks"
LOGS_DIR = DATA_DIR / "logs"
RUN_DIR = DATA_DIR / "run"
INTEGRITY_DIR = DATA_DIR / "integrity"

XMRIG_PID_FILE = RUN_DIR / "xmrig.pid"
MINER_INTEGRITY_FILE = INTEGRITY_DIR / "miner_integrity.json"


def ensure_data_dirs() -> None:
    for d in (BENCHMARKS_DIR, LOGS_DIR, RUN_DIR, INTEGRITY_DIR):
        d.mkdir(parents=True, exist_ok=True)
