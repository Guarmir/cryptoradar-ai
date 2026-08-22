from dataclasses import dataclass
from typing import Optional

from app.monitoring.monitoring_observation import MonitoringObservation
from app.monitoring.monitoring_target import MonitoringTarget


@dataclass(frozen=True)
class MonitoringState:
    target: MonitoringTarget
    previous_observation: Optional[MonitoringObservation] = None
    current_observation: Optional[MonitoringObservation] = None
    observation_count: int = 0

    def __post_init__(self):
        if self.observation_count < 0:
            raise ValueError(
                "A quantidade de observações não pode ser negativa."
            )

        for observation in (
            self.previous_observation,
            self.current_observation,
        ):
            if observation is None:
                continue

            if observation.symbol != self.target.symbol:
                raise ValueError(
                    "A observação deve pertencer ao mesmo ativo monitorado."
                )

    @property
    def has_observation(self) -> bool:
        return self.current_observation is not None

    @property
    def has_previous_observation(self) -> bool:
        return self.previous_observation is not None

    @property
    def current_price(self) -> Optional[float]:
        if self.current_observation is None:
            return None

        return self.current_observation.price

    @property
    def previous_price(self) -> Optional[float]:
        if self.previous_observation is None:
            return None

        return self.previous_observation.price

    @property
    def price_change_since_previous_percent(
        self,
    ) -> Optional[float]:
        previous_price = self.previous_price
        current_price = self.current_price

        if (
            previous_price is None
            or current_price is None
            or previous_price <= 0
        ):
            return None

        return (
            (current_price - previous_price)
            / previous_price
            * 100
        )

    def observe(
        self,
        observation: MonitoringObservation,
    ) -> "MonitoringState":
        if observation.symbol != self.target.symbol:
            raise ValueError(
                "A nova observação deve pertencer ao mesmo ativo monitorado."
            )

        return MonitoringState(
            target=self.target,
            previous_observation=self.current_observation,
            current_observation=observation,
            observation_count=self.observation_count + 1,
        )