from app.early_movement.early_movement_confirmation_criterion import (
    EarlyMovementConfirmationCriterion,
)
from app.early_movement.early_movement_confirmation_distance import (
    EarlyMovementConfirmationDistance,
)


class EarlyMovementConfirmationDistanceCalculator:
    MAXIMUM_CRITERIA = {
        "false_breakout_risk",
    }

    def calculate(
        self,
        criterion: EarlyMovementConfirmationCriterion,
    ) -> EarlyMovementConfirmationDistance:
        if criterion.passed:
            return EarlyMovementConfirmationDistance(
                key=criterion.key,
                passed=True,
                value=criterion.value,
                threshold=criterion.threshold,
                distance_ratio=0.0,
            )

        if (
            criterion.value is None
            or criterion.threshold is None
            or criterion.threshold <= 0
        ):
            return EarlyMovementConfirmationDistance(
                key=criterion.key,
                passed=False,
                value=criterion.value,
                threshold=criterion.threshold,
                distance_ratio=None,
            )

        if criterion.key in self.MAXIMUM_CRITERIA:
            distance_ratio = (
                criterion.value
                - criterion.threshold
            ) / criterion.threshold
        else:
            distance_ratio = (
                criterion.threshold
                - abs(criterion.value)
            ) / criterion.threshold

        distance_ratio = max(
            0.0,
            distance_ratio,
        )

        return EarlyMovementConfirmationDistance(
            key=criterion.key,
            passed=False,
            value=criterion.value,
            threshold=criterion.threshold,
            distance_ratio=distance_ratio,
        )