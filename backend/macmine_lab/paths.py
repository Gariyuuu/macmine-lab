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
BIN_DIR = DATA_DIR / "bin"

XMRIG_PID_FILE = RUN_DIR / "xmrig.pid"
MONEROD_PID_FILE = RUN_DIR / "monerod.pid"
P2POOL_PID_FILE = RUN_DIR / "p2pool.pid"
MINER_INTEGRITY_FILE = INTEGRITY_DIR / "miner_integrity.json"
MONEROD_INTEGRITY_FILE = INTEGRITY_DIR / "monerod_integrity.json"
P2POOL_INTEGRITY_FILE = INTEGRITY_DIR / "p2pool_integrity.json"
P2POOL_BINARY = BIN_DIR / "p2pool"

# Default location for monerod's blockchain data. This can grow to
# tens-to-100+ GB (see monerod.py) — deliberately kept configurable so
# users can point it at external storage instead of accepting this default.
DEFAULT_MONEROD_DATA_DIR = DATA_DIR / "monerod-chain"
DEFAULT_P2POOL_DATA_DIR = DATA_DIR / "p2pool-cache"


def ensure_data_dirs() -> None:
    for d in (BENCHMARKS_DIR, LOGS_DIR, RUN_DIR, INTEGRITY_DIR, BIN_DIR):
        d.mkdir(parents=True, exist_ok=True)
