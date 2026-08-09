"""Simple, honest aggregations over real benchmark/mining data for the
Analytics page. Every series requires at least MIN_POINTS real data points
before it's considered "available" — with fewer than that, there's nothing
statistically meaningful to show, so we say so instead of drawing a line
through one or two dots.

Deliberately does NOT include a "power draw vs hashrate" series: power
draw is a single user-entered constant (see economics.py), not a
per-run measurement, so plotting it against hashrate would imply a
measured relationship that doesn't exist.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import db

MIN_POINTS = 2


@dataclass
class AnalyticsSeries:
    available: bool
    reason: str | None
    points: list[dict]


def threads_vs_hashrate() -> AnalyticsSeries:
    runs = db.list_benchmark_runs(limit=100_000)
    points = [
        {"x": r["threads"], "y": r["avg_hs"], "label": f"run #{r['id']}"}
        for r in runs if r.get("avg_hs") is not None
    ]
    if len(points) < MIN_POINTS:
        return AnalyticsSeries(False, f"Need at least {MIN_POINTS} benchmark runs — have {len(points)}.", [])
    return AnalyticsSeries(True, None, points)


def threads_vs_efficiency() -> AnalyticsSeries:
    runs = db.list_benchmark_runs(limit=100_000)
    points = [
        {"x": r["threads"], "y": r["hs_per_thread"], "label": f"run #{r['id']}"}
        for r in runs if r.get("hs_per_thread") is not None
    ]
    if len(points) < MIN_POINTS:
        return AnalyticsSeries(False, f"Need at least {MIN_POINTS} benchmark runs — have {len(points)}.", [])
    return AnalyticsSeries(True, None, points)


def session_duration_vs_hashrate() -> AnalyticsSeries:
    sessions = db.list_finished_mining_sessions()
    points = [
        {"x": s["duration_s"], "y": s["avg_hs"], "label": f"session #{s['id']}"}
        for s in sessions if s.get("avg_hs") is not None and s.get("duration_s") is not None
    ]
    if len(points) < MIN_POINTS:
        return AnalyticsSeries(
            False, f"Need at least {MIN_POINTS} completed mining sessions — have {len(points)}.", []
        )
    return AnalyticsSeries(True, None, points)


def thermal_state_vs_hashrate() -> AnalyticsSeries:
    runs = db.list_benchmark_runs(limit=100_000)
    by_state: dict[str, list[float]] = {}
    for r in runs:
        if r.get("avg_hs") is None:
            continue
        by_state.setdefault(r["final_thermal_state"], []).append(r["avg_hs"])

    if len(by_state) < MIN_POINTS:
        total = sum(len(v) for v in by_state.values())
        return AnalyticsSeries(
            False, f"Need runs across at least {MIN_POINTS} different thermal states — have {len(by_state)} ({total} runs total).", []
        )
    points = [
        {"x": state, "y": round(sum(vals) / len(vals), 1), "label": f"{len(vals)} runs"}
        for state, vals in by_state.items()
    ]
    return AnalyticsSeries(True, None, points)


def get_analytics() -> dict:
    return {
        "threads_vs_hashrate": threads_vs_hashrate().__dict__,
        "threads_vs_efficiency": threads_vs_efficiency().__dict__,
        "session_duration_vs_hashrate": session_duration_vs_hashrate().__dict__,
        "thermal_state_vs_hashrate": thermal_state_vs_hashrate().__dict__,
    }
