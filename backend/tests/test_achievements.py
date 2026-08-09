"""Tests for First Penny progress + achievement unlock logic. Network/price
are mocked (deterministic values); the DB is isolated per test."""

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from macmine_lab import achievements, db
from macmine_lab.network import NetworkSnapshot
from macmine_lab.price import PriceSnapshot


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return db


@dataclass
class _FakeBenchmark:
    avg_hs: float
    duration: float
    threads: int = 4
    duration_target_s: int = 30
    xmrig_version: str = "6.26.0"
    peak_hs: float = 0.0
    low_hs: float = 0.0
    hs_per_thread: float = 0.0
    final_thermal_state: str = "NORMAL"
    stopped_reason: str = "duration reached"
    hashrate_samples: list = None
    telemetry_samples: list = None
    started_at: str = "2026-01-01T00:00:00+00:00"
    ended_at: str = "2026-01-01T00:00:30+00:00"

    def __post_init__(self):
        self.duration_actual_s = self.duration
        if self.hashrate_samples is None:
            self.hashrate_samples = []
        if self.telemetry_samples is None:
            self.telemetry_samples = []
        if not self.peak_hs:
            self.peak_hs = self.avg_hs


FAKE_NETWORK = NetworkSnapshot(
    difficulty=1e11, network_hash_rate=1_000_000.0, block_reward_xmr=0.6,
    block_time_s=120.0, height=3_000_000, source="test", fetched_at="2026-01-01T00:00:00+00:00",
)
FAKE_PRICE = PriceSnapshot(price_usd=100.0, source="test", fetched_at="2026-01-01T00:00:00+00:00")


def test_no_activity_yields_zero_progress_and_no_unlocks(isolated_db):
    with patch("macmine_lab.achievements.network_module.get_network_snapshot", return_value=FAKE_NETWORK), \
         patch("macmine_lab.achievements.price_module.get_price", return_value=FAKE_PRICE):
        state = achievements.get_first_penny_state()

    assert state["estimated_usd_total"] == 0.0
    assert state["total_hashes"] == 0
    assert all(not a["unlocked"] for a in state["achievements"])


def test_benchmark_hashes_count_toward_first_hash_but_not_earnings(isolated_db):
    db.insert_benchmark_run(_FakeBenchmark(avg_hs=1000.0, duration=30.0))

    with patch("macmine_lab.achievements.network_module.get_network_snapshot", return_value=FAKE_NETWORK), \
         patch("macmine_lab.achievements.price_module.get_price", return_value=FAKE_PRICE):
        state = achievements.get_first_penny_state()

    assert state["total_hashes"] == 30_000  # 1000 H/s * 30s, real measured values
    assert state["estimated_usd_total"] == 0.0  # benchmark mode never touches a pool/wallet
    first_hash = next(a for a in state["achievements"] if a["key"] == "first_hash")
    assert first_hash["unlocked"] is True
    first_penny = next(a for a in state["achievements"] if a["key"] == "first_penny")
    assert first_penny["unlocked"] is False


def test_mining_session_unlocks_first_share_and_accrues_estimate(isolated_db):
    pool_id = db.insert_pool("P", "pool.example.com", 3333, False, None, None, None)
    wallet_id = db.insert_wallet("4" + "x" * 94, "standard", None)
    session_id = db.insert_mining_session_start(pool_id, wallet_id, 4, "2026-01-01T00:00:00+00:00")
    db.finalize_mining_session(
        session_id, "2026-01-01T01:00:00+00:00", duration_s=3600.0, avg_hs=1000.0,
        peak_hs=1100.0, shares_good=2, shares_total=2, hashes_total=3_600_000,
        stopped_reason="manual", hashrate_samples=[],
    )

    with patch("macmine_lab.achievements.network_module.get_network_snapshot", return_value=FAKE_NETWORK), \
         patch("macmine_lab.achievements.price_module.get_price", return_value=FAKE_PRICE):
        state = achievements.get_first_penny_state()

    # my_share = 1000/1_000_000 = 0.001; blocks/day = 720; xmr/day = 0.432
    # xmr/hour = 0.018; usd/hour = 1.8; 1 hour session -> $1.80 estimated
    assert round(state["estimated_usd_total"], 4) == 1.8
    assert state["total_shares_good"] == 2

    first_share = next(a for a in state["achievements"] if a["key"] == "first_share")
    assert first_share["unlocked"] is True
    million = next(a for a in state["achievements"] if a["key"] == "million_hashes")
    assert million["unlocked"] is True  # 3,600,000 real hashes >= 1,000,000

    for key in ("first_penny", "five_cents", "ten_cents", "quarter", "half_dollar", "one_dollar"):
        assert next(a for a in state["achievements"] if a["key"] == key)["unlocked"] is True


def test_first_payout_never_auto_unlocks(isolated_db):
    pool_id = db.insert_pool("P", "pool.example.com", 3333, False, None, None, None)
    wallet_id = db.insert_wallet("4" + "x" * 94, "standard", None)
    session_id = db.insert_mining_session_start(pool_id, wallet_id, 4, "2026-01-01T00:00:00+00:00")
    db.finalize_mining_session(
        session_id, "2026-01-02T00:00:00+00:00", duration_s=86400.0, avg_hs=100_000.0,
        peak_hs=100_000.0, shares_good=999, shares_total=1000, hashes_total=8_640_000_000,
        stopped_reason="manual", hashrate_samples=[],
    )
    with patch("macmine_lab.achievements.network_module.get_network_snapshot", return_value=FAKE_NETWORK), \
         patch("macmine_lab.achievements.price_module.get_price", return_value=FAKE_PRICE):
        state = achievements.get_first_penny_state()

    payout = next(a for a in state["achievements"] if a["key"] == "first_payout")
    assert payout["unlocked"] is False
    assert payout.get("unavailable") is True


def test_unlocking_is_idempotent_and_persists_timestamp(isolated_db):
    db.insert_benchmark_run(_FakeBenchmark(avg_hs=1000.0, duration=30.0))
    with patch("macmine_lab.achievements.network_module.get_network_snapshot", return_value=FAKE_NETWORK), \
         patch("macmine_lab.achievements.price_module.get_price", return_value=FAKE_PRICE):
        state1 = achievements.get_first_penny_state()
        state2 = achievements.get_first_penny_state()

    a1 = next(a for a in state1["achievements"] if a["key"] == "first_hash")
    a2 = next(a for a in state2["achievements"] if a["key"] == "first_hash")
    assert a1["unlocked_at"] == a2["unlocked_at"]  # didn't re-stamp on second call


def test_network_or_price_unavailable_reports_honestly(isolated_db):
    pool_id = db.insert_pool("P", "pool.example.com", 3333, False, None, None, None)
    wallet_id = db.insert_wallet("4" + "x" * 94, "standard", None)
    session_id = db.insert_mining_session_start(pool_id, wallet_id, 4, "2026-01-01T00:00:00+00:00")
    db.finalize_mining_session(
        session_id, "2026-01-01T01:00:00+00:00", duration_s=3600.0, avg_hs=1000.0,
        peak_hs=1000.0, shares_good=1, shares_total=1, hashes_total=3_600_000,
        stopped_reason="manual", hashrate_samples=[],
    )
    with patch("macmine_lab.achievements.network_module.get_network_snapshot", return_value=None), \
         patch("macmine_lab.achievements.price_module.get_price", return_value=FAKE_PRICE):
        state = achievements.get_first_penny_state()

    assert state["estimated_usd_total"] == 0.0
    assert "unavailable" in state["estimate_basis"].lower()
