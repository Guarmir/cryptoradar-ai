
from abc import ABC, abstractmethod
from typing import Optional

from app.early_movement.scanner.scanner_signal_history_record import (
    EarlyMovementScannerSignalHistoryRecord,
)


class EarlyMovementScannerSignalHistoryStore(
    ABC
):
    @abstractmethod
    def save(
        self,
        record: EarlyMovementScannerSignalHistoryRecord,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_recent(
        self,
        *,
        limit: int = 100,
    ) -> tuple[
        EarlyMovementScannerSignalHistoryRecord,
        ...,
    ]:
        raise NotImplementedError

    def load_latest_for_coin(
        self,
        *,
        coin_id: str,
    ) -> Optional[
        EarlyMovementScannerSignalHistoryRecord
    ]:
        raise NotImplementedError
