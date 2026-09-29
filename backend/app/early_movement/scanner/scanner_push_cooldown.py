from datetime import (
    datetime,
    timezone,
)
from typing import Callable

from app.early_movement.scanner.scanner_ranked_result import (
    EarlyMovementScannerRankedResult,
)


class EarlyMovementScannerPushCooldown:
    def __init__(
        self,
        *,
        cooldown_seconds: float,
        clock: Callable[
            [],
            datetime,
        ] = lambda: datetime.now(
            timezone.utc,
        ),
    ) -> None:
        if cooldown_seconds <= 0:
            raise ValueError(
                "O cooldown deve ser maior que zero."
            )

        self._cooldown_seconds = float(
            cooldown_seconds
        )

        self._clock = clock

        self._last_delivered_at: dict[
            tuple[str, str],
            datetime,
        ] = {}

    @property
    def cooldown_seconds(
        self,
    ) -> float:
        return self._cooldown_seconds

    def can_deliver(
        self,
        result: EarlyMovementScannerRankedResult,
    ) -> bool:
        key = self._result_key(
            result
        )

        last_delivered_at = (
            self._last_delivered_at.get(
                key
            )
        )

        if last_delivered_at is None:
            return True

        now = self._clock()

        elapsed_seconds = (
            now - last_delivered_at
        ).total_seconds()

        return (
            elapsed_seconds
            >= self._cooldown_seconds
        )

    def mark_delivered(
        self,
        result: EarlyMovementScannerRankedResult,
    ) -> None:
        self._last_delivered_at[
            self._result_key(
                result
            )
        ] = self._clock()

    def clear(
        self,
    ) -> None:
        self._last_delivered_at.clear()

    @staticmethod
    def _result_key(
        result: EarlyMovementScannerRankedResult,
    ) -> tuple[str, str]:
        state = result.state

        state_value = (
            state.value
            if state is not None
            else "unknown"
        )

        return (
            result.coin_id,
            state_value,
        )