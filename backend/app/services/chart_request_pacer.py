import time
from collections.abc import Callable


Clock = Callable[[], float]


class ChartRequestPacer:
    DEFAULT_MIN_INTERVAL_SECONDS = 2.0

    def __init__(
        self,
        *,
        min_interval_seconds: float = (
            DEFAULT_MIN_INTERVAL_SECONDS
        ),
        clock: Clock | None = None,
    ) -> None:
        if min_interval_seconds <= 0:
            raise ValueError(
                "O intervalo mínimo deve ser "
                "maior que zero."
            )

        self._min_interval_seconds = (
            min_interval_seconds
        )
        self._clock = clock or time.monotonic
        self._last_request_at: float | None = None

    def can_request(self) -> bool:
        if self._last_request_at is None:
            return True

        elapsed = (
            self._clock()
            - self._last_request_at
        )

        return (
            elapsed
            >= self._min_interval_seconds
        )

    def record_request(self) -> None:
        self._last_request_at = self._clock()

    def reset(self) -> None:
        self._last_request_at = None