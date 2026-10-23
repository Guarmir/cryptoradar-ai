
import pytest

from app.early_movement.early_movement_direction import (
    EarlyMovementDirection,
)
from app.early_movement.early_movement_direction_transition import (
    EarlyMovementDirectionTransitionDetector,
    EarlyMovementDirectionTransitionType,
)


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        (
            None,
            EarlyMovementDirection.DOWN,
            EarlyMovementDirectionTransitionType.INITIAL,
        ),
        (
            EarlyMovementDirection.UP,
            EarlyMovementDirection.UP,
            EarlyMovementDirectionTransitionType.UNCHANGED,
        ),
        (
            EarlyMovementDirection.DOWN,
            EarlyMovementDirection.DOWN,
            EarlyMovementDirectionTransitionType.UNCHANGED,
        ),
        (
            EarlyMovementDirection.DOWN,
            EarlyMovementDirection.NEUTRAL,
            EarlyMovementDirectionTransitionType.WEAKENING,
        ),
        (
            EarlyMovementDirection.UP,
            EarlyMovementDirection.NEUTRAL,
            EarlyMovementDirectionTransitionType.WEAKENING,
        ),
        (
            EarlyMovementDirection.NEUTRAL,
            EarlyMovementDirection.UP,
            EarlyMovementDirectionTransitionType.EMERGING,
        ),
        (
            EarlyMovementDirection.NEUTRAL,
            EarlyMovementDirection.DOWN,
            EarlyMovementDirectionTransitionType.EMERGING,
        ),
        (
            EarlyMovementDirection.DOWN,
            EarlyMovementDirection.UP,
            EarlyMovementDirectionTransitionType.REVERSAL,
        ),
        (
            EarlyMovementDirection.UP,
            EarlyMovementDirection.DOWN,
            EarlyMovementDirectionTransitionType.REVERSAL,
        ),
        (
            EarlyMovementDirection.NEUTRAL,
            EarlyMovementDirection.NEUTRAL,
            EarlyMovementDirectionTransitionType.UNCHANGED,
        ),
    ],
)
def test_direction_transition(previous, current, expected):
    detector = EarlyMovementDirectionTransitionDetector()

    result = detector.detect(
        previous=previous,
        current=current,
    )

    assert result.previous == previous
    assert result.current == current
    assert result.transition_type == expected
