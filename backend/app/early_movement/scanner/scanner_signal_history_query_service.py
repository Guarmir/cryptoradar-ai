
from app.early_movement.scanner.scanner_signal_history_serializer import (
    EarlyMovementScannerSignalHistorySerializer,
)
from app.early_movement.scanner.scanner_signal_history_store import (
    EarlyMovementScannerSignalHistoryStore,
)


class EarlyMovementScannerSignalHistoryQueryService:
    def __init__(
        self,
        *,
        store: EarlyMovementScannerSignalHistoryStore,
    ) -> None:
        self._store = store
        self._serializer = (
            EarlyMovementScannerSignalHistorySerializer()
        )

    def load_recent(
        self,
        *,
        limit: int = 20,
    ) -> dict:
        if not 1 <= limit <= 100:
            raise ValueError(
                "O limite deve estar entre 1 e 100."
            )

        records = self._store.load_recent(
            limit=limit,
        )

        signals = [
            self._serializer.serialize(record)
            for record in records
        ]

        return {
            "status": "ok",
            "signal_count": len(signals),
            "signals": signals,
        }
