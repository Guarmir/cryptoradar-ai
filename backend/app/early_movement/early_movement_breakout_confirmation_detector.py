import math
from typing import Any, Mapping

from app.early_movement.early_movement_breakout_confirmation import (
    EarlyMovementBreakoutConfirmation,
)


class EarlyMovementBreakoutConfirmationDetector:
    BASELINE_LOOKBACK = 6

    BREAK_BUFFER_PERCENT = 0.25

    RETEST_TOLERANCE_PERCENT = 0.40

    RETEST_WINDOW = 3

    def detect(
        self,
        chart_data: Mapping[str, Any],
    ) -> EarlyMovementBreakoutConfirmation:
        prices = self._extract_prices(
            chart_data.get("prices"),
        )

        minimum_samples = (
            self.BASELINE_LOOKBACK + 3
        )

        if len(prices) < minimum_samples:
            return EarlyMovementBreakoutConfirmation(
                sample_count=len(prices),
            )

        latest_breakout_index = (
            len(prices) - 2
        )

        for breakout_index in range(
            latest_breakout_index,
            self.BASELINE_LOOKBACK - 1,
            -1,
        ):
            baseline = prices[
                breakout_index
                - self.BASELINE_LOOKBACK:
                breakout_index
            ]

            breakout_price = prices[
                breakout_index
            ]

            resistance = max(baseline)
            support = min(baseline)

            upward_result = (
                self._evaluate_upward_breakout(
                    prices=prices,
                    breakout_index=breakout_index,
                    breakout_price=breakout_price,
                    resistance=resistance,
                )
            )

            if upward_result is not None:
                return upward_result

            downward_result = (
                self._evaluate_downward_breakout(
                    prices=prices,
                    breakout_index=breakout_index,
                    breakout_price=breakout_price,
                    support=support,
                )
            )

            if downward_result is not None:
                return downward_result

        return EarlyMovementBreakoutConfirmation(
            sample_count=len(prices),
        )

    def _evaluate_upward_breakout(
        self,
        *,
        prices: list[float],
        breakout_index: int,
        breakout_price: float,
        resistance: float,
    ) -> (
        EarlyMovementBreakoutConfirmation
        | None
    ):
        threshold = resistance * (
            1.0
            + (
                self.BREAK_BUFFER_PERCENT
                / 100.0
            )
        )

        if breakout_price <= threshold:
            return None

        retest_price = self._find_retest_price(
            prices=prices,
            breakout_index=breakout_index,
            level=resistance,
        )

        if retest_price is None:
            return None

        current_price = prices[-1]

        holding_level = current_price > threshold

        if not holding_level:
            return None

        return EarlyMovementBreakoutConfirmation(
            retest_confirmed=True,
            breakout_direction="up",
            breakout_level=resistance,
            breakout_price=breakout_price,
            retest_price=retest_price,
            holding_breakout_level=True,
            sample_count=len(prices),
        )

    def _evaluate_downward_breakout(
        self,
        *,
        prices: list[float],
        breakout_index: int,
        breakout_price: float,
        support: float,
    ) -> (
        EarlyMovementBreakoutConfirmation
        | None
    ):
        threshold = support * (
            1.0
            - (
                self.BREAK_BUFFER_PERCENT
                / 100.0
            )
        )

        if breakout_price >= threshold:
            return None

        retest_price = self._find_retest_price(
            prices=prices,
            breakout_index=breakout_index,
            level=support,
        )

        if retest_price is None:
            return None

        current_price = prices[-1]

        holding_level = current_price < threshold

        if not holding_level:
            return None

        return EarlyMovementBreakoutConfirmation(
            retest_confirmed=True,
            breakout_direction="down",
            breakout_level=support,
            breakout_price=breakout_price,
            retest_price=retest_price,
            holding_breakout_level=True,
            sample_count=len(prices),
        )

    def _find_retest_price(
        self,
        *,
        prices: list[float],
        breakout_index: int,
        level: float,
    ) -> float | None:
        start = breakout_index + 1

        end = min(
            len(prices),
            start + self.RETEST_WINDOW,
        )

        candidates = prices[start:end]

        if not candidates:
            return None

        tolerance = (
            self.RETEST_TOLERANCE_PERCENT
            / 100.0
        )

        lower_bound = level * (
            1.0 - tolerance
        )

        upper_bound = level * (
            1.0 + tolerance
        )

        for price in candidates:
            if (
                lower_bound
                <= price
                <= upper_bound
            ):
                return price

        return None

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