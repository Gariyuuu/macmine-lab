"""Real XMR pool mining.

Launches actual XMRig against a configured pool and your public wallet
address, tracks accepted/rejected shares via XMRig's local HTTP API, and
persists the session to SQLite. Unlike benchmark mode this runs
indefinitely — until `stop_event` is set — since real mining has no natural
end time.

MacMine Lab never touches a seed phrase or private key: the only wallet
data that ever reaches XMRig is the public address, passed as the pool
username exactly like any other Monero mining setup.
"""

from __future__ import annotations

import datetime
import threading
import time
from dataclasses import asdict, dataclass

from . import db, miner, xmrig_api

POLL_INTERVAL_S = 1.0


@dataclass
class MiningHashrateSample:
    t_offset_s: float
    hashrate_10s: float | None
    hashrate_60s: float | None


@dataclass
class MiningSessionResult:
    session_id: int
    pool_id: int
    wallet_id: int
    threads: int
    started_at: str
    ended_at: str
    duration_s: float
    avg_hs: float | None
    peak_hs: float | None
    shares_good: int | None
    shares_total: int | None
    hashes_total: int | None
    stopped_reason: str
    hashrate_samples: list


def build_mining_args(pool: dict, wallet_address: str, threads: int, http_port: int, http_token: str) -> list[str]:
    user = wallet_address
    if pool.get("worker_name"):
        user = f"{wallet_address}.{pool['worker_name']}"

    args = [
        "-o", f"{pool['host']}:{pool['port']}",
        "-u", user,
        "-p", pool.get("password") or "x",
        "-t", str(threads),
        "--http-host=127.0.0.1",
        f"--http-port={http_port}",
        f"--http-access-token={http_token}",
        "--no-color",
    ]
    if pool.get("tls"):
        args.append("--tls")
    return args


def run_mining_session(
    pool: dict, wallet: dict, threads: int, stop_event: threading.Event, on_sample=None
) -> MiningSessionResult:
    port = xmrig_api.free_port()
    token = xmrig_api.new_token()
    args = build_mining_args(pool, wallet["address"], threads, port, token)

    started_at = datetime.datetime.now(datetime.timezone.utc)
    session_id = db.insert_mining_session_start(pool["id"], wallet["id"], threads, started_at.isoformat())
    log_name = f"mining_{started_at.strftime('%Y%m%dT%H%M%SZ')}_{threads}t.log"
    proc, _log_path = miner.launch(args, log_name)

    hashrate_samples: list[MiningHashrateSample] = []
    stopped_reason = "manual"
    last_summary: dict | None = None

    try:
        start = time.monotonic()
        while not stop_event.is_set():
            if proc.poll() is not None:
                stopped_reason = f"xmrig exited unexpectedly (code {proc.returncode})"
                break

            elapsed = time.monotonic() - start
            summary = xmrig_api.fetch_summary(port, token)
            if summary:
                last_summary = summary
                hr = summary.get("hashrate", {}).get("total", [None, None, None])
                sample = MiningHashrateSample(round(elapsed, 1), hr[0], hr[1])
                hashrate_samples.append(sample)
                if on_sample:
                    on_sample(sample, summary)

            stop_event.wait(POLL_INTERVAL_S)
    finally:
        miner.stop(proc.pid)

    ended_at = datetime.datetime.now(datetime.timezone.utc)
    duration = (ended_at - started_at).total_seconds()

    valid_rates = [s.hashrate_10s for s in hashrate_samples if s.hashrate_10s is not None]
    avg_hs = round(sum(valid_rates) / len(valid_rates), 1) if valid_rates else None
    peak_hs = round(max(valid_rates), 1) if valid_rates else None

    results = (last_summary or {}).get("results", {})
    shares_good = results.get("shares_good")
    shares_total = results.get("shares_total")
    hashes_total = results.get("hashes_total")

    hashrate_samples_dicts = [asdict(s) for s in hashrate_samples]
    db.finalize_mining_session(
        session_id, ended_at.isoformat(), round(duration, 1), avg_hs, peak_hs,
        shares_good, shares_total, hashes_total, stopped_reason, hashrate_samples_dicts,
    )

    return MiningSessionResult(
        session_id=session_id,
        pool_id=pool["id"],
        wallet_id=wallet["id"],
        threads=threads,
        started_at=started_at.isoformat(),
        ended_at=ended_at.isoformat(),
        duration_s=round(duration, 1),
        avg_hs=avg_hs,
        peak_hs=peak_hs,
        shares_good=shares_good,
        shares_total=shares_total,
        hashes_total=hashes_total,
        stopped_reason=stopped_reason,
        hashrate_samples=hashrate_samples_dicts,
    )
