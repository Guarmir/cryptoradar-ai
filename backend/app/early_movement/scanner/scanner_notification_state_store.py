
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementScannerNotificationState:
    coin_id: str
    last_notified_state: str
    last_notified_at: datetime


class EarlyMovementScannerNotificationStateStore(ABC):
    @abstractmethod
    def load(
        self,
        coin_id: str,
    ) -> Optional[EarlyMovementScannerNotificationState]:
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        state: EarlyMovementScannerNotificationState,
    ) -> None:
        raise NotImplementedError
