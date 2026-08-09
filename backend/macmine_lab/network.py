"""Monero network stats (difficulty, network hashrate, current block
reward) — abstracted behind a NetworkProvider, same caching/failure
philosophy as price.py: never fabricate a value, fall back to a stale
cache before giving up entirely, return None if there's truly nothing.

Source is xmrchain.net, a community Monero block explorer — not the
official Monero project. That's disclosed everywhere this data is shown.
"""

from __future__ import annotations

import datetime
import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass

from . import db

CACHE_TTL_S = 150  # network stats move roughly once per block (~120s)
ATOMIC_UNITS_PER_XMR = 1_000_000_000_000


@dataclass
class NetworkSnapshot:
    difficulty: float
    network_hash_rate: float
    block_reward_xmr: float
    block_time_s: float
    height: int
    source: str
    fetched_at: str


class NetworkProvider(ABC):
    @abstractmethod
    def fetch(self) -> NetworkSnapshot | None: ...


class XmrchainNetworkProvider(NetworkProvider):
    INFO_URL = "https://xmrchain.net/api/networkinfo"
    BLOCK_URL = "https://xmrchain.net/api/block/{height}"
    SOURCE = "xmrchain.net (community explorer)"

    def _get_json(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": "MacMineLab/1.0"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            return json.loads(resp.read())

    def _coinbase_reward_atomic(self, height: int) -> int:
        block = self._get_json(self.BLOCK_URL.format(height=height))["data"]
        coinbase = next(tx for tx in block["txs"] if tx.get("coinbase"))
        return coinbase["xmr_outputs"]

    def fetch(self) -> NetworkSnapshot | None:
        try:
            info = self._get_json(self.INFO_URL)["data"]
            height = info["height"]

            try:
                # The very newest block occasionally isn't fully indexed
                # yet (observed during development) — fall back one block.
                reward_atomic = self._coinbase_reward_atomic(height)
            except KeyError:
                reward_atomic = self._coinbase_reward_atomic(height - 1)
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError, StopIteration, OSError):
            return None

        return NetworkSnapshot(
            difficulty=float(info["difficulty"]),
            network_hash_rate=float(info["hash_rate"]),
            block_reward_xmr=reward_atomic / ATOMIC_UNITS_PER_XMR,
            block_time_s=float(info["target"]),
            height=height,
            source=self.SOURCE,
            fetched_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )


_default_provider: NetworkProvider = XmrchainNetworkProvider()


def get_network_snapshot(force_refresh: bool = False) -> NetworkSnapshot | None:
    if not force_refresh:
        cached = db.get_latest_network_snapshot()
        if cached:
            age_s = (
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.datetime.fromisoformat(cached["fetched_at"])
            ).total_seconds()
            if age_s < CACHE_TTL_S:
                return _snapshot_from_row(cached)

    fresh = _default_provider.fetch()
    if fresh:
        db.init_db()
        db.insert_network_snapshot(
            fresh.difficulty, fresh.network_hash_rate, fresh.block_reward_xmr,
            fresh.block_time_s, fresh.height, fresh.source, fresh.fetched_at,
        )
        return fresh

    cached = db.get_latest_network_snapshot()
    if cached:
        return _snapshot_from_row(cached)
    return None


def _snapshot_from_row(row: dict) -> NetworkSnapshot:
    return NetworkSnapshot(
        difficulty=row["difficulty"],
        network_hash_rate=row["network_hash_rate"],
        block_reward_xmr=row["block_reward_xmr"],
        block_time_s=row["block_time_s"],
        height=row["height"],
        source=row["source"],
        fetched_at=row["fetched_at"],
    )
