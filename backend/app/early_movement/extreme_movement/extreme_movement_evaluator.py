import math

from app.early_movement.early_movement_metrics import (
    EarlyMovementMetrics,
)
from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)


class ExtremeMovementEvaluator:
    MIN_RECENT_RETURN = 1.0
    MIN_ACCELERATION = 0.5
    MIN_VOLUME_RATIO = 1.5
    MIN_VOLATILITY_EXPANSION = 1.5
    MIN_PERSISTENCE = 35.0

    def evaluate(
        self,
        metrics: EarlyMovementMetrics,
    ) -> ExtremeMovementAssessment:
        recent_return = self._finite(
            metrics.recent_price_return
        )
        acceleration = self._finite(
            metrics.price_acceleration
        )
        volume_ratio = self._finite(
            metrics.abnormal_volume_ratio
        )
        volatility = self._finite(
            metrics.volatility_expansion
        )
        persistence = self._finite(
            metrics.persistence_score
        )

        if recent_return is None or acceleration is None:
            return self._assessment(
                "insufficient_evidence",
                "neutral",
                0,
                0.0,
            )

        direction = "up" if recent_return > 0 else (
            "down" if recent_return < 0 else "neutral"
        )

        if (
            abs(recent_return) < self.MIN_RECENT_RETURN
            or direction == "neutral"
        ):
            return self._assessment(
                "insufficient_evidence",
                direction,
                0,
                0.0,
            )

        aligned_acceleration = (
            acceleration > 0
            if direction == "up"
            else acceleration < 0
        )

        opposing_acceleration = (
            acceleration < 0
            if direction == "up"
            else acceleration > 0
        )

        strong_acceleration = (
            abs(acceleration) >= self.MIN_ACCELERATION
        )

        strong_volume = (
            volume_ratio is not None
            and volume_ratio >= self.MIN_VOLUME_RATIO
        )

        expanding_volatility = (
            volatility is not None
            and volatility >= self.MIN_VOLATILITY_EXPANSION
        )

        persistent = (
            persistence is not None
            and persistence >= self.MIN_PERSISTENCE
        )

        supporting_evidence_count = sum(
            (
                strong_acceleration,
                strong_volume,
                expanding_volatility,
                persistent,
            )
        )

        relevance_score = min(
            100.0,
            (
                min(abs(recent_return), 20.0) * 2.0
                + min(abs(acceleration), 20.0) * 1.5
                + (20.0 if strong_volume else 0.0)
                + (15.0 if expanding_volatility else 0.0)
                + (10.0 if persistent else 0.0)
            ),
        )

        if (
            opposing_acceleration
            and strong_acceleration
            and supporting_evidence_count >= 2
        ):
            state = "possible_reversal"

        elif (
            aligned_acceleration
            and strong_acceleration
            and strong_volume
            and supporting_evidence_count >= 3
        ):
            state = "extreme_acceleration"

        else:
            state = "movement_pressure"

        return self._assessment(
            state,
            direction,
            supporting_evidence_count,
            relevance_score,
        )

    @staticmethod
    def _finite(value):
        if value is None:
            return None

        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None

        if not math.isfinite(parsed):
            return None

        return parsed

    @staticmethod
    def _assessment(
        state: str,
        direction: str,
        evidence_count: int,
        relevance_score: float,
    ) -> ExtremeMovementAssessment:
        return ExtremeMovementAssessment(
            state=state,
            direction=direction,
            relevance_score=relevance_score,
            supporting_evidence_count=evidence_count,
        )