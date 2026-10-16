
from datetime import datetime, timezone
from typing import Optional

from app.early_movement.scanner.scanner_notification_state_store import (
    EarlyMovementScannerNotificationState,
    EarlyMovementScannerNotificationStateStore,
)
from app.early_movement.scanner.scanner_ranked_result import (
    EarlyMovementScannerRankedResult,
)


class EarlyMovementScannerPushEvolutionGuard:
    def __init__(
        self,
        *,
        state_store: Optional[
            EarlyMovementScannerNotificationStateStore
        ] = None,
    ) -> None:
        self._state_store = state_store
        self._last_notified_state: dict[str, str] = {}

    def should_notify(
        self,
        result: EarlyMovementScannerRankedResult,
    ) -> bool:
        coin_id = result.coin_id
        current_state = result.state.value

        if self._state_store is not None:
            previous = self._state_store.load(coin_id)

            if previous is None:
                return True

            return previous.last_notified_state != current_state

        previous_state = self._last_notified_state.get(coin_id)

        if previous_state is None:
            return True

        return previous_state != current_state

    def mark_notified(
        self,
        result: EarlyMovementScannerRankedResult,
    ) -> None:
        coin_id = result.coin_id
        current_state = result.state.value

        if self._state_store is not None:
            self._state_store.save(
                EarlyMovementScannerNotificationState(
                    coin_id=coin_id,
                    last_notified_state=current_state,
                    last_notified_at=datetime.now(timezone.utc),
                )
            )
            return

        self._last_notified_state[coin_id] = current_state
