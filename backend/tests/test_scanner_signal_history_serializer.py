
from datetime import datetime, timezone

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_signal_history_record import (
    EarlyMovementScannerSignalHistoryRecord,
)
from app.early_movement.scanner.scanner_signal_history_serializer import (
    EarlyMovementScannerSignalHistorySerializer,
)


def test_serialize_signal_history_record():
    state = next(iter(EarlyMovementState))

    record = EarlyMovementScannerSignalHistoryRecord(
        observed_at=datetime(
            2026, 10, 12, 12, 30, tzinfo=timezone.utc
        ),
        coin_id="bitcoin",
        symbol="btc",
        name="Bitcoin",
        current_price=65000.0,
        state=state,
        relevance_score=85.0,
        abnormal_volume_ratio=2.5,
        alertable=True,
    )

    result = (
        EarlyMovementScannerSignalHistorySerializer.serialize(
            record
        )
    )

    assert result["coin_id"] == "bitcoin"
    assert result["state"] == state.value
    assert result["relevance_score"] == 85.0
    assert result["abnormal_volume_ratio"] == 2.5
    assert result["alertable"] is True
    assert result["observed_at"] == (
        "2026-10-12T12:30:00+00:00"
    )
