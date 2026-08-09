"""Tests for the network-snapshot cache logic — same pattern as
test_price.py. The real xmrchain.net fetch (including the fallback to
height-1 for a not-yet-fully-indexed tip block) was verified manually."""

import datetime
from unittest.mock import patch

import pytest

from macmine_lab import db, network


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return db


def _snapshot(**overrides):
    defaults = dict(
        difficulty=1e11,
        network_hash_rate=5e9,
        block_reward_xmr=0.6,
        block_time_s=120.0,
        height=3_000_000,
        source="test",
        fetched_at="2026-01-01T00:00:00+00:00",
    )
    defaults.update(overrides)
    return network.NetworkSnapshot(**defaults)


def test_get_network_snapshot_fetches_and_caches(isolated_db):
    with patch.object(network._default_provider, "fetch", return_value=_snapshot()):
        result = network.get_network_snapshot()
    assert result.height == 3_000_000
    assert db.get_latest_network_snapshot()["height"] == 3_000_000


def test_get_network_snapshot_reuses_fresh_cache(isolated_db):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.insert_network_snapshot(1e11, 5e9, 0.6, 120.0, 42, "cached", now)

    with patch.object(network._default_provider, "fetch") as mock_fetch:
        result = network.get_network_snapshot()
    mock_fetch.assert_not_called()
    assert result.height == 42


def test_get_network_snapshot_falls_back_to_stale_cache(isolated_db):
    old = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).isoformat()
    db.insert_network_snapshot(1e11, 5e9, 0.6, 120.0, 99, "old", old)

    with patch.object(network._default_provider, "fetch", return_value=None):
        result = network.get_network_snapshot()
    assert result.height == 99


def test_get_network_snapshot_none_when_no_cache_and_fetch_fails(isolated_db):
    with patch.object(network._default_provider, "fetch", return_value=None):
        result = network.get_network_snapshot()
    assert result is None
