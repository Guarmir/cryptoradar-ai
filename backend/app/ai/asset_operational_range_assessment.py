from dataclasses import dataclass
import math
from typing import Iterable, Optional


@dataclass(frozen=True)
class AssetOperationalRangeAssessment:
    current_price: float
    lower_limit: float
    upper_limit: float
    amplitude_percent: float
    position_percent: float
    distance_to_lower_percent: float
    distance_to_upper_percent: float
    observed_points_count: int
    is_operational_amplitude: bool


def calculate_asset_operational_range(
    *,
    current_price: float,
    prices: Iterable[float],
) -> Optional[AssetOperationalRangeAssessment]:
    if (
        not math.isfinite(current_price)
        or current_price <= 0
    ):
        return None

    valid_prices = tuple(
        float(price)
        for price in prices
        if _is_valid_price(price)
    )

    if len(valid_prices) < 2:
        return None

    lower_limit = min(valid_prices)
    upper_limit = max(valid_prices)

    if (
        lower_limit <= 0
        or upper_limit <= lower_limit
    ):
        return None

    amplitude_percent = (
        (upper_limit - lower_limit)
        / lower_limit
        * 100
    )

    position_percent = (
        (current_price - lower_limit)
        / (upper_limit - lower_limit)
        * 100
    )

    distance_to_lower_percent = (
        (current_price - lower_limit)
        / current_price
        * 100
    )

    distance_to_upper_percent = (
        (upper_limit - current_price)
        / current_price
        * 100
    )

    return AssetOperationalRangeAssessment(
        current_price=current_price,
        lower_limit=lower_limit,
        upper_limit=upper_limit,
        amplitude_percent=amplitude_percent,
        position_percent=position_percent,
        distance_to_lower_percent=(
            distance_to_lower_percent
        ),
        distance_to_upper_percent=(
            distance_to_upper_percent
        ),
        observed_points_count=len(
            valid_prices
        ),
        is_operational_amplitude=(
            4.0
            <= amplitude_percent
            <= 6.0
        ),
    )


def _is_valid_price(
    value,
) -> bool:
    try:
        price = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return False

    return (
        math.isfinite(price)
        and price > 0
    )