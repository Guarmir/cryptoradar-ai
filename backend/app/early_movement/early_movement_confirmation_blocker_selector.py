from typing import Optional

from app.early_movement.early_movement_confirmation_blocker import (
    EarlyMovementConfirmationBlocker,
)
from app.early_movement.early_movement_confirmation_criterion import (
    EarlyMovementConfirmationCriterion,
)
from app.early_movement.early_movement_confirmation_distance_calculator import (
    EarlyMovementConfirmationDistanceCalculator,
)


class EarlyMovementConfirmationBlockerSelector:
    def __init__(
        self,
        *,
        distance_calculator: Optional[
            EarlyMovementConfirmationDistanceCalculator
        ] = None,
    ) -> None:
        self._distance_calculator = (
            distance_calculator
            or EarlyMovementConfirmationDistanceCalculator()
        )

    def select(
        self,
        criteria: tuple[
            EarlyMovementConfirmationCriterion,
            ...,
        ],
    ) -> Optional[
        EarlyMovementConfirmationBlocker
    ]:
        failed = [
            criterion
            for criterion in criteria
            if not criterion.passed
        ]

        if not failed:
            return None

        candidates = []

        for criterion in failed:
            distance = (
                self._distance_calculator.calculate(
                    criterion,
                )
            )

            candidates.append(
                (
                    criterion,
                    distance,
                )
            )

        criterion, distance = max(
            candidates,
            key=lambda item: (
                item[1].distance_ratio
                if item[1].distance_ratio
                is not None
                else -1.0
            ),
        )

        return EarlyMovementConfirmationBlocker(
            key=criterion.key,
            label=criterion.label,
            value=criterion.value,
            threshold=criterion.threshold,
            distance_ratio=(
                distance.distance_ratio
            ),
            proximity=distance.proximity,
        )