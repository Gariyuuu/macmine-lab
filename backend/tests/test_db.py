"""Tests for the SQLite persistence layer, using a throwaway DB file per test."""

from dataclasses import dataclass

import pytest

from macmine_lab import db, hardware


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return db


@dataclass
class _FakeBenchmarkResult:
    threads: int
    duration_target_s: int
    duration_actual_s: float
    started_at: str
    ended_at: str
    xmrig_version: str | None
    avg_hs: float | None
    peak_hs: float | None
    low_hs: float | None
    hs_per_thread: float | None
    final_thermal_state: str
    stopped_reason: str
    hashrate_samples: list
    telemetry_samples: list


def _sample_result(threads=4, avg_hs=2000.0):
    return _FakeBenchmarkResult(
        threads=threads,
        duration_target_s=30,
        duration_actual_s=32.1,
        started_at="2026-01-01T00:00:00+00:00",
        ended_at="2026-01-01T00:00:32+00:00",
        xmrig_version="6.26.0",
        avg_hs=avg_hs,
        peak_hs=avg_hs + 500,
        low_hs=avg_hs - 500,
        hs_per_thread=avg_hs / threads,
        final_thermal_state="NORMAL",
        stopped_reason="duration reached",
        hashrate_samples=[{"t_offset_s": 10.0, "hashrate_10s": avg_hs, "hashrate_60s": None}],
        telemetry_samples=[],
    )


def test_insert_and_list_benchmark_runs(isolated_db):
    run_id = db.insert_benchmark_run(_sample_result(threads=6, avg_hs=3000.0))
    assert run_id == 1

    runs = db.list_benchmark_runs()
    assert len(runs) == 1
    assert runs[0]["threads"] == 6
    assert runs[0]["avg_hs"] == 3000.0


def test_get_benchmark_run_includes_samples(isolated_db):
    run_id = db.insert_benchmark_run(_sample_result())
    run = db.get_benchmark_run(run_id)
    assert run is not None
    assert run["hashrate_samples"][0]["hashrate_10s"] == 2000.0


def test_get_benchmark_run_missing_returns_none(isolated_db):
    assert db.get_benchmark_run(9999) is None


def test_list_benchmark_runs_respects_limit_and_order(isolated_db):
    for i in range(5):
        db.insert_benchmark_run(_sample_result(threads=i + 1))
    runs = db.list_benchmark_runs(limit=2)
    assert len(runs) == 2
    # newest first
    assert runs[0]["threads"] == 5
    assert runs[1]["threads"] == 4


def test_insert_telemetry_sample_and_history(isolated_db):
    telemetry = hardware.SystemTelemetry(
        battery=hardware.BatteryInfo(True, 87, False, False, "discharging"),
        thermal=hardware.ThermalInfo("NORMAL", 100),
        cpu=hardware.CpuLoadInfo(10.0, 5.0, 85.0, 1.2, 1.5, 1.8),
        memory=hardware.MemoryInfo(25769803776, 20.0, 4.0),
    )
    db.insert_telemetry_sample(telemetry, miner_running=True, miner_cpu_percent=54.2)

    history = db.list_telemetry_samples(since_minutes=60)
    assert len(history) == 1
    assert history[0]["battery_percent"] == 87
    assert history[0]["miner_running"] == 1
    assert history[0]["miner_cpu_percent"] == 54.2


def test_settings_roundtrip(isolated_db):
    assert db.get_setting("nonexistent") is None
    assert db.get_setting("nonexistent", "fallback") == "fallback"

    db.set_setting("mining_mode", "eco")
    assert db.get_setting("mining_mode") == "eco"

    db.set_setting("mining_mode", "balanced")
    assert db.get_setting("mining_mode") == "balanced"
