
from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)


class EarlyMovementScannerEarlyObservationEvaluator:
    MIN_LIQUIDITY_SCORE = 50.0
    MIN_PERSISTENCE_SCORE = 35.0
    MIN_PRICE_ACCELERATION = 0.50
    MAX_FALSE_BREAKOUT_RISK = 55.0

    MIN_VOLUME_RATIO = 0.75
    MIN_SUPPORTING_EVIDENCES = 3

    def is_relevant(
        self,
        evidence: EarlyMovementEvidence,
    ) -> bool:
        if evidence.state is not EarlyMovementState.OBSERVATION:
            return False

        if (
            evidence.liquidity_score is None
            or evidence.liquidity_score < self.MIN_LIQUIDITY_SCORE
        ):
            return False

        if (
            evidence.persistence_score is None
            or evidence.persistence_score < self.MIN_PERSISTENCE_SCORE
        ):
            return False

        if (
            evidence.false_breakout_risk is None
            or evidence.false_breakout_risk > self.MAX_FALSE_BREAKOUT_RISK
        ):
            return False

        acceleration = evidence.price_acceleration

        if (
            acceleration is None
            or abs(acceleration) < self.MIN_PRICE_ACCELERATION
        ):
            return False

        if (
            evidence.support_break
            and evidence.resistance_break
        ):
            return False

        if (
            evidence.support_break
            and acceleration >= 0
        ):
            return False

        if (
            evidence.resistance_break
            and acceleration <= 0
        ):
            return False

        volume_ratio = evidence.abnormal_volume_ratio

        if (
            volume_ratio is None
            or volume_ratio < self.MIN_VOLUME_RATIO
        ):
            return False

        supporting_evidences = 0

        if evidence.support_break or evidence.resistance_break:
            supporting_evidences += 1

        if evidence.retest_confirmed:
            supporting_evidences += 1

        if volume_ratio >= 1.0:
            supporting_evidences += 1

        if (
            evidence.volatility_expansion is not None
            and evidence.volatility_expansion >= 1.15
        ):
            supporting_evidences += 1

        if evidence.persistence_score >= 50.0:
            supporting_evidences += 1

        return (
            supporting_evidences
            >= self.MIN_SUPPORTING_EVIDENCES
        )
