"""SQLite persistence layer — the local, canonical store for everything
MacMine Lab measures. No ORM: the schema is small enough that raw sqlite3
keeps this auditable and dependency-free.

Retention: telemetry_samples is the only table that grows unbounded during
normal use (a background sampler writes to it every few seconds while the
server runs), so every write also prunes rows older than TELEMETRY_RETENTION_DAYS.
Benchmark/session data is kept indefinitely unless the user deletes it.
"""

from __future__ import annotations

import contextlib
import datetime
import json
import sqlite3
from pathlib import Path

from . import paths

DB_PATH = paths.DATA_DIR / "macmine.db"
TELEMETRY_RETENTION_DAYS = 7

SCHEMA = """
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    threads INTEGER NOT NULL,
    duration_target_s INTEGER NOT NULL,
    duration_actual_s REAL NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    xmrig_version TEXT,
    avg_hs REAL,
    peak_hs REAL,
    low_hs REAL,
    hs_per_thread REAL,
    final_thermal_state TEXT NOT NULL,
    stopped_reason TEXT NOT NULL,
    hashrate_samples_json TEXT NOT NULL,
    telemetry_samples_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS telemetry_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sampled_at TEXT NOT NULL,
    cpu_user_percent REAL,
    cpu_sys_percent REAL,
    cpu_idle_percent REAL,
    load_avg_1m REAL,
    memory_used_gb REAL,
    memory_unused_gb REAL,
    battery_percent INTEGER,
    on_ac_power INTEGER,
    thermal_state TEXT NOT NULL,
    miner_running INTEGER NOT NULL DEFAULT 0,
    miner_cpu_percent REAL
);
CREATE INDEX IF NOT EXISTS idx_telemetry_sampled_at ON telemetry_samples(sampled_at);

CREATE TABLE IF NOT EXISTS miner_installations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    installed INTEGER NOT NULL,
    binary_path TEXT,
    version TEXT,
    architecture TEXT,
    sha256 TEXT,
    install_source TEXT NOT NULL,
    upstream_project TEXT NOT NULL,
    verification_method TEXT NOT NULL,
    checked_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL,
    label TEXT,
    address_kind TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    tls INTEGER NOT NULL DEFAULT 0,
    worker_name TEXT,
    password TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS mining_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pool_id INTEGER NOT NULL REFERENCES pools(id),
    wallet_id INTEGER NOT NULL REFERENCES wallets(id),
    threads INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_s REAL,
    avg_hs REAL,
    peak_hs REAL,
    shares_good INTEGER,
    shares_total INTEGER,
    hashes_total INTEGER,
    stopped_reason TEXT,
    hashrate_samples_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@contextlib.contextmanager
def connect():
    paths.ensure_data_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def insert_benchmark_run(result) -> int:
    """`result` is a benchmark.BenchmarkResult."""
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO benchmark_runs
               (threads, duration_target_s, duration_actual_s, started_at, ended_at,
                xmrig_version, avg_hs, peak_hs, low_hs, hs_per_thread,
                final_thermal_state, stopped_reason, hashrate_samples_json,
                telemetry_samples_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.threads,
                result.duration_target_s,
                result.duration_actual_s,
                result.started_at,
                result.ended_at,
                result.xmrig_version,
                result.avg_hs,
                result.peak_hs,
                result.low_hs,
                result.hs_per_thread,
                result.final_thermal_state,
                result.stopped_reason,
                json.dumps(result.hashrate_samples),
                json.dumps(result.telemetry_samples),
            ),
        )
        return cur.lastrowid


def list_benchmark_runs(limit: int = 50) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT id, threads, duration_target_s, duration_actual_s, started_at,
                      ended_at, xmrig_version, avg_hs, peak_hs, low_hs, hs_per_thread,
                      final_thermal_state, stopped_reason
               FROM benchmark_runs ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_benchmark_run(run_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM benchmark_runs WHERE id = ?", (run_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["hashrate_samples"] = json.loads(d.pop("hashrate_samples_json"))
        d["telemetry_samples"] = json.loads(d.pop("telemetry_samples_json"))
        return d


def insert_telemetry_sample(telemetry, miner_running: bool, miner_cpu_percent: float | None) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with connect() as conn:
        conn.execute(
            """INSERT INTO telemetry_samples
               (sampled_at, cpu_user_percent, cpu_sys_percent, cpu_idle_percent,
                load_avg_1m, memory_used_gb, memory_unused_gb, battery_percent,
                on_ac_power, thermal_state, miner_running, miner_cpu_percent)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                now,
                telemetry.cpu.user_percent,
                telemetry.cpu.sys_percent,
                telemetry.cpu.idle_percent,
                telemetry.cpu.load_avg_1m,
                telemetry.memory.used_gb,
                telemetry.memory.unused_gb,
                telemetry.battery.percent,
                int(bool(telemetry.battery.on_ac_power)) if telemetry.battery.on_ac_power is not None else None,
                telemetry.thermal.state,
                int(miner_running),
                miner_cpu_percent,
            ),
        )
        cutoff = (
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=TELEMETRY_RETENTION_DAYS)
        ).isoformat()
        conn.execute("DELETE FROM telemetry_samples WHERE sampled_at < ?", (cutoff,))


