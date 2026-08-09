"""Tests for analytics aggregation — verifies the "don't fake a correlation
with too little data" guarantee as much as the happy path."""

import pytest

from macmine_lab import analytics, db


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return db


def _insert_benchmark(threads, avg_hs, thermal="NORMAL"):
    from dataclasses import dataclass

    @dataclass
    class _Fake:
        threads: int
        duration_target_s: int = 30
        duration_actual_s: float = 30.0
        started_at: str = "2026-01-01T00:00:00+00:00"
        ended_at: str = "2026-01-01T00:00:30+00:00"
        xmrig_version: str = "6.26.0"
        avg_hs: float = 0.0
        peak_hs: float = 0.0
        low_hs: float = 0.0
        hs_per_thread: float = 0.0
        final_thermal_state: str = "NORMAL"
        stopped_reason: str = "duration reached"
        hashrate_samples: list = None
        telemetry_samples: list = None

        def __post_init__(self):
            if self.hashrate_samples is None:
                self.hashrate_samples = []
            if self.telemetry_samples is None:
                self.telemetry_samples = []

    fake = _Fake(threads=threads, avg_hs=avg_hs, peak_hs=avg_hs, hs_per_thread=avg_hs / threads, final_thermal_state=thermal)
    db.insert_benchmark_run(fake)


def test_threads_vs_hashrate_unavailable_with_too_little_data(isolated_db):
    _insert_benchmark(4, 1000.0)
    series = analytics.threads_vs_hashrate()
    assert series.available is False
    assert "1" in series.reason


def test_threads_vs_hashrate_available_with_enough_data(isolated_db):
    _insert_benchmark(4, 1000.0)
    _insert_benchmark(8, 1800.0)
    series = analytics.threads_vs_hashrate()
    assert series.available is True
    assert len(series.points) == 2
    assert {"x": 4, "y": 1000.0, "label": "run #1"} in series.points


def test_threads_vs_efficiency_uses_hs_per_thread(isolated_db):
    _insert_benchmark(4, 1000.0)
    _insert_benchmark(8, 1600.0)
    series = analytics.threads_vs_efficiency()
    assert series.available is True
    ys = sorted(p["y"] for p in series.points)
    assert ys == [200.0, 250.0]


def test_session_duration_vs_hashrate_needs_completed_sessions(isolated_db):
    pool_id = db.insert_pool("P", "pool.example.com", 3333, False, None, None, None)
    wallet_id = db.insert_wallet("4" + "x" * 94, "standard", None)
    session_id = db.insert_mining_session_start(pool_id, wallet_id, 4, "2026-01-01T00:00:00+00:00")

    series_before = analytics.session_duration_vs_hashrate()
    assert series_before.available is False  # not finalized yet

    db.finalize_mining_session(
        session_id, "2026-01-01T01:00:00+00:00", duration_s=3600.0, avg_hs=1000.0,
        peak_hs=1000.0, shares_good=1, shares_total=1, hashes_total=3_600_000,
        stopped_reason="manual", hashrate_samples=[],
    )
    series_still_before = analytics.session_duration_vs_hashrate()
    assert series_still_before.available is False  # only 1 session — still below MIN_POINTS


def test_thermal_state_vs_hashrate_groups_by_state(isolated_db):
    _insert_benchmark(4, 1000.0, thermal="NORMAL")
    _insert_benchmark(4, 900.0, thermal="NORMAL")
    _insert_benchmark(6, 800.0, thermal="HOT")
    series = analytics.thermal_state_vs_hashrate()
    assert series.available is True
    by_label = {p["x"]: p["y"] for p in series.points}
    assert by_label["NORMAL"] == 950.0  # average of 1000 and 900
    assert by_label["HOT"] == 800.0


def test_get_analytics_returns_all_four_series_shape(isolated_db):
    result = analytics.get_analytics()
    assert set(result.keys()) == {
        "threads_vs_hashrate", "threads_vs_efficiency",
        "session_duration_vs_hashrate", "thermal_state_vs_hashrate",
    }
    for series in result.values():
        assert series["available"] is False  # empty DB
        assert series["points"] == []
