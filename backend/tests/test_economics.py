"""Pure-math tests for earnings estimation — no network involved."""

from macmine_lab.economics import estimate_earnings
from macmine_lab.network import NetworkSnapshot
from macmine_lab.price import PriceSnapshot


def _network(hash_rate=1_000_000.0, reward=0.6, block_time=120.0):
    return NetworkSnapshot(
        difficulty=1e11,
        network_hash_rate=hash_rate,
        block_reward_xmr=reward,
        block_time_s=block_time,
        height=3_000_000,
        source="test",
        fetched_at="2026-01-01T00:00:00+00:00",
    )


def _price(usd=100.0):
    return PriceSnapshot(price_usd=usd, source="test", fetched_at="2026-01-01T00:00:00+00:00")


def test_basic_estimate_matches_hand_calculation():
    # my_share = 1000 / 1_000_000 = 0.001
    # blocks_per_day = 86400 / 120 = 720
    # xmr_per_day = 0.001 * 720 * 0.6 = 0.432
    net = _network(hash_rate=1_000_000.0, reward=0.6, block_time=120.0)
    pr = _price(usd=100.0)
    est = estimate_earnings(1000.0, net, pr)

    assert est.my_share_of_network == 0.001
    assert round(est.xmr_per_day, 6) == 0.432
    assert round(est.xmr_per_hour, 6) == round(0.432 / 24, 6)
    assert round(est.usd_per_day, 4) == round(0.432 * 100, 4)


def test_zero_network_hashrate_does_not_divide_by_zero():
    net = _network(hash_rate=0.0)
    pr = _price()
    est = estimate_earnings(1000.0, net, pr)
    assert est.my_share_of_network == 0.0
    assert est.xmr_per_day == 0.0


def test_electricity_cost_and_net_only_computed_when_both_inputs_given():
    net = _network()
    pr = _price()
    est_without = estimate_earnings(1000.0, net, pr)
    assert est_without.electricity_cost_per_day_usd is None
    assert est_without.net_usd_per_day is None

    est_with = estimate_earnings(
        1000.0, net, pr, power_draw_watts=100.0, electricity_rate_usd_per_kwh=0.15
    )
    # 0.1 kW * 24h * $0.15/kWh = $0.36/day
    assert round(est_with.electricity_cost_per_day_usd, 4) == 0.36
    assert round(est_with.net_usd_per_day, 4) == round(est_with.usd_per_day - 0.36, 4)


def test_estimate_carries_through_source_and_freshness_metadata():
    net = _network()
    pr = _price()
    est = estimate_earnings(500.0, net, pr)
    assert est.price_source == "test"
    assert est.network_source == "test"
    assert est.network_height == 3_000_000
