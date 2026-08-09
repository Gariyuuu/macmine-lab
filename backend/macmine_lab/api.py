"""MacMine Lab local backend — FastAPI app.

Binds to 127.0.0.1 only (see cli.py `serve` command). No auth, no cloud,
because nothing here is reachable from outside this Mac. Every response is
either a real measurement, a real stored record, or an explicit null/empty
value — nothing here fabricates data when a measurement is unavailable.
"""

from __future__ import annotations

import asyncio
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import benchmark, db, hardware, integrity, miner
from .runner import benchmark_runner

TELEMETRY_SAMPLE_INTERVAL_S = 8  # per project's telemetry sampling strategy


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    db.init_db()
    _sampler_stop.clear()
    global _sampler_thread
    _sampler_thread = threading.Thread(target=_telemetry_sampler_loop, daemon=True)
    _sampler_thread.start()
    yield
    _sampler_stop.set()
    if _sampler_thread:
        _sampler_thread.join(timeout=2)


app = FastAPI(title="MacMine Lab", version="0.2.0", lifespan=_lifespan)

# The dashboard (Phase 3) runs on a different localhost port during
# development; both ends are 127.0.0.1-only so this is still fully local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_sampler_stop = threading.Event()
_sampler_thread: threading.Thread | None = None


def _telemetry_sampler_loop() -> None:
    while not _sampler_stop.is_set():
        try:
            telemetry = hardware.sample_telemetry()
            status = miner.get_status()
            db.insert_telemetry_sample(telemetry, status.running, status.cpu_percent)
        except Exception:
            pass  # a single failed sample must never crash the sampler loop
        _sampler_stop.wait(TELEMETRY_SAMPLE_INTERVAL_S)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/hardware")
def get_hardware():
    return asdict(hardware.detect_hardware())


@app.get("/api/telemetry/live")
def get_telemetry_live():
    telemetry = hardware.sample_telemetry()
    status = miner.get_status()
    return {
        "telemetry": asdict(telemetry),
        "miner_running": status.running,
        "miner_cpu_percent": status.cpu_percent,
    }


@app.get("/api/telemetry/history")
def get_telemetry_history(minutes: int = 60, limit: int = 2000):
    return db.list_telemetry_samples(since_minutes=minutes, limit=limit)


@app.get("/api/integrity")
def get_integrity():
    record = db.get_latest_miner_installation()
    if not record:
        raise HTTPException(status_code=404, detail="No integrity record yet — run `./macmine setup`.")
    return record


@app.get("/api/miner/status")
def get_miner_status():
    return asdict(miner.get_status())


@app.post("/api/miner/stop")
def post_miner_stop():
    ok = miner.stop_tracked()
    if not ok:
        raise HTTPException(status_code=500, detail="Could not confirm the miner process stopped.")
    return {"stopped": True}


@app.post("/api/benchmark/start")
def post_benchmark_start(threads: int | None = None, duration_seconds: int = 30):
    if duration_seconds not in (30, 60, 300):
        raise HTTPException(status_code=400, detail="duration_seconds must be 30, 60, or 300")
    hw = hardware.detect_hardware()
    resolved_threads = threads or hw.total_cores
    if not resolved_threads:
        raise HTTPException(status_code=400, detail="threads not given and could not be auto-detected")
    if not integrity.find_xmrig_binary():
        raise HTTPException(status_code=409, detail="xmrig is not installed — run `./macmine setup`.")
    try:
        benchmark_runner.start(resolved_threads, duration_seconds)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"started": True, "threads": resolved_threads, "duration_seconds": duration_seconds}


@app.get("/api/benchmark/live")
def get_benchmark_live():
    return asdict(benchmark_runner.snapshot())


@app.get("/api/benchmark/history")
def get_benchmark_history(limit: int = 50):
    return benchmark.list_saved_results(limit=limit)


@app.get("/api/benchmark/{run_id}")
def get_benchmark_run(run_id: int):
    run = db.get_benchmark_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"No benchmark run with id {run_id}")
    return run


@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    """Pushes real telemetry + miner + benchmark state once per second —
    the 1-second UI refresh cadence from the project's telemetry strategy."""
    await websocket.accept()
    try:
        while True:
            telemetry, status = await asyncio.gather(
                asyncio.to_thread(hardware.sample_telemetry),
                asyncio.to_thread(miner.get_status),
            )
            payload = {
                "t": time.time(),
                "telemetry": asdict(telemetry),
                "miner": asdict(status),
                "benchmark": asdict(benchmark_runner.snapshot()),
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
