from typing import Any, Mapping, Optional

from app.monitoring.monitoring_cycle_result import MonitoringCycleResult
from app.monitoring.monitoring_observation import MonitoringObservation
from app.monitoring.monitoring_observation_builder import (
    build_monitoring_observation,
)
from app.monitoring.monitoring_state import MonitoringState
from app.monitoring.monitoring_target import MonitoringTarget


class MonitoringEngine:
    def __init__(self):
        self._states: dict[str, MonitoringState] = {}

    @property
    def target_count(self) -> int:
        return len(self._states)

    @property
    def registered_symbols(self) -> tuple[str, ...]:
        return tuple(
            self._states.keys(),
        )

    def register_target(
        self,
        target: MonitoringTarget,
    ) -> MonitoringState:
        existing = self._states.get(
            target.symbol,
        )

        if existing is None:
            state = MonitoringState(
                target=target,
            )
        else:
            state = MonitoringState(
                target=target,
                previous_observation=existing.previous_observation,
                current_observation=existing.current_observation,
                observation_count=existing.observation_count,
            )

        self._states[target.symbol] = state

        return state

    def restore_state(
        self,
        state: MonitoringState,
    ) -> MonitoringState:
        self._states[
            state.target.symbol
        ] = state

        return state

    def contains(
        self,
        symbol: str,
    ) -> bool:
        return self.state_for(
            symbol,
        ) is not None

    def state_for(
        self,
        symbol: str,
    ) -> Optional[MonitoringState]:
        normalized = self._normalize_symbol(
            symbol,
        )

        if not normalized:
            return None

        return self._states.get(
            normalized,
        )

    def observe_market_data(
        self,
        symbol: str,
        market_data: Mapping[str, Any],
    ) -> MonitoringCycleResult:
        state = self._require_state(
            symbol,
        )

        observation = build_monitoring_observation(
            state.target,
            market_data,
        )

        return self.observe(
            observation,
        )

    def observe(
        self,
        observation: MonitoringObservation,
    ) -> MonitoringCycleResult:
        previous_state = self._require_state(
            observation.symbol,
        )

        current_state = previous_state.observe(
            observation,
        )

        self._states[
            observation.symbol
        ] = current_state

        return MonitoringCycleResult(
            target=current_state.target,
            previous_state=previous_state,
            current_state=current_state,
            observation=observation,
        )

    def remove_target(
        self,
        symbol: str,
    ) -> bool:
        normalized = self._normalize_symbol(
            symbol,
        )

        if not normalized:
            return False

        return (
            self._states.pop(
                normalized,
                None,
            )
            is not None
        )

    def clear(self) -> None:
        self._states.clear()

    def _require_state(
        self,
        symbol: str,
    ) -> MonitoringState:
        normalized = self._normalize_symbol(
            symbol,
        )

        state = self._states.get(
            normalized,
        )

        if state is None:
            raise KeyError(
                f"O ativo {normalized or symbol} "
                "não está registrado para monitoramento."
            )

        return state

    @staticmethod
    def _normalize_symbol(
        value: str,
    ) -> str:
        return value.strip().upper()