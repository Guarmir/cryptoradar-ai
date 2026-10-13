
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_signal_history_query_service import (
    EarlyMovementScannerSignalHistoryQueryService,
)
from app.early_movement.scanner.scanner_signal_history_record import (
    EarlyMovementScannerSignalHistoryRecord,
)


def test_load_recent_returns_serialized_signals():
    record = EarlyMovementScannerSignalHistoryRecord(
        observed_at=datetime(
            2026, 10, 12, 12, 30, tzinfo=timezone.utc
        ),
        coin_id="bitcoin",
        symbol="btc",
        name="Bitcoin",
        current_price=65000.0,
        state=next(iter(EarlyMovementState)),
        relevance_score=85.0,
        alertable=True,
    )

    store = Mock()
    store.load_recent.return_value = (record,)

    service = EarlyMovementScannerSignalHistoryQueryService(
        store=store,
    )

    result = service.load_recent(limit=20)

    store.load_recent.assert_called_once_with(limit=20)

    assert result["status"] == "ok"
    assert result["signal_count"] == 1
    assert result["signals"][0]["coin_id"] == "bitcoin"
    assert result["signals"][0]["alertable"] is True


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_load_recent_rejects_invalid_limits(limit):
    store = Mock()

    service = EarlyMovementScannerSignalHistoryQueryService(
        store=store,
    )

    with pytest.raises(ValueError):
        service.load_recent(limit=limit)

    store.load_recent.assert_not_called()
