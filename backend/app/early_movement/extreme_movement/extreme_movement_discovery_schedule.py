import time
from collections.abc import Callable


class ExtremeMovementDiscoverySchedule:
    DEFAULT_INTERVAL_SECONDS = 900

    def __init__(
        self,
        *,
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if interval_seconds < 1:
            raise ValueError(
                "O intervalo deve ser maior que zero."
            )

        self._interval_seconds = interval_seconds
        self._clock = clock
        self._next_run_at: float | None = None

    def should_run(self) -> bool:
        now = self._clock()

        if (
            self._next_run_at is not None
            and now < self._next_run_at
        ):
            return False

        self._next_run_at = now + self._interval_seconds
        return True

    @property
    def interval_seconds(self) -> int:
        return self._interval_seconds
