
from dataclasses import dataclass
from datetime import datetime, timezone

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_notification_state_store import (
    EarlyMovementScannerNotificationState,
)
from app.early_movement.scanner.scanner_push_evolution_guard import (
    EarlyMovementScannerPushEvolutionGuard,
)


@dataclass(frozen=True)
class FakeSignal:
    coin_id: str
    state: EarlyMovementState


class FakeNotificationStateStore:
    def __init__(self):
        self.records = {}

    def load(self, coin_id):
        return self.records.get(coin_id)

    def save(self, state):
        self.records[state.coin_id] = state


def test_first_notification_is_allowed():
    store = FakeNotificationStateStore()
    guard = EarlyMovementScannerPushEvolutionGuard(
        state_store=store,
    )

    signal = FakeSignal(
        coin_id="bitcoin",
        state=EarlyMovementState.OBSERVATION,
    )

    assert guard.should_notify(signal) is True


def test_repeated_state_is_blocked():
    store = FakeNotificationStateStore()
    guard = EarlyMovementScannerPushEvolutionGuard(
        state_store=store,
    )

    signal = FakeSignal(
        coin_id="bitcoin",
        state=EarlyMovementState.OBSERVATION,
    )

    guard.mark_notified(signal)

    assert guard.should_notify(signal) is False


def test_state_change_is_allowed():
    store = FakeNotificationStateStore()
    guard = EarlyMovementScannerPushEvolutionGuard(
        state_store=store,
    )

    observation = FakeSignal(
        coin_id="bitcoin",
        state=EarlyMovementState.OBSERVATION,
    )

    early_movement = FakeSignal(
        coin_id="bitcoin",
        state=EarlyMovementState.EARLY_MOVEMENT,
    )

    guard.mark_notified(observation)

    assert guard.should_notify(early_movement) is True


def test_state_survives_guard_recreation():
    store = FakeNotificationStateStore()

    signal = FakeSignal(
        coin_id="bitcoin",
        state=EarlyMovementState.OBSERVATION,
    )

    first_guard = EarlyMovementScannerPushEvolutionGuard(
        state_store=store,
    )

    first_guard.mark_notified(signal)

    restarted_guard = EarlyMovementScannerPushEvolutionGuard(
        state_store=store,
    )

    assert restarted_guard.should_notify(signal) is False


def test_notification_state_records_timestamp():
    store = FakeNotificationStateStore()
    guard = EarlyMovementScannerPushEvolutionGuard(
        state_store=store,
    )

    signal = FakeSignal(
        coin_id="bitcoin",
        state=EarlyMovementState.OBSERVATION,
    )

    guard.mark_notified(signal)

    saved = store.load("bitcoin")

    assert isinstance(
        saved,
        EarlyMovementScannerNotificationState,
    )
    assert isinstance(saved.last_notified_at, datetime)
    assert saved.last_notified_at.tzinfo is not None
    assert saved.last_notified_state == "observation"
