import math
from typing import Any, Mapping, Optional

from app.early_movement.early_movement_price_structure import (
    EarlyMovementPriceStructure,
)


class EarlyMovementPriceStructureDetector:
    LOOKBACK = 8

    BREAK_BUFFER_PERCENT = 0.25

    def detect(
        self,
        chart_data: Mapping[str, Any],
    ) -> EarlyMovementPriceStructure:
        prices = self._extract_prices(
            chart_data.get("prices"),
        )

        required_samples = self.LOOKBACK + 1

        if len(prices) < required_samples:
            return EarlyMovementPriceStructure(
                current_price=(
                    prices[-1]
                    if prices
                    else None
                ),
                sample_count=len(prices),
            )

        baseline = prices[
            -(self.LOOKBACK + 1):-1
        ]

        current_price = prices[-1]

        support_level = min(baseline)
        resistance_level = max(baseline)

        support_break_threshold = (
            support_level
            * (
                1.0
                - (
                    self.BREAK_BUFFER_PERCENT
                    / 100.0
                )
            )
        )

        resistance_break_threshold = (
            resistance_level
            * (
                1.0
                + (
                    self.BREAK_BUFFER_PERCENT
                    / 100.0
                )
            )
        )

        support_break = (
            current_price
            < support_break_threshold
        )

        resistance_break = (
            current_price
            > resistance_break_threshold
        )

        support_break_distance_percent = None
        resistance_break_distance_percent = None

        if support_break:
            support_break_distance_percent = (
                self._percentage_distance(
                    reference=support_level,
                    current=current_price,
                )
            )

        if resistance_break:
            resistance_break_distance_percent = (
                self._percentage_distance(
                    reference=resistance_level,
                    current=current_price,
                )
            )

        return EarlyMovementPriceStructure(
            current_price=current_price,
            support_level=support_level,
            resistance_level=resistance_level,
            support_break=support_break,
            resistance_break=resistance_break,
            support_break_distance_percent=(
                support_break_distance_percent
            ),
            resistance_break_distance_percent=(
                resistance_break_distance_percent
            ),
            sample_count=len(prices),
        )

    @staticmethod
    def _percentage_distance(
        *,
        reference: float,
        current: float,
    ) -> Optional[float]:
        if reference <= 0:
            return None

        return (
            (current - reference)
            / reference
            * 100.0
        )

    @staticmethod
    def _extract_prices(
        series: Any,
    ) -> list[float]:
        if not isinstance(series, list):
            return []

        prices: list[float] = []

        for item in series:
            if (
                not isinstance(
                    item,
                    (list, tuple),
                )
                or len(item) < 2
            ):
                continue

            raw_value = item[1]

            if isinstance(raw_value, bool):
                continue

            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue

            if not math.isfinite(value):
                continue

            if value <= 0:
                continue

            prices.append(value)

        return prices