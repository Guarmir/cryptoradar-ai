from dataclasses import dataclass
from typing import Optional

from app.monitoring.monitoring_observation import MonitoringObservation
from app.monitoring.monitoring_state import MonitoringState
from app.monitoring.monitoring_target import MonitoringTarget


@dataclass(frozen=True)
class MonitoringCycleResult:
    target: MonitoringTarget
    previous_state: MonitoringState
    current_state: MonitoringState
    observation: MonitoringObservation

    def __post_init__(self):
        if self.previous_state.target.symbol != self.target.symbol:
            raise ValueError(
                "O estado anterior deve pertencer ao mesmo alvo monitorado."
            )

        if self.current_state.target.symbol != self.target.symbol:
            raise ValueError(
                "O estado atual deve pertencer ao mesmo alvo monitorado."
            )

        if self.observation.symbol != self.target.symbol:
            raise ValueError(
                "A observação deve pertencer ao mesmo alvo monitorado."
            )

    @property
    def is_first_observation(self) -> bool:
        return not self.previous_state.has_observation

    @property
    def observation_count(self) -> int:
        return self.current_state.observation_count

    @property
    def current_price(self) -> float:
        return self.observation.price

    @property
    def previous_price(self) -> Optional[float]:
        return self.current_state.previous_price

    @property
    def price_change_percent(self) -> Optional[float]:
        return self.current_state.price_change_since_previous_percent