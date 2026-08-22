from typing import Optional

from app.monitoring.monitoring_cycle_result import (
    MonitoringCycleResult,
)
from app.monitoring.monitoring_engine import MonitoringEngine
from app.monitoring.monitoring_market_data_provider import (
    MonitoringMarketDataProvider,
)
from app.monitoring.monitoring_state import MonitoringState
from app.monitoring.monitoring_state_store import MonitoringStateStore
from app.monitoring.monitoring_target import MonitoringTarget


class MonitoringService:
    def __init__(
        self,
        *,
        engine: MonitoringEngine,
        market_data_provider: MonitoringMarketDataProvider,
        state_store: Optional[MonitoringStateStore] = None,
    ):
        self._engine = engine
        self._market_data_provider = market_data_provider
        self._state_store = state_store

    @property
    def target_count(self) -> int:
        return self._engine.target_count

    @property
    def registered_symbols(self) -> tuple[str, ...]:
        return self._engine.registered_symbols

    def restore_from_store(
        self,
    ) -> tuple[MonitoringState, ...]:
        store = self._state_store

        if store is None:
            return ()

        states = store.load_all()

        for state in states:
            self._engine.restore_state(
                state,
            )

        return states

    def register_target(
        self,
        target: MonitoringTarget,
    ) -> MonitoringState:
        state = self._engine.register_target(
            target,
        )

        self._persist_state(
            state,
        )

        return state

    def state_for(
        self,
        symbol: str,
    ) -> Optional[MonitoringState]:
        return self._engine.state_for(
            symbol,
        )

    def run_cycle(
        self,
        symbol: str,
    ) -> MonitoringCycleResult:
        state = self._engine.state_for(
            symbol,
        )

        if state is None:
            normalized = symbol.strip().upper()

            raise KeyError(
                f"O ativo {normalized or symbol} "
                "não está registrado para monitoramento."
            )

        market_data = (
            self._market_data_provider.fetch_market_data(
                state.target,
            )
        )

        result = self._engine.observe_market_data(
            state.target.symbol,
            market_data,
        )

        self._persist_state(
            result.current_state,
        )

        return result

    def remove_target(
        self,
        symbol: str,
    ) -> bool:
        removed = self._engine.remove_target(
            symbol,
        )

        if not removed:
            return False

        store = self._state_store

        if store is not None:
            store.delete_state(
                symbol,
            )

        return True

    def clear(self) -> None:
        self._engine.clear()

        store = self._state_store

        if store is not None:
            store.clear()

    def _persist_state(
        self,
        state: MonitoringState,
    ) -> None:
        store = self._state_store

        if store is None:
            return

        store.save_state(
            state,
        )