"""First Penny progress + achievements.

Unlock conditions are computed from real, measured facts only: cumulative
hashes (from benchmark_runs + mining_sessions), cumulative real accepted
shares (mining_sessions only — benchmark mode never touches a pool), and
cumulative ESTIMATED USD earnings. That estimate is each finished mining
session's own real measured average hashrate combined with CURRENT network
difficulty and CURRENT XMR price (not the conditions at the time the
session actually ran) — an approximation, and labeled as one everywhere
it's shown. It is not derived from a real pool or wallet balance, which
this version has no way to verify.

"First Payout" is defined below but can never auto-unlock: confirming an
actual payout would need wallet-balance or blockchain integration this
version doesn't have. Faking that would defeat the entire point of this
project, so it just stays locked with an honest explanation.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from . import db
from . import network as network_module
from . import price as price_module
from .economics import estimate_earnings

FIRST_PENNY_TARGET_USD = 0.01
MILESTONES_USD = [0.01, 0.05, 0.10, 0.25, 0.50, 1.00]

_MILESTONE_KEYS = {
    0.01: "first_penny",
    0.05: "five_cents",
    0.10: "ten_cents",
    0.25: "quarter",
    0.50: "half_dollar",
    1.00: "one_dollar",
}

ACHIEVEMENTS = [
    {"key": "first_hash", "icon": "⛏️", "name": "First Hash",
     "description": "Submitted your first RandomX hash."},
    {"key": "first_share", "icon": "✅", "name": "First Share",
     "description": "Your first share was accepted by a pool."},
    {"key": "million_hashes", "icon": "🟢", "name": "1,000,000 Hashes",
     "description": "Calculated one million hashes total."},
    {"key": "first_penny", "icon": "💰", "name": "First Penny",
     "description": "Estimated mining earnings crossed $0.01."},
    {"key": "five_cents", "icon": "💰", "name": "$0.05",
     "description": "Estimated mining earnings crossed $0.05."},
    {"key": "ten_cents", "icon": "💰", "name": "$0.10",
     "description": "Estimated mining earnings crossed $0.10."},
    {"key": "quarter", "icon": "💰", "name": "$0.25",
     "description": "Estimated mining earnings crossed $0.25."},
    {"key": "half_dollar", "icon": "💰", "name": "$0.50",
     "description": "Estimated mining earnings crossed $0.50."},
    {"key": "one_dollar", "icon": "💰", "name": "$1.00",
     "description": "Estimated mining earnings crossed $1.00."},
    {"key": "first_payout", "icon": "🪙", "name": "First Payout",
     "description": "A real, confirmed mining payout — requires wallet balance "
                     "verification, not available in this version.",
     "unavailable": True},
]


@dataclass
class CumulativeStats:
    total_hashes: int
    total_shares_good: int
    total_shares_total: int
    total_mining_seconds: float
    estimated_usd_total: float
    estimate_basis: str


def compute_cumulative_stats() -> CumulativeStats:
    benchmark_runs = db.list_benchmark_runs(limit=100_000)
    mining_sessions = db.list_finished_mining_sessions()

    total_hashes = 0
    for run in benchmark_runs:
        # benchmark_runs stores avg/peak hashrate, not a raw hash count —
        # approximate real hashes from avg_hs x measured duration.
        if run.get("avg_hs") and run.get("duration_actual_s"):
            total_hashes += int(run["avg_hs"] * run["duration_actual_s"])

    total_shares_good = 0
    total_shares_total = 0
    total_mining_seconds = 0.0
    for s in mining_sessions:
        total_hashes += s.get("hashes_total") or 0
        total_shares_good += s.get("shares_good") or 0
        total_shares_total += s.get("shares_total") or 0
        total_mining_seconds += s.get("duration_s") or 0.0

    estimated_usd_total = 0.0
    basis = "no completed mining sessions yet"
    net = network_module.get_network_snapshot()
    pr = price_module.get_price()
    if mining_sessions and net and pr:
        for s in mining_sessions:
            if not s.get("avg_hs") or not s.get("duration_s"):
                continue
            est = estimate_earnings(s["avg_hs"], net, pr)
            estimated_usd_total += est.usd_per_hour * (s["duration_s"] / 3600)
        basis = (
            f"sum of each mining session's real average hashrate x its real "
            f"duration, valued at current network difficulty (height "
            f"{net.height}) and current XMR price — not the conditions at "
            f"the time each session actually ran"
        )
    elif mining_sessions:
        basis = "network/price data unavailable right now — cannot estimate"

    return CumulativeStats(
        total_hashes=total_hashes,
        total_shares_good=total_shares_good,
        total_shares_total=total_shares_total,
        total_mining_seconds=total_mining_seconds,
        estimated_usd_total=estimated_usd_total,
        estimate_basis=basis,
    )


def refresh_achievements(stats: CumulativeStats) -> list[str]:
    """Checks real measured facts against unlock conditions and persists any
    newly-unlocked achievements. Returns keys newly unlocked this call."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    newly_unlocked: list[str] = []

    def maybe_unlock(key: str, condition: bool) -> None:
        if condition and db.unlock_achievement(key, now):
            newly_unlocked.append(key)

    maybe_unlock("first_hash", stats.total_hashes > 0)
    maybe_unlock("first_share", stats.total_shares_good > 0)
    maybe_unlock("million_hashes", stats.total_hashes >= 1_000_000)
    for usd_threshold, key in _MILESTONE_KEYS.items():
        maybe_unlock(key, stats.estimated_usd_total >= usd_threshold)

    return newly_unlocked


def get_first_penny_state() -> dict:
    db.init_db()
    stats = compute_cumulative_stats()
    refresh_achievements(stats)
    unlocked = db.list_unlocked_achievements()

    achievements = [
        {**a, "unlocked": a["key"] in unlocked, "unlocked_at": unlocked.get(a["key"])}
        for a in ACHIEVEMENTS
    ]

    next_milestone = next((m for m in MILESTONES_USD if stats.estimated_usd_total < m), None)

    return {
        "estimated_usd_total": round(stats.estimated_usd_total, 6),
        "target_usd": FIRST_PENNY_TARGET_USD,
        "next_milestone_usd": next_milestone,
        "progress_to_next_milestone": (
            min(stats.estimated_usd_total / next_milestone, 1.0) if next_milestone else 1.0
        ),
        "total_hashes": stats.total_hashes,
        "total_shares_good": stats.total_shares_good,
        "total_shares_total": stats.total_shares_total,
        "total_mining_seconds": stats.total_mining_seconds,
        "estimate_basis": stats.estimate_basis,
        "achievements": achievements,
    }
