"""In-process background real-mining runner used by the FastAPI backend.

Mirrors runner.BenchmarkRunner's structure — a background thread plus a
thread-safe snapshot — but mining runs indefinitely (until stop() is
called) rather than for a fixed duration, so it's driven by a
threading.Event instead of a wall-clock deadline.
"""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass

from . import db, mining
from .mining import StopSignal


@dataclass
class MiningRunnerState:
    running: bool
    pool_id: int | None
    wallet_id: int | None
    threads: int | None
    session_id: int | None
    elapsed_s: float | None
    latest_hashrate_10s: float | None
    latest_hashrate_60s: float | None
    shares_good: int | None
    shares_total: int | None
    connection_pool: str | None
    last_result: dict | None
    error: str | None


class MiningRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._pool_id: int | None = None
        self._wallet_id: int | None = None
        self._threads: int | None = None
        self._session_id: int | None = None
        self._start_monotonic: float | None = None
        self._latest_10s: float | None = None
        self._latest_60s: float | None = None
        self._shares_good: int | None = None
        self._shares_total: int | None = None
        self._connection_pool: str | None = None
        self._last_result: dict | None = None
        self._error: str | None = None
        self._stop_event = StopSignal()
        self._thread: threading.Thread | None = None

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self, pool: dict, wallet: dict, threads: int) -> None:
        with self._lock:
            if self._running:
                raise RuntimeError("A mining session is already running.")
            self._running = True
            self._pool_id = pool["id"]
            self._wallet_id = wallet["id"]
            self._threads = threads
            self._session_id = None
            self._start_monotonic = time.monotonic()
            self._latest_10s = None
            self._latest_60s = None
            self._shares_good = None
            self._shares_total = None
            self._connection_pool = None
            self._error = None

        self._stop_event = StopSignal()
        self._thread = threading.Thread(target=self._run, args=(pool, wallet, threads), daemon=True)
        self._thread.start()

    def _on_sample(self, sample, summary: dict) -> None:
        with self._lock:
            self._latest_10s = sample.hashrate_10s
            self._latest_60s = sample.hashrate_60s
            results = summary.get("results", {})
            self._shares_good = results.get("shares_good")
            self._shares_total = results.get("shares_total")
            self._connection_pool = summary.get("connection", {}).get("pool")

    def _run(self, pool: dict, wallet: dict, threads: int) -> None:
        try:
            result = mining.run_mining_session(pool, wallet, threads, self._stop_event, on_sample=self._on_sample)
            with self._lock:
                self._session_id = result.session_id
                self._last_result = asdict(result)
        except Exception as e:  # noqa: BLE001 — surfaced via snapshot(), never swallowed
            with self._lock:
                self._error = str(e)
        finally:
            with self._lock:
                self._running = False
                self._start_monotonic = None

    def stop(self, reason: str = "manual") -> None:
        self._stop_event.set(reason)

    def stop_and_wait(self, reason: str = "manual", timeout: float = 10.0) -> bool:
        """Used by the safety manager: blocks until the session has actually
        finished (not just signaled), so a follow-up restart_with_threads()
        doesn't race with the old session still shutting down."""
        thread = self._thread
        self.stop(reason)
        if thread:
            thread.join(timeout=timeout)
        return not self.is_running()

    def restart_with_threads(self, new_threads: int, reason: str) -> bool:
        """Stops the current session (if any) and immediately starts a new
        one against the same pool/wallet with a different thread count.
        Used by the safety manager to back off under thermal pressure.
        Returns False (and does nothing) if nothing was running."""
        with self._lock:
            if not self._running:
                return False
            pool_id, wallet_id = self._pool_id, self._wallet_id
        if pool_id is None or wallet_id is None:
            return False

        pool = db.get_pool(pool_id)
        wallet = db.get_wallet(wallet_id)
        if not self.stop_and_wait(reason=reason):
            return False
        if not pool or not wallet:
            return False
        self.start(pool, wallet, max(1, new_threads))
        return True

    def snapshot(self) -> MiningRunnerState:
        with self._lock:
            elapsed = (
                round(time.monotonic() - self._start_monotonic, 1)
                if self._running and self._start_monotonic is not None
                else None
            )
            return MiningRunnerState(
                running=self._running,
                pool_id=self._pool_id,
                wallet_id=self._wallet_id,
                threads=self._threads,
                session_id=self._session_id,
                elapsed_s=elapsed,
                latest_hashrate_10s=self._latest_10s,
                latest_hashrate_60s=self._latest_60s,
                shares_good=self._shares_good,
                shares_total=self._shares_total,
                connection_pool=self._connection_pool,
                last_result=self._last_result,
                error=self._error,
            )


# Single shared instance — MacMine Lab only ever runs one mining session at a time.
mining_runner = MiningRunner()
