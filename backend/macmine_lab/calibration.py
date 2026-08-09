"""Thread-count recommendation logic — shared by the CLI's `calibrate`
command and the Journal page's "recommended configs" section.

Operates on plain dicts with "threads"/"avg_hs"/etc. keys so the same code
works over BenchmarkResult objects (CLI, via dataclasses.asdict) and
benchmark_runs rows from SQLite (API/Journal) — one source of truth.
Recommendations are only ever computed from runs that were actually
measured, never assumed or interpolated.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Recommendation:
    threads: int | None
    avg_hs: float | None
    tested: bool


def best_in_thread_range(
    runs: list[dict], total_cores: int, lo_frac: float, hi_frac: float
) -> Recommendation:
    if not total_cores:
        return Recommendation(threads=None, avg_hs=None, tested=False)
    candidates = [
        r for r in runs
        if r.get("avg_hs") is not None and lo_frac <= r["threads"] / total_cores <= hi_frac
    ]
    if not candidates:
        return Recommendation(threads=None, avg_hs=None, tested=False)
    best = max(candidates, key=lambda r: r["avg_hs"])
    return Recommendation(threads=best["threads"], avg_hs=best["avg_hs"], tested=True)


def recommend_configs(runs: list[dict], total_cores: int) -> dict[str, Recommendation]:
    tested = [r for r in runs if r.get("avg_hs") is not None]
    if not tested:
        empty = Recommendation(None, None, False)
        return {"eco": empty, "balanced": empty, "performance": empty}

    eco = best_in_thread_range(runs, total_cores, 0.20, 0.40)
    balanced = best_in_thread_range(runs, total_cores, 0.40, 0.65)
    best_overall = max(tested, key=lambda r: r["avg_hs"])
    performance = Recommendation(threads=best_overall["threads"], avg_hs=best_overall["avg_hs"], tested=True)

    return {"eco": eco, "balanced": balanced, "performance": performance}


def label_result(run: dict, all_runs: list[dict]) -> str:
    """A short, honest, comparison-based label for one run — e.g. "Best raw
    performance" — used in the Journal. Needs at least 2 measured runs to
    say anything comparative; otherwise just "Recorded"."""
    tested = [r for r in all_runs if r.get("avg_hs") is not None]
    if run.get("avg_hs") is None or len(tested) < 2:
        return "Recorded"

    best_overall = max(tested, key=lambda r: r["avg_hs"])
    efficiency_candidates = [r for r in tested if r.get("hs_per_thread") is not None]
    best_efficiency = max(efficiency_candidates, key=lambda r: r["hs_per_thread"]) if efficiency_candidates else None

    if run["id"] == best_overall["id"]:
        return "Best raw performance"
    if best_efficiency and run["id"] == best_efficiency["id"]:
        return "Most efficient (H/s per thread)"
    if run.get("final_thermal_state") == "NORMAL":
        return "Ran cool"
    return "Recorded"