def list_telemetry_samples(since_minutes: int = 60, limit: int = 2000) -> list[dict]:
    cutoff = (
        datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(minutes=since_minutes)
    ).isoformat()
    with connect() as conn:
        rows = conn.execute(
            """SELECT * FROM telemetry_samples WHERE sampled_at >= ?
               ORDER BY id ASC LIMIT ?""",
            (cutoff, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def insert_miner_installation(record) -> int:
    """`record` is an integrity.MinerIntegrity."""
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO miner_installations
               (installed, binary_path, version, architecture, sha256,
                install_source, upstream_project, verification_method, checked_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                int(record.installed),
                record.binary_path,
                record.version,
                record.architecture,
                record.sha256,
                record.install_source,
                record.upstream_project,
                record.verification_method,
                record.checked_at,
            ),
        )
        return cur.lastrowid


def get_latest_miner_installation() -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM miner_installations ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def set_setting(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            """INSERT INTO app_settings (key, value, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                                               updated_at = excluded.updated_at""",
            (key, value),
        )


def get_setting(key: str, default: str | None = None) -> str | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default


# --- Wallets -----------------------------------------------------------
# Public receiving addresses only. MacMine Lab never stores a seed phrase
# or private/spend key — there is no column for one.

def insert_wallet(address: str, address_kind: str, label: str | None) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO wallets (address, label, address_kind) VALUES (?, ?, ?)",
            (address, label, address_kind),
        )
        return cur.lastrowid


def list_wallets() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM wallets ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_wallet(wallet_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,)).fetchone()
        return dict(row) if row else None


def delete_wallet(wallet_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))


# --- Pools ---------------------------------------------------------------

def insert_pool(
    name: str, host: str, port: int, tls: bool, worker_name: str | None,
    password: str | None, notes: str | None,
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO pools (name, host, port, tls, worker_name, password, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, host, port, int(tls), worker_name, password, notes),
        )
        return cur.lastrowid


def list_pools() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM pools ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_pool(pool_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM pools WHERE id = ?", (pool_id,)).fetchone()
        return dict(row) if row else None


def delete_pool(pool_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM pools WHERE id = ?", (pool_id,))


# --- Mining sessions -------------------------------------------------------

def insert_mining_session_start(pool_id: int, wallet_id: int, threads: int, started_at: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO mining_sessions (pool_id, wallet_id, threads, started_at)
               VALUES (?, ?, ?, ?)""",
            (pool_id, wallet_id, threads, started_at),
        )
        return cur.lastrowid


def finalize_mining_session(
    session_id: int, ended_at: str, duration_s: float, avg_hs: float | None,
    peak_hs: float | None, shares_good: int | None, shares_total: int | None,
    hashes_total: int | None, stopped_reason: str, hashrate_samples: list,
) -> None:
    with connect() as conn:
        conn.execute(
            """UPDATE mining_sessions SET ended_at = ?, duration_s = ?, avg_hs = ?,
               peak_hs = ?, shares_good = ?, shares_total = ?, hashes_total = ?,
               stopped_reason = ?, hashrate_samples_json = ? WHERE id = ?""",
            (
                ended_at, duration_s, avg_hs, peak_hs, shares_good, shares_total,
                hashes_total, stopped_reason, json.dumps(hashrate_samples), session_id,
            ),
        )


def list_mining_sessions(limit: int = 50) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT id, pool_id, wallet_id, threads, started_at, ended_at, duration_s,
                      avg_hs, peak_hs, shares_good, shares_total, hashes_total, stopped_reason
               FROM mining_sessions ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_mining_session(session_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM mining_sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["hashrate_samples"] = json.loads(d.pop("hashrate_samples_json"))
        return d
