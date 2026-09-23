from dataclasses import dataclass
import math
from typing import Iterable, Optional

from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
)


@dataclass(frozen=True)
class AssetOperationalRangeRecurrenceAssessment:
    lower_limit_touches: int
    upper_limit_touches: int
    observed_points_count: int
    total_limit_touches: int
    completed_oscillations: int
    has_both_limits_tested: bool
    has_minimum_recurrence: bool
    has_strong_recurrence: bool
    is_unbalanced: bool
    suggests_recurring_range: bool
    suggests_organized_oscillation: bool
    state: str


def calculate_asset_operational_range_recurrence(
    *,
    prices: Iterable[float],
    range_assessment: AssetOperationalRangeAssessment,
) -> Optional[
    AssetOperationalRangeRecurrenceAssessment
]:
    valid_prices = tuple(
        float(price)
        for price in prices
        if _is_valid_price(price)
    )

    if len(valid_prices) < 2:
        return None

    lower_limit = (
        range_assessment.lower_limit
    )

    upper_limit = (
        range_assessment.upper_limit
    )

    range_width = (
        upper_limit
        - lower_limit
    )

    if (
        not math.isfinite(range_width)
        or range_width <= 0
    ):
        return None

    touch_tolerance = (
        range_width * 0.20
    )

    lower_touch_limit = (
        lower_limit
        + touch_tolerance
    )

    upper_touch_limit = (
        upper_limit
        - touch_tolerance
    )

    lower_touches = 0
    upper_touches = 0

    last_touch_zone: Optional[str] = None

    for price in valid_prices:
        current_zone: Optional[str]

        if price <= lower_touch_limit:
            current_zone = "lower"

        elif price >= upper_touch_limit:
            current_zone = "upper"

        else:
            current_zone = None

        if current_zone is None:
            last_touch_zone = None
            continue

        if current_zone == last_touch_zone:
            continue

        if current_zone == "lower":
            lower_touches += 1

        elif current_zone == "upper":
            upper_touches += 1

        last_touch_zone = current_zone

    total_limit_touches = (
        lower_touches
        + upper_touches
    )

    completed_oscillations = min(
        lower_touches,
        upper_touches,
    )

    has_both_limits_tested = (
        lower_touches > 0
        and upper_touches > 0
    )

    has_minimum_recurrence = (
        lower_touches >= 2
        and upper_touches >= 2
    )

    has_strong_recurrence = (
        lower_touches >= 3
        and upper_touches >= 3
    )

    is_unbalanced = (
        abs(
            lower_touches
            - upper_touches
        )
        > 1
    )

    suggests_recurring_range = (
        has_minimum_recurrence
    )

    suggests_organized_oscillation = (
        has_strong_recurrence
        and not is_unbalanced
    )

    if suggests_organized_oscillation:
        state = "organized_oscillation"

    elif suggests_recurring_range:
        state = "recurring_range"

    else:
        state = "insufficient_recurrence"

    return (
        AssetOperationalRangeRecurrenceAssessment(
            lower_limit_touches=(
                lower_touches
            ),
            upper_limit_touches=(
                upper_touches
            ),
            observed_points_count=(
                len(valid_prices)
            ),
            total_limit_touches=(
                total_limit_touches
            ),
            completed_oscillations=(
                completed_oscillations
            ),
            has_both_limits_tested=(
                has_both_limits_tested
            ),
            has_minimum_recurrence=(
                has_minimum_recurrence
            ),
            has_strong_recurrence=(
                has_strong_recurrence
            ),
            is_unbalanced=(
                is_unbalanced
            ),
            suggests_recurring_range=(
                suggests_recurring_range
            ),
            suggests_organized_oscillation=(
                suggests_organized_oscillation
            ),
            state=state,
        )
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