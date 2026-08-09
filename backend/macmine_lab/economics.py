"""Mining earnings estimation — pure math over real network/price data plus
a hashrate and user-supplied cost inputs. Every output here is explicitly
an ESTIMATE (see README's "real vs estimated money" section): it's
calculated from hashrate/network/price, not observed from a pool or wallet.

Power draw is a user-entered estimate, not a measurement — macOS doesn't
expose real-time power draw without `sudo powermetrics`, and this project
avoids sudo. We say so wherever the number is shown.
"""

from __future__ import annotations

from dataclasses import dataclass

from .network import NetworkSnapshot
from .price import PriceSnapshot

SECONDS_PER_DAY = 86400


@dataclass
class EarningsEstimate:
    my_hashrate_hs: float
    network_hash_rate: float
    my_share_of_network: float
    xmr_per_hour: float
    xmr_per_day: float
    usd_per_hour: float
    usd_per_day: float
    power_draw_watts: float | None
    electricity_rate_usd_per_kwh: float | None
    electricity_cost_per_day_usd: float | None
    net_usd_per_day: float | None
    price_usd: float
    price_source: str
    price_fetched_at: str
    network_source: str
    network_fetched_at: str
    network_height: int


def estimate_earnings(
    my_hashrate_hs: float,
    network: NetworkSnapshot,
    price: PriceSnapshot,
    power_draw_watts: float | None = None,
    electricity_rate_usd_per_kwh: float | None = None,
) -> EarningsEstimate:
    my_share = my_hashrate_hs / network.network_hash_rate if network.network_hash_rate else 0.0
    blocks_per_day = SECONDS_PER_DAY / network.block_time_s
    xmr_per_day = my_share * blocks_per_day * network.block_reward_xmr
    xmr_per_hour = xmr_per_day / 24

    usd_per_day = xmr_per_day * price.price_usd
    usd_per_hour = xmr_per_hour * price.price_usd

    electricity_cost_per_day = None
    net_usd_per_day = None
    if power_draw_watts is not None and electricity_rate_usd_per_kwh is not None:
        electricity_cost_per_day = (power_draw_watts / 1000) * 24 * electricity_rate_usd_per_kwh
        net_usd_per_day = usd_per_day - electricity_cost_per_day

    return EarningsEstimate(
        my_hashrate_hs=my_hashrate_hs,
        network_hash_rate=network.network_hash_rate,
        my_share_of_network=my_share,
        xmr_per_hour=xmr_per_hour,
        xmr_per_day=xmr_per_day,
        usd_per_hour=usd_per_hour,
        usd_per_day=usd_per_day,
        power_draw_watts=power_draw_watts,
        electricity_rate_usd_per_kwh=electricity_rate_usd_per_kwh,
        electricity_cost_per_day_usd=electricity_cost_per_day,
        net_usd_per_day=net_usd_per_day,
        price_usd=price.price_usd,
        price_source=price.source,
        price_fetched_at=price.fetched_at,
        network_source=network.source,
        network_fetched_at=network.fetched_at,
        network_height=network.height,
    )
