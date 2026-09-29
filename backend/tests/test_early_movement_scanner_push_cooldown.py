from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_push_cooldown import (
    EarlyMovementScannerPushCooldown,
)


@dataclass(frozen=True)
class FakeRankedResult:
    coin_id: str
    state: EarlyMovementState


class FakeClock:
    def __init__(
        self,
        now: datetime,
    ) -> None:
        self.now = now

    def __call__(
        self,
    ) -> datetime:
        return self.now

    def advance(
        self,
        *,
        seconds: float,
    ) -> None:
        self.now = (
            self.now
            + timedelta(
                seconds=seconds,
            )
        )


def make_signal() -> FakeRankedResult:
    return FakeRankedResult(
        coin_id="bitcoin",
        state=EarlyMovementState.EARLY_MOVEMENT,
    )


def test_cooldown_allows_first_delivery() -> None:
    clock = FakeClock(
        datetime(
            2026,
            9,
            29,
            tzinfo=timezone.utc,
        )
    )

    cooldown = (
        EarlyMovementScannerPushCooldown(
            cooldown_seconds=300,
            clock=clock,
        )
    )

    assert (
        cooldown.can_deliver(
            make_signal()
        )
        is True
    )


def test_cooldown_blocks_repeated_delivery() -> None:
    clock = FakeClock(
        datetime(
            2026,
            9,
            29,
            tzinfo=timezone.utc,
        )
    )

    cooldown = (
        EarlyMovementScannerPushCooldown(
            cooldown_seconds=300,
            clock=clock,
        )
    )

    signal = make_signal()

    cooldown.mark_delivered(
        signal
    )

    clock.advance(
        seconds=299,
    )

    assert (
        cooldown.can_deliver(
            signal
        )
        is False
    )


def test_cooldown_allows_after_interval() -> None:
    clock = FakeClock(
        datetime(
            2026,
            9,
            29,
            tzinfo=timezone.utc,
        )
    )

    cooldown = (
        EarlyMovementScannerPushCooldown(
            cooldown_seconds=300,
            clock=clock,
        )
    )

    signal = make_signal()

    cooldown.mark_delivered(
        signal
    )

    clock.advance(
        seconds=300,
    )

    assert (
        cooldown.can_deliver(
            signal
        )
        is True
    )


def test_cooldown_clear_resets_state() -> None:
    clock = FakeClock(
        datetime(
            2026,
            9,
            29,
            tzinfo=timezone.utc,
        )
    )

    cooldown = (
        EarlyMovementScannerPushCooldown(
            cooldown_seconds=300,
            clock=clock,
        )
    )

    signal = make_signal()

    cooldown.mark_delivered(
        signal
    )

    assert (
        cooldown.can_deliver(
            signal
        )
        is False
    )

    cooldown.clear()

    assert (
        cooldown.can_deliver(
            signal
        )
        is True
    )