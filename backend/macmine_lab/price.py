"""XMR/USD price lookup, abstracted behind a PriceProvider so the backing
API can be swapped later without touching callers.

Cached in SQLite (price_snapshots) so we don't hammer the public API — a
cached value younger than CACHE_TTL_S is reused. On failure, callers get
None; nothing here ever fabricates a price.
"""

from __future__ import annotations

import datetime
import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass

from . import db

CACHE_TTL_S = 300  # 5 minutes


@dataclass
class PriceSnapshot:
    price_usd: float
    source: str
    fetched_at: str


class PriceProvider(ABC):
    @abstractmethod
    def fetch(self) -> PriceSnapshot | None:
        """Returns None on any failure — never fabricates a price."""


class CoinGeckoPriceProvider(PriceProvider):
    URL = "https://api.coingecko.com/api/v3/simple/price?ids=monero&vs_currencies=usd"
    SOURCE = "CoinGecko"

    def fetch(self) -> PriceSnapshot | None:
        try:
            with urllib.request.urlopen(self.URL, timeout=5.0) as resp:
                data = json.loads(resp.read())
            price = data["monero"]["usd"]
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError, OSError):
            return None
        return PriceSnapshot(
            price_usd=float(price),
            source=self.SOURCE,
            fetched_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )


_default_provider: PriceProvider = CoinGeckoPriceProvider()


def get_price(force_refresh: bool = False) -> PriceSnapshot | None:
    """Cached lookup: reuses a recent SQLite snapshot instead of hitting the
    API every call. Returns None (never a fabricated price) if there's no
    usable cache and the live fetch also fails."""
    if not force_refresh:
        cached = db.get_latest_price_snapshot()
        if cached:
            age_s = (
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.datetime.fromisoformat(cached["fetched_at"])
            ).total_seconds()
            if age_s < CACHE_TTL_S:
                return PriceSnapshot(cached["price_usd"], cached["source"], cached["fetched_at"])

    fresh = _default_provider.fetch()
    if fresh:
        db.init_db()
        db.insert_price_snapshot(fresh.price_usd, fresh.source, fresh.fetched_at)
        return fresh

    # Live fetch failed — fall back to whatever cache exists, however old,
    # rather than showing nothing. Still real data, just stale.
    cached = db.get_latest_price_snapshot()
    if cached:
        return PriceSnapshot(cached["price_usd"], cached["source"], cached["fetched_at"])
    return None
