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

from pydantic import BaseModel

from . import (
    achievements, analytics, benchmark, calibration, db, economics, hardware,
    integrity, miner, mining, network, notifications, paths, pools, price, safety, wallet,
)
from .mining_runner import mining_runner
from .runner import benchmark_runner
from .safety import safety_manager

TELEMETRY_SAMPLE_INTERVAL_S = 8  # per project's telemetry sampling strategy


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    db.init_db()
    _sampler_stop.clear()
    global _sampler_thread
    _sampler_thread = threading.Thread(target=_telemetry_sampler_loop, daemon=True)
    _sampler_thread.start()
    safety_manager.start()
    yield
    _sampler_stop.set()
    if _sampler_thread:
        _sampler_thread.join(timeout=2)
    safety_manager.stop()


app = FastAPI(title="MacMine Lab", version="0.6.0", lifespan=_lifespan)

# The dashboard runs on whatever localhost port Next.js picks (3000 is
# frequently already taken by another local project) — match any local
# port rather than hardcoding one, since both ends never leave this Mac.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
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


class WalletCreateRequest(BaseModel):
    address: str
    label: str | None = None


class PoolCreateRequest(BaseModel):
    name: str
    host: str
    port: int
    tls: bool = False
    worker_name: str | None = None
    password: str | None = None
    notes: str | None = None


class PoolConnectionTestRequest(BaseModel):
    host: str
    port: int
    tls: bool = False


class MiningStartRequest(BaseModel):
    pool_id: int
    wallet_id: int
    threads: int


@app.post("/api/wallets/validate")
def post_validate_wallet(body: WalletCreateRequest):
    """Local format check only — no network call, and this never sees a
    seed phrase or private key (there's no field for one)."""
    return asdict(wallet.validate_monero_address(body.address))


@app.post("/api/wallets")
def post_create_wallet(body: WalletCreateRequest):
    result = wallet.validate_monero_address(body.address)
    if not result.valid:
        raise HTTPException(status_code=400, detail=result.reason)
    wallet_id = db.insert_wallet(body.address.strip(), result.kind, body.label)
    return db.get_wallet(wallet_id)


@app.get("/api/wallets")
def get_wallets():
    return db.list_wallets()


@app.delete("/api/wallets/{wallet_id}")
def delete_wallet_route(wallet_id: int):
    if not db.get_wallet(wallet_id):
        raise HTTPException(status_code=404, detail=f"No wallet with id {wallet_id}")
    db.delete_wallet(wallet_id)
    return {"deleted": True}


@app.post("/api/pools")
def post_create_pool(body: PoolCreateRequest):
    pool_id = db.insert_pool(
        body.name, body.host, body.port, body.tls, body.worker_name, body.password, body.notes
    )
    return db.get_pool(pool_id)


@app.get("/api/pools")
def get_pools():
    return db.list_pools()


@app.delete("/api/pools/{pool_id}")
def delete_pool_route(pool_id: int):
    if not db.get_pool(pool_id):
        raise HTTPException(status_code=404, detail=f"No pool with id {pool_id}")
    db.delete_pool(pool_id)
    return {"deleted": True}


@app.post("/api/pools/test-connection")
def post_test_pool_connection(body: PoolConnectionTestRequest):
    """Plain TCP/TLS reachability check — no wallet, no mining protocol.
    Proves the pool server is reachable; whether your wallet address is
    accepted only shows up once you actually start mining."""
    return asdict(pools.test_pool_connection(body.host, body.port, body.tls))


@app.post("/api/mining/start")
def post_mining_start(body: MiningStartRequest):
    pool = db.get_pool(body.pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail=f"No pool with id {body.pool_id}")
    w = db.get_wallet(body.wallet_id)
    if not w:
        raise HTTPException(status_code=404, detail=f"No wallet with id {body.wallet_id}")
    if not integrity.find_xmrig_binary():
        raise HTTPException(status_code=409, detail="xmrig is not installed — run `./macmine setup`.")
    if miner.get_status().running:
        raise HTTPException(
            status_code=409, detail="MacMine Lab already has an xmrig process running. Stop it first."
        )
    try:
        mining_runner.start(pool, w, body.threads)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"started": True, "pool_id": pool["id"], "wallet_id": w["id"], "threads": body.threads}


@app.post("/api/mining/stop")
def post_mining_stop():
    """Signals the mining loop to stop on its next ~1s tick, which then
    SIGTERMs xmrig itself — not instant, but bounded to a few seconds, same
    as benchmark stop. Poll /api/mining/live to see when it's confirmed."""
    mining_runner.stop()
    return {"stopping": True}


@app.get("/api/mining/live")
def get_mining_live():
    return asdict(mining_runner.snapshot())


