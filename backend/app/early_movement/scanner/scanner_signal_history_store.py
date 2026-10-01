from abc import ABC, abstractmethod

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