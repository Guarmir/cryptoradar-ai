from typing import Optional

from app.monitoring.market_event import MarketEvent
from app.monitoring.monitoring_cycle_result import (
    MonitoringCycleResult,
)


class MarketEventEvaluator:
    def __init__(
        self,
        *,
        minimum_price_change_percent: float,
        maximum_observation_gap_seconds: Optional[
            float
        ] = 180.0,
    ):
        if minimum_price_change_percent <= 0:
            raise ValueError(
                "A variacao minima deve ser maior que zero."
            )

        if (
            maximum_observation_gap_seconds is not None
            and maximum_observation_gap_seconds <= 0
        ):
            raise ValueError(
                "O intervalo maximo entre observacoes "
                "deve ser maior que zero."
            )

        self._minimum_price_change_percent = (
            minimum_price_change_percent
        )

        self._maximum_observation_gap_seconds = (
            maximum_observation_gap_seconds
        )

    @property
    def minimum_price_change_percent(self) -> float:
        return self._minimum_price_change_percent

    @property
    def maximum_observation_gap_seconds(
        self,
    ) -> Optional[float]:
        return self._maximum_observation_gap_seconds

    def evaluate(
        self,
        result: MonitoringCycleResult,
    ) -> tuple[MarketEvent, ...]:
        if result.is_first_observation:
            return ()

        previous_observation = (
            result.previous_state.current_observation
        )

        current_observation = result.observation

        if previous_observation is None:
            return ()

        previous_observed_at = (
            previous_observation.observed_at
        )

        current_observed_at = (
            current_observation.observed_at
        )

        if (
            previous_observed_at is None
            or current_observed_at is None
        ):
            return ()

        observation_gap_seconds = (
            current_observed_at
            - previous_observed_at
        ).total_seconds()

        if observation_gap_seconds <= 0:
            return ()

        maximum_gap = (
            self._maximum_observation_gap_seconds
        )

        if (
            maximum_gap is not None
            and observation_gap_seconds > maximum_gap
        ):
            return ()

        previous_price = result.previous_price
        price_change_percent = (
            result.price_change_percent
        )

        if (
            previous_price is None
            or price_change_percent is None
        ):
            return ()

        if (
            abs(price_change_percent)
            < self._minimum_price_change_percent
        ):
            return ()

        if price_change_percent > 0:
            event_type = "price_move_up"
        else:
            event_type = "price_move_down"

        return (
            MarketEvent(
                target=result.target,
                event_type=event_type,
                previous_price=previous_price,
                current_price=result.current_price,
                price_change_percent=price_change_percent,
                observed_at=current_observed_at,
            ),
        )