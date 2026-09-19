from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from app.monitoring.monitoring_target import MonitoringTarget


MarketEventType = Literal[
    "price_move_up",
    "price_move_down",
]


@dataclass(frozen=True)
class MarketEvent:
    target: MonitoringTarget
    event_type: MarketEventType
    previous_price: float
    current_price: float
    price_change_percent: float
    observed_at: datetime

    def __post_init__(self):
        if self.event_type not in (
            "price_move_up",
            "price_move_down",
        ):
            raise ValueError(
                "O tipo de evento de mercado nao e valido."
            )

        if self.previous_price <= 0:
            raise ValueError(
                "O preco anterior deve ser maior que zero."
            )

        if self.current_price <= 0:
            raise ValueError(
                "O preco atual deve ser maior que zero."
            )

        if (
            self.event_type == "price_move_up"
            and self.price_change_percent <= 0
        ):
            raise ValueError(
                "Um evento de alta exige variacao positiva."
            )

        if (
            self.event_type == "price_move_down"
            and self.price_change_percent >= 0
        ):
            raise ValueError(
                "Um evento de queda exige variacao negativa."
            )

        observed_at = self.observed_at

        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(
                tzinfo=timezone.utc,
            )

            object.__setattr__(
                self,
                "observed_at",
                observed_at,
            )

    @property
    def symbol(self) -> str:
        return self.target.symbol

    @property
    def is_upward(self) -> bool:
        return self.event_type == "price_move_up"

    @property
    def is_downward(self) -> bool:
        return self.event_type == "price_move_down"