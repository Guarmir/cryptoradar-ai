from dataclasses import dataclass

from app.early_movement.early_movement_confirmation_criterion import (
    EarlyMovementConfirmationCriterion,
)
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)


@dataclass(frozen=True)
class EarlyMovementConfirmationExplanation:
    current_state: EarlyMovementState
    target_state: EarlyMovementState

    criteria: tuple[
        EarlyMovementConfirmationCriterion,
        ...,
    ]

    @property
    def passed_count(
        self,
    ) -> int:
        return sum(
            1
            for criterion in self.criteria
            if criterion.passed
        )

    @property
    def failed_count(
        self,
    ) -> int:
        return (
            len(self.criteria)
            - self.passed_count
        )

    @property
    def is_confirmed(
        self,
    ) -> bool:
        return (
            self.failed_count == 0
            and len(self.criteria) > 0
        )

    @property
    def failed_criteria(
        self,
    ) -> tuple[
        EarlyMovementConfirmationCriterion,
        ...,
    ]:
        return tuple(
            criterion
            for criterion in self.criteria
            if not criterion.passed
        )