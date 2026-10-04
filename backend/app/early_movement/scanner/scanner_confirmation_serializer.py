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
        explainer: EarlyMovementConfirmationExplainer | None = None,
    ) -> None:
        self._explainer = (
            explainer
            or EarlyMovementConfirmationExplainer()
        )

    def serialize(
        self,
        evidence: EarlyMovementEvidence,
    ) -> dict:
        explanation = self._explainer.explain(
            evidence,
        )

        failed_criteria = [
            {
                "key": criterion.key,
                "label": criterion.label,
                "value": criterion.value,
                "threshold": criterion.threshold,
                "reason": criterion.reason,
            }
            for criterion in explanation.failed_criteria
        ]

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
                failed_criteria
            ),
        }