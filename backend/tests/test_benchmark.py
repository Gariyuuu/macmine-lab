"""Unit tests for benchmark result aggregation — pure math, no xmrig involved.

Per project rule: automated tests must not perform live/monetary mining.
These test the aggregation logic in isolation; the live end-to-end proof
(genuine RandomX hashing -> real STOP -> saved JSON) was run manually and is
documented in CHANGELOG.md / README.md rather than baked into the default
test suite.
"""

from macmine_lab.benchmark import HashrateSample, aggregate_stats


def test_aggregate_stats_basic():
    samples = [
        HashrateSample(t_offset_s=10.0, hashrate_10s=4000.0, hashrate_60s=None),
        HashrateSample(t_offset_s=11.0, hashrate_10s=4500.0, hashrate_60s=None),
        HashrateSample(t_offset_s=12.0, hashrate_10s=5000.0, hashrate_60s=None),
    ]
    avg, peak, low, per_thread = aggregate_stats(samples, threads=12)
    assert avg == 4500.0
    assert peak == 5000.0
    assert low == 4000.0
    assert per_thread == round(4500.0 / 12, 1)


def test_aggregate_stats_ignores_none_samples():
    samples = [
        HashrateSample(t_offset_s=10.0, hashrate_10s=None, hashrate_60s=None),
        HashrateSample(t_offset_s=11.0, hashrate_10s=3000.0, hashrate_60s=None),
    ]
    avg, peak, low, per_thread = aggregate_stats(samples, threads=4)
    assert avg == 3000.0
    assert peak == 3000.0
    assert low == 3000.0


def test_aggregate_stats_no_samples_returns_none_never_zero():
    # This is the "never fake a success" rule: no data means None
    # (renders as "Unavailable"), not a fabricated 0.
    avg, peak, low, per_thread = aggregate_stats([], threads=8)
    assert avg is None
    assert peak is None
    assert low is None
    assert per_thread is None


def test_aggregate_stats_zero_threads_does_not_divide_by_zero():
    samples = [HashrateSample(t_offset_s=1.0, hashrate_10s=100.0, hashrate_60s=None)]
    avg, peak, low, per_thread = aggregate_stats(samples, threads=0)
    assert avg == 100.0
    assert per_thread is None
