import time
from collections.abc import Callable


Clock = Callable[[], float]


class ChartRequestCooldown:
    DEFAULT_COOLDOWN_SECONDS = 60.0

    def __init__(
        self,
        *,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        clock: Clock | None = None,
    ) -> None:
        if cooldown_seconds <= 0:
            raise ValueError(
                "O cooldown deve ser maior que zero."
            )

        self._cooldown_seconds = cooldown_seconds
        self._clock = clock or time.monotonic
        self._blocked_until = 0.0

    def is_blocked(
        self,
    ) -> bool:
        return (
            self._clock()
            < self._blocked_until
        )

    def activate(
        self,
    ) -> None:
        self._blocked_until = (
            self._clock()
            + self._cooldown_seconds
        )

    def reset(
        self,
    ) -> None:
        self._blocked_until = 0.0