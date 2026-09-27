import math
from statistics import fmean
from typing import Any, Mapping, Optional

from app.early_movement.early_movement_metrics import EarlyMovementMetrics


class EarlyMovementMetricExtractor:
    PRICE_ACCELERATION_SEGMENT = 3

    VOLUME_RECENT_WINDOW = 3
    VOLUME_BASELINE_WINDOW = 6

    VOLATILITY_RECENT_WINDOW = 3
    VOLATILITY_BASELINE_WINDOW = 6

    PERSISTENCE_WINDOW = 5

    def extract(
        self,
        chart_data: Mapping[str, Any],
    ) -> EarlyMovementMetrics:
        prices = self._extract_values(
            chart_data.get("prices"),
            allow_zero=False,
        )

        volumes = self._extract_values(
            chart_data.get("total_volumes"),
            allow_zero=True,
        )

        return EarlyMovementMetrics(
            price_acceleration=self._price_acceleration(
                prices,
            ),
            abnormal_volume_ratio=self._abnormal_volume_ratio(
                volumes,
            ),
            volatility_expansion=self._volatility_expansion(
                prices,
            ),
            persistence_score=self._persistence_score(
                prices,
            ),
            price_sample_count=len(prices),
            volume_sample_count=len(volumes),
        )

    def _price_acceleration(
        self,
        prices: list[float],
    ) -> Optional[float]:
        segment = self.PRICE_ACCELERATION_SEGMENT
        required = (segment * 2) + 1

        if len(prices) < required:
            return None

        previous_start = prices[-required]
        middle = prices[-(segment + 1)]
        current = prices[-1]

        previous_return = self._percentage_change(
            previous_start,
            middle,
        )

        recent_return = self._percentage_change(
            middle,
            current,
        )

        if previous_return is None or recent_return is None:
            return None

        return recent_return - previous_return

    def _abnormal_volume_ratio(
        self,
        volumes: list[float],
    ) -> Optional[float]:
        required = (
            self.VOLUME_BASELINE_WINDOW
            + self.VOLUME_RECENT_WINDOW
        )

        if len(volumes) < required:
            return None

        baseline_start = -required
        baseline_end = -self.VOLUME_RECENT_WINDOW

        baseline = volumes[
            baseline_start:baseline_end
        ]

        recent = volumes[
            -self.VOLUME_RECENT_WINDOW:
        ]

        baseline_average = fmean(baseline)

        if baseline_average <= 0:
            return None

        recent_average = fmean(recent)

        return recent_average / baseline_average

    def _volatility_expansion(
        self,
        prices: list[float],
    ) -> Optional[float]:
        required_returns = (
            self.VOLATILITY_BASELINE_WINDOW
            + self.VOLATILITY_RECENT_WINDOW
        )

        required_prices = required_returns + 1

        if len(prices) < required_prices:
            return None

        selected_prices = prices[-required_prices:]

        returns = self._percentage_returns(
            selected_prices,
        )

        if len(returns) != required_returns:
            return None

        baseline = returns[
            :self.VOLATILITY_BASELINE_WINDOW
        ]

        recent = returns[
            self.VOLATILITY_BASELINE_WINDOW:
        ]

        baseline_average = fmean(
            abs(value)
            for value in baseline
        )

        if baseline_average <= 0:
            return None

        recent_average = fmean(
            abs(value)
            for value in recent
        )

        return recent_average / baseline_average

    def _persistence_score(
        self,
        prices: list[float],
    ) -> Optional[float]:
        required_prices = self.PERSISTENCE_WINDOW + 1

        if len(prices) < required_prices:
            return None

        selected_prices = prices[-required_prices:]

        returns = self._percentage_returns(
            selected_prices,
        )

        if len(returns) != self.PERSISTENCE_WINDOW:
            return None

        absolute_movement = sum(
            abs(value)
            for value in returns
        )

        if absolute_movement <= 0:
            return 0.0

        net_movement = sum(returns)

        if net_movement == 0:
            return 0.0

        direction = 1 if net_movement > 0 else -1

        aligned_count = sum(
            1
            for value in returns
            if (
                value > 0
                and direction > 0
            )
            or (
                value < 0
                and direction < 0
            )
        )

        directional_consistency = (
            aligned_count / len(returns)
        )

        efficiency = (
            abs(net_movement)
            / absolute_movement
        )

        score = (
            directional_consistency
            * efficiency
            * 100.0
        )

        return max(
            0.0,
            min(100.0, score),
        )

    @staticmethod
    def _percentage_returns(
        prices: list[float],
    ) -> list[float]:
        returns: list[float] = []

        for index in range(
            1,
            len(prices),
        ):
            change = (
                EarlyMovementMetricExtractor
                ._percentage_change(
                    prices[index - 1],
                    prices[index],
                )
            )

            if change is None:
                return []

            returns.append(change)

        return returns

    @staticmethod
    def _percentage_change(
        start: float,
        end: float,
    ) -> Optional[float]:
        if start <= 0:
            return None

        return (
            (end - start)
            / start
            * 100.0
        )

    @staticmethod
    def _extract_values(
        series: Any,
        *,
        allow_zero: bool,
    ) -> list[float]:
        if not isinstance(series, list):
            return []

        values: list[float] = []

        for item in series:
            if (
                not isinstance(item, (list, tuple))
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

            if allow_zero:
                if value < 0:
                    continue
            elif value <= 0:
                continue

            values.append(value)

        return values