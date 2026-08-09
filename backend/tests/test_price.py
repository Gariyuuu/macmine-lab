"""Tests for the price cache logic. The real CoinGecko fetch was verified
manually (see CHANGELOG); here we mock the provider to test caching,
staleness, and fallback-to-stale-cache-on-failure without hitting the
network in an automated test run."""

from unittest.mock import patch

import pytest

from macmine_lab import db, price


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return db


def test_get_price_fetches_and_caches(isolated_db):
    fake_snapshot = price.PriceSnapshot(123.45, "test-source", "2026-01-01T00:00:00+00:00")
    with patch.object(price._default_provider, "fetch", return_value=fake_snapshot):
        result = price.get_price()
    assert result.price_usd == 123.45
    assert db.get_latest_price_snapshot()["price_usd"] == 123.45


def test_get_price_reuses_fresh_cache_without_refetching(isolated_db):
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.insert_price_snapshot(500.0, "cached", now)

    with patch.object(price._default_provider, "fetch") as mock_fetch:
        result = price.get_price()
    mock_fetch.assert_not_called()
    assert result.price_usd == 500.0


def test_get_price_falls_back_to_stale_cache_on_fetch_failure(isolated_db):
    import datetime
    old = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat()
    db.insert_price_snapshot(200.0, "old-cache", old)

    with patch.object(price._default_provider, "fetch", return_value=None):
        result = price.get_price()
    assert result.price_usd == 200.0  # stale but real, not fabricated


def test_get_price_returns_none_when_no_cache_and_fetch_fails(isolated_db):
    with patch.object(price._default_provider, "fetch", return_value=None):
        result = price.get_price()
    assert result is None


def test_force_refresh_bypasses_fresh_cache(isolated_db):
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.insert_price_snapshot(500.0, "cached", now)

    fresh = price.PriceSnapshot(999.0, "fresh", "2026-01-01T00:00:00+00:00")
    with patch.object(price._default_provider, "fetch", return_value=fresh):
        result = price.get_price(force_refresh=True)
    assert result.price_usd == 999.0
