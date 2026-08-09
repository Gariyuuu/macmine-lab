"""Tests for thread-count recommendation and Journal labeling logic —
pure functions over plain dicts, no xmrig involved."""

from macmine_lab import calibration


def _run(id, threads, avg_hs, hs_per_thread=None, thermal="NORMAL"):
    return {
        "id": id, "threads": threads, "avg_hs": avg_hs,
        "hs_per_thread": hs_per_thread if hs_per_thread is not None else (avg_hs / threads if avg_hs else None),
        "final_thermal_state": thermal,
    }


def test_recommend_configs_picks_best_in_each_range():
    runs = [
        _run(1, 2, 900.0),   # 2/12 = 0.167 -> below eco range
        _run(2, 4, 2200.0),  # 4/12 = 0.333 -> eco range (0.20-0.40)
        _run(3, 6, 3000.0),  # 6/12 = 0.5   -> balanced range (0.40-0.65)
        _run(4, 12, 4200.0), # performance
    ]
    recs = calibration.recommend_configs(runs, total_cores=12)

    assert recs["eco"].tested is True
    assert recs["eco"].threads == 4
    assert recs["balanced"].tested is True
    assert recs["balanced"].threads == 6
    assert recs["performance"].threads == 12
    assert recs["performance"].avg_hs == 4200.0


def test_recommend_configs_no_runs_returns_untested():
    recs = calibration.recommend_configs([], total_cores=12)
    for label in ("eco", "balanced", "performance"):
        assert recs[label].tested is False
        assert recs[label].threads is None


def test_recommend_configs_ignores_runs_missing_avg_hs():
    runs = [{"id": 1, "threads": 4, "avg_hs": None, "hs_per_thread": None, "final_thermal_state": "NORMAL"}]
    recs = calibration.recommend_configs(runs, total_cores=12)
    assert recs["performance"].tested is False


def test_recommend_configs_zero_total_cores_does_not_crash():
    runs = [_run(1, 4, 1000.0)]
    recs = calibration.recommend_configs(runs, total_cores=0)
    assert recs["eco"].tested is False
    assert recs["balanced"].tested is False


def test_label_result_best_overall():
    runs = [_run(1, 4, 1000.0), _run(2, 8, 2000.0)]
    assert calibration.label_result(runs[1], runs) == "Best raw performance"


def test_label_result_best_efficiency():
    # run 1: 500 H/s/thread (2 threads, 1000 H/s) — most efficient
    # run 2: 250 H/s/thread (8 threads, 2000 H/s) — best raw but least efficient
    runs = [_run(1, 2, 1000.0), _run(2, 8, 2000.0)]
    assert calibration.label_result(runs[0], runs) == "Most efficient (H/s per thread)"


def test_label_result_neither_best_falls_back_to_thermal_or_recorded():
    runs = [_run(1, 2, 500.0), _run(2, 4, 1000.0), _run(3, 8, 2000.0)]
    # run 2 (middle) is neither best overall nor most efficient
    label = calibration.label_result(runs[1], runs)
    assert label in ("Ran cool", "Recorded")


def test_label_result_single_run_is_just_recorded():
    runs = [_run(1, 4, 1000.0)]
    assert calibration.label_result(runs[0], runs) == "Recorded"


def test_label_result_missing_avg_hs_is_recorded():
    run = {"id": 1, "threads": 4, "avg_hs": None, "hs_per_thread": None, "final_thermal_state": "NORMAL"}
    runs = [run, _run(2, 8, 2000.0)]
    assert calibration.label_result(run, runs) == "Recorded"