@app.get("/api/mining/history")
def get_mining_history(limit: int = 50):
    return db.list_mining_sessions(limit=limit)


@app.get("/api/mining/{session_id}")
def get_mining_session_detail(session_id: int):
    session = db.get_mining_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"No mining session with id {session_id}")
    return session


class EconomicsSettingsRequest(BaseModel):
    electricity_rate_usd_per_kwh: float | None = None
    power_draw_watts: float | None = None


@app.get("/api/economics/price")
def get_price_snapshot():
    snapshot = price.get_price()
    if not snapshot:
        raise HTTPException(status_code=503, detail="Price data unavailable — CoinGecko unreachable and no cache.")
    return asdict(snapshot)


@app.get("/api/economics/network")
def get_network_snapshot_route():
    snapshot = network.get_network_snapshot()
    if not snapshot:
        raise HTTPException(
            status_code=503, detail="Network data unavailable — xmrchain.net unreachable and no cache."
        )
    return asdict(snapshot)


@app.get("/api/economics/settings")
def get_economics_settings():
    rate = db.get_setting("electricity_rate_usd_per_kwh")
    watts = db.get_setting("power_draw_watts")
    return {
        "electricity_rate_usd_per_kwh": float(rate) if rate is not None else None,
        "power_draw_watts": float(watts) if watts is not None else None,
    }


@app.post("/api/economics/settings")
def post_economics_settings(body: EconomicsSettingsRequest):
    if body.electricity_rate_usd_per_kwh is not None:
        db.set_setting("electricity_rate_usd_per_kwh", str(body.electricity_rate_usd_per_kwh))
    if body.power_draw_watts is not None:
        db.set_setting("power_draw_watts", str(body.power_draw_watts))
    return get_economics_settings()


@app.get("/api/economics/estimate")
def get_earnings_estimate(hashrate_hs: float):
    net = network.get_network_snapshot()
    pr = price.get_price()
    if not net or not pr:
        raise HTTPException(
            status_code=503,
            detail="Cannot estimate earnings — price and/or network data unavailable right now.",
        )
    settings = get_economics_settings()
    estimate = economics.estimate_earnings(
        hashrate_hs, net, pr,
        power_draw_watts=settings["power_draw_watts"],
        electricity_rate_usd_per_kwh=settings["electricity_rate_usd_per_kwh"],
    )
    return asdict(estimate)


@app.get("/api/first-penny")
def get_first_penny():
    return achievements.get_first_penny_state()


class SafetySettingsRequest(BaseModel):
    safety_automation_enabled: bool | None = None
    allow_mining_on_battery: bool | None = None
    battery_pause_threshold_percent: int | None = None


@app.get("/api/safety/status")
def get_safety_status():
    return asdict(safety_manager.snapshot())


@app.get("/api/safety/settings")
def get_safety_settings():
    return asdict(safety.get_settings())


@app.post("/api/safety/settings")
def post_safety_settings(body: SafetySettingsRequest):
    if body.safety_automation_enabled is not None:
        db.set_setting("safety_automation_enabled", "true" if body.safety_automation_enabled else "false")
    if body.allow_mining_on_battery is not None:
        db.set_setting("allow_mining_on_battery", "true" if body.allow_mining_on_battery else "false")
    if body.battery_pause_threshold_percent is not None:
        if not (0 <= body.battery_pause_threshold_percent <= 100):
            raise HTTPException(status_code=400, detail="battery_pause_threshold_percent must be 0-100")
        db.set_setting("battery_pause_threshold_percent", str(body.battery_pause_threshold_percent))
    return asdict(safety.get_settings())


@app.get("/api/journal")
def get_journal(limit: int = 100):
    hw = hardware.detect_hardware()
    runs = db.list_benchmark_runs(limit=limit)
    annotated = [{**r, "result_label": calibration.label_result(r, runs)} for r in runs]
    recommendations = calibration.recommend_configs(runs, hw.total_cores or 8)
    return {
        "runs": annotated,
        "recommendations": {k: asdict(v) for k, v in recommendations.items()},
    }


@app.get("/api/analytics")
def get_analytics_route():
    return analytics.get_analytics()


@app.get("/api/logs/latest")
def get_latest_log(lines: int = 200):
    """Tail the most recent raw XMRig log MacMine Lab wrote. Real output
    only — if nothing has run yet, this returns an empty list, not
    fabricated log lines."""
    log_files = sorted(paths.LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime)
    if not log_files:
        return {"log_file": None, "lines": []}
    latest = log_files[-1]
    with open(latest, "r", errors="replace") as f:
        all_lines = f.readlines()
    return {"log_file": latest.name, "lines": [line.rstrip("\n") for line in all_lines[-lines:]]}


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
                "mining": asdict(mining_runner.snapshot()),
                "safety": asdict(safety_manager.snapshot()),
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
