"""Duration-controlled RandomX benchmarking, fully offline.

We deliberately avoid xmrig's `--stress` mode: it dials an external
xmrig.com stress-test server by default. Instead we use `--bench=10M`
(the maximum hash count XMRig's benchmark accepts) purely as a ceiling that
won't be reached within our test window, and enforce the actual 30s/1min/5min
duration ourselves — polling XMRig's *local* HTTP API (127.0.0.1 only, random
token, verified via lsof during development to make zero outbound
connections) for real hashrate samples, then stopping the process cleanly.
"""

from __future__ import annotations

import datetime
import json
import secrets
import socket
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

from . import hardware, miner, paths

MAX_BENCH_HASHES = "10M"  # ceiling XMRig accepts; never reached in a <=5min run
POLL_INTERVAL_S = 1.0
TELEMETRY_SAMPLE_EVERY_S = 5.0
DATASET_WARMUP_GRACE_S = 10.0  # RandomX dataset init before hashrate is meaningful


@dataclass
class HashrateSample:
    t_offset_s: float
    hashrate_10s: float | None
    hashrate_60s: float | None


@dataclass
class TelemetrySample:
    t_offset_s: float
    cpu_user_percent: float | None
    thermal_state: str
    battery_percent: int | None
    on_ac_power: bool | None


@dataclass
class BenchmarkResult:
    threads: int
    duration_target_s: int
    duration_actual_s: float
    started_at: str
    ended_at: str
    xmrig_version: str | None
    hashrate_samples: list
    telemetry_samples: list
    avg_hs: float | None
    peak_hs: float | None
    low_hs: float | None
    hs_per_thread: float | None
    final_thermal_state: str
    stopped_reason: str


def aggregate_stats(
    hashrate_samples: list[HashrateSample], threads: int
) -> tuple[float | None, float | None, float | None, float | None]:
    """Pure aggregation, factored out so it's unit-testable without xmrig.
    Returns (avg_hs, peak_hs, low_hs, hs_per_thread)."""
    valid_rates = [s.hashrate_10s for s in hashrate_samples if s.hashrate_10s is not None]
    if not valid_rates:
        return None, None, None, None
    avg_hs = sum(valid_rates) / len(valid_rates)
    peak_hs = max(valid_rates)
    low_hs = min(valid_rates)
    hs_per_thread = (avg_hs / threads) if threads else None
    return (
        round(avg_hs, 1),
        round(peak_hs, 1),
        round(low_hs, 1),
        round(hs_per_thread, 1) if hs_per_thread else None,
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _fetch_summary(port: int, token: str) -> dict | None:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/2/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, ValueError, ConnectionError):
        return None


def run_benchmark(threads: int, duration_seconds: int) -> BenchmarkResult:
    """Run a real, offline RandomX benchmark for `duration_seconds` wall-clock
    seconds using `threads` CPU threads, then stop the miner and return
    aggregated real results. Raises if xmrig isn't installed."""
    port = _free_port()
    token = secrets.token_hex(16)

    args = [
        f"--bench={MAX_BENCH_HASHES}",
        "-t", str(threads),
        "--http-host=127.0.0.1",
        f"--http-port={port}",
        f"--http-access-token={token}",
        "--no-color",
    ]

    started_at = datetime.datetime.now(datetime.timezone.utc)
    log_name = f"benchmark_{started_at.strftime('%Y%m%dT%H%M%SZ')}_{threads}t.log"
    proc, log_path = miner.launch(args, log_name)

    hashrate_samples: list[HashrateSample] = []
    telemetry_samples: list[TelemetrySample] = []
    stopped_reason = "duration reached"
    xmrig_version = None

    try:
        start = time.monotonic()
        last_telemetry_t = -TELEMETRY_SAMPLE_EVERY_S
        while True:
            elapsed = time.monotonic() - start

            if proc.poll() is not None:
                stopped_reason = f"xmrig exited early (code {proc.returncode})"
                break

            if elapsed >= duration_seconds:
                break

            summary = _fetch_summary(port, token)
            if summary:
                if xmrig_version is None:
                    xmrig_version = summary.get("version")
                hr = summary.get("hashrate", {}).get("total", [None, None, None])
                if elapsed >= DATASET_WARMUP_GRACE_S:
                    hashrate_samples.append(
                        HashrateSample(round(elapsed, 1), hr[0], hr[1])
                    )

            if elapsed - last_telemetry_t >= TELEMETRY_SAMPLE_EVERY_S:
                telemetry = hardware.sample_telemetry()
                telemetry_samples.append(
                    TelemetrySample(
                        round(elapsed, 1),
                        telemetry.cpu.user_percent,
                        telemetry.thermal.state,
                        telemetry.battery.percent,
                        telemetry.battery.on_ac_power,
                    )
                )
                last_telemetry_t = elapsed

            time.sleep(POLL_INTERVAL_S)
    finally:
        miner.stop(proc.pid)

    ended_at = datetime.datetime.now(datetime.timezone.utc)
    duration_actual = (ended_at - started_at).total_seconds()

    avg_hs, peak_hs, low_hs, hs_per_thread = aggregate_stats(hashrate_samples, threads)

    final_thermal_state = (
        telemetry_samples[-1].thermal_state if telemetry_samples else "UNAVAILABLE"
    )

    result = BenchmarkResult(
        threads=threads,
        duration_target_s=duration_seconds,
        duration_actual_s=round(duration_actual, 1),
        started_at=started_at.isoformat(),
        ended_at=ended_at.isoformat(),
        xmrig_version=xmrig_version,
        hashrate_samples=[asdict(s) for s in hashrate_samples],
        telemetry_samples=[asdict(s) for s in telemetry_samples],
        avg_hs=avg_hs,
        peak_hs=peak_hs,
        low_hs=low_hs,
        hs_per_thread=hs_per_thread,
        final_thermal_state=final_thermal_state,
        stopped_reason=stopped_reason,
    )
    _save_result(result)
    return result


def _save_result(result: BenchmarkResult) -> None:
    paths.ensure_data_dirs()
    started = result.started_at.replace(":", "").replace("-", "")
    out_path = paths.BENCHMARKS_DIR / f"{started}_{result.threads}t.json"
    with open(out_path, "w") as f:
        json.dump(asdict(result), f, indent=2)


def list_saved_results() -> list[dict]:
    paths.ensure_data_dirs()
    results = []
    for p in sorted(paths.BENCHMARKS_DIR.glob("*.json")):
        with open(p) as f:
            results.append(json.load(f))
    return results
