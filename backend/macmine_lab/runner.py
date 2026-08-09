"""In-process background benchmark runner used by the FastAPI backend.

`benchmark.run_benchmark` is a blocking, real-time-paced call (it sleeps in
step with actual wall-clock seconds) — it must not run on the API's async
event loop. This wraps it in a plain background thread and exposes a
thread-safe snapshot of progress so HTTP/WebSocket handlers can report real,
current state without blocking.

Only one benchmark can be in flight at a time, mirroring the single-process
assumption in miner.py.
"""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass

from . import benchmark


@dataclass
class RunnerState:
    running: bool
    threads: int | None
    duration_target_s: int | None
    elapsed_s: float | None
    latest_hashrate_10s: float | None
    latest_hashrate_60s: float | None
    last_result: dict | None
    error: str | None


class BenchmarkRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._threads: int | None = None
        self._duration_target_s: int | None = None
        self._start_monotonic: float | None = None
        self._latest_10s: float | None = None
        self._latest_60s: float | None = None
        self._last_result: dict | None = None
        self._error: str | None = None
        self._thread: threading.Thread | None = None

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self, threads: int, duration_seconds: int) -> None:
        with self._lock:
            if self._running:
                raise RuntimeError("A benchmark is already running.")
            self._running = True
            self._threads = threads
            self._duration_target_s = duration_seconds
            self._start_monotonic = time.monotonic()
            self._latest_10s = None
            self._latest_60s = None
            self._error = None

        self._thread = threading.Thread(target=self._run, args=(threads, duration_seconds), daemon=True)
        self._thread.start()

    def _on_sample(self, sample) -> None:
        with self._lock:
            self._latest_10s = sample.hashrate_10s
            self._latest_60s = sample.hashrate_60s

    def _run(self, threads: int, duration_seconds: int) -> None:
        try:
            result = benchmark.run_benchmark(threads, duration_seconds, on_sample=self._on_sample)
            with self._lock:
                self._last_result = asdict(result)
        except Exception as e:  # noqa: BLE001 — surfaced to the API, never swallowed silently
            with self._lock:
                self._error = str(e)
        finally:
            with self._lock:
                self._running = False
                self._start_monotonic = None

    def snapshot(self) -> RunnerState:
        with self._lock:
            elapsed = (
                round(time.monotonic() - self._start_monotonic, 1)
                if self._running and self._start_monotonic is not None
                else None
            )
            return RunnerState(
                running=self._running,
                threads=self._threads,
                duration_target_s=self._duration_target_s,
                elapsed_s=elapsed,
                latest_hashrate_10s=self._latest_10s,
                latest_hashrate_60s=self._latest_60s,
                last_result=self._last_result,
                error=self._error,
            )


# Single shared instance — MacMine Lab only ever runs one benchmark at a time.
benchmark_runner = BenchmarkRunner()
