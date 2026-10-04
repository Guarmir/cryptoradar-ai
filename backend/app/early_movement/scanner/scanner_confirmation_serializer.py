from typing import Optional

from app.early_movement.early_movement_confirmation_blocker_selector import (
    EarlyMovementConfirmationBlockerSelector,
)
from app.early_movement.early_movement_confirmation_distance_calculator import (
    EarlyMovementConfirmationDistanceCalculator,
)
from app.early_movement.early_movement_confirmation_explainer import (
    EarlyMovementConfirmationExplainer,
)
from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)


class EarlyMovementScannerConfirmationSerializer:
    def __init__(
        self,
        *,
        explainer: Optional[
            EarlyMovementConfirmationExplainer
        ] = None,
        distance_calculator: Optional[
            EarlyMovementConfirmationDistanceCalculator
        ] = None,
        blocker_selector: Optional[
            EarlyMovementConfirmationBlockerSelector
        ] = None,
    ) -> None:
        self._explainer = (
            explainer
            or EarlyMovementConfirmationExplainer()
        )

        self._distance_calculator = (
            distance_calculator
            or EarlyMovementConfirmationDistanceCalculator()
        )

        self._blocker_selector = (
            blocker_selector
            or EarlyMovementConfirmationBlockerSelector(
                distance_calculator=(
                    self._distance_calculator
                ),
            )
        )

    def serialize(
        self,
        evidence: EarlyMovementEvidence,
    ) -> dict:
        explanation = self._explainer.explain(
            evidence,
        )

        missing_criteria = []

        for criterion in (
            explanation.failed_criteria
        ):
            distance = (
                self._distance_calculator.calculate(
                    criterion,
                )
            )

            missing_criteria.append(
                {
                    "key": criterion.key,
                    "label": criterion.label,
                    "value": criterion.value,
                    "threshold": criterion.threshold,
                    "reason": criterion.reason,
                    "distance_ratio": (
                        distance.distance_ratio
                    ),
                    "proximity": (
                        distance.proximity
                    ),
                }
            )

        main_blocker = (
            self._blocker_selector.select(
                explanation.criteria,
            )
        )

        serialized_blocker = None

        if main_blocker is not None:
            serialized_blocker = {
                "key": main_blocker.key,
                "label": main_blocker.label,
                "value": main_blocker.value,
                "threshold": (
                    main_blocker.threshold
                ),
                "distance_ratio": (
                    main_blocker.distance_ratio
                ),
                "proximity": (
                    main_blocker.proximity
                ),
            }

        return {
            "target_state": (
                explanation.target_state.value
            ),
            "passed_count": (
                explanation.passed_count
            ),
            "failed_count": (
                explanation.failed_count
            ),
            "is_confirmed": (
                explanation.is_confirmed
            ),
            "missing_criteria": (
                missing_criteria
            ),
            "main_blocker": (
                serialized_blocker
            ),
        }