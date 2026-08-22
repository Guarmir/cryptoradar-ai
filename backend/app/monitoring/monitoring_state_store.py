from abc import ABC, abstractmethod
from typing import Optional

from app.monitoring.monitoring_state import MonitoringState


class MonitoringStateStore(ABC):
    @abstractmethod
    def load_state(
        self,
        symbol: str,
    ) -> Optional[MonitoringState]:
        raise NotImplementedError

    @abstractmethod
    def load_all(
        self,
    ) -> tuple[MonitoringState, ...]:
        raise NotImplementedError

    @abstractmethod
    def save_state(
        self,
        state: MonitoringState,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_state(
        self,
        symbol: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def clear(
        self,
    ) -> None:
        raise NotImplementedError