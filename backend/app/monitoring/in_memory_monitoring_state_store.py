import threading
from typing import Optional

from app.monitoring.monitoring_state import MonitoringState
from app.monitoring.monitoring_state_store import (
    MonitoringStateStore,
)
from app.monitoring.monitoring_state_serializer import (
    monitoring_state_from_dict,
    monitoring_state_to_dict,
)


class InMemoryMonitoringStateStore(
    MonitoringStateStore
):
    def __init__(self):
        self._data: dict[
            str,
            dict,
        ] = {}

        self._lock = threading.Lock()

    def load_state(
        self,
        symbol: str,
    ) -> Optional[MonitoringState]:
        normalized = self._normalize_symbol(
            symbol,
        )

        if not normalized:
            return None

        with self._lock:
            raw_state = self._data.get(
                normalized,
            )

            if raw_state is None:
                return None

            snapshot = dict(
                raw_state,
            )

        return monitoring_state_from_dict(
            snapshot,
        )

    def load_all(
        self,
    ) -> tuple[MonitoringState, ...]:
        with self._lock:
            snapshots = [
                dict(
                    raw_state,
                )
                for raw_state
                in self._data.values()
            ]

        return tuple(
            monitoring_state_from_dict(
                snapshot,
            )
            for snapshot in snapshots
        )

    def save_state(
        self,
        state: MonitoringState,
    ) -> None:
        serialized = (
            monitoring_state_to_dict(
                state,
            )
        )

        with self._lock:
            self._data[
                state.target.symbol
            ] = serialized

    def delete_state(
        self,
        symbol: str,
    ) -> bool:
        normalized = self._normalize_symbol(
            symbol,
        )

        if not normalized:
            return False

        with self._lock:
            return (
                self._data.pop(
                    normalized,
                    None,
                )
                is not None
            )

    def clear(
        self,
    ) -> None:
        with self._lock:
            self._data.clear()

    @staticmethod
    def _normalize_symbol(
        value: str,
    ) -> str:
        return value.strip().upper()