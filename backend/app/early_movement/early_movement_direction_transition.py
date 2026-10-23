
from dataclasses import dataclass
from enum import Enum

from app.early_movement.early_movement_direction import (
    EarlyMovementDirection,
)


class EarlyMovementDirectionTransitionType(str, Enum):
    INITIAL = "initial"
    UNCHANGED = "unchanged"
    WEAKENING = "weakening"
    EMERGING = "emerging"
    REVERSAL = "reversal"


@dataclass(frozen=True)
class EarlyMovementDirectionTransition:
    previous: EarlyMovementDirection | None
    current: EarlyMovementDirection
    transition_type: EarlyMovementDirectionTransitionType


class EarlyMovementDirectionTransitionDetector:
    def detect(
        self,
        *,
        previous: EarlyMovementDirection | None,
        current: EarlyMovementDirection,
    ) -> EarlyMovementDirectionTransition:
        if previous is None:
            transition_type = EarlyMovementDirectionTransitionType.INITIAL
        elif previous == current:
            transition_type = EarlyMovementDirectionTransitionType.UNCHANGED
        elif current == EarlyMovementDirection.NEUTRAL:
            transition_type = EarlyMovementDirectionTransitionType.WEAKENING
        elif previous == EarlyMovementDirection.NEUTRAL:
            transition_type = EarlyMovementDirectionTransitionType.EMERGING
        else:
            transition_type = EarlyMovementDirectionTransitionType.REVERSAL

        return EarlyMovementDirectionTransition(
            previous=previous,
            current=current,
            transition_type=transition_type,
        )
