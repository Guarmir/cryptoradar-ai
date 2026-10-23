
from app.early_movement.early_movement_direction import (
    EarlyMovementDirection,
)
from app.early_movement.early_movement_metrics import (
    EarlyMovementMetrics,
)
from app.early_movement.early_movement_price_structure import (
    EarlyMovementPriceStructure,
)


class EarlyMovementDirectionClassifier:
    MIN_RETURN_PERCENT = 0.5
    MIN_ACCELERATION_PERCENT = 0.1
    MIN_PERSISTENCE_SCORE = 35.0

    def classify(
        self,
        *,
        metrics: EarlyMovementMetrics,
        price_structure: EarlyMovementPriceStructure,
    ) -> EarlyMovementDirection:
        recent_return = metrics.recent_price_return
        acceleration = metrics.price_acceleration

        if recent_return is None or acceleration is None:
            return EarlyMovementDirection.NEUTRAL

        if (
            price_structure.support_break
            and price_structure.resistance_break
        ):
            return EarlyMovementDirection.NEUTRAL

        if (
            recent_return >= self.MIN_RETURN_PERCENT
            and acceleration >= self.MIN_ACCELERATION_PERCENT
        ):
            if price_structure.support_break:
                return EarlyMovementDirection.NEUTRAL

            if (
                price_structure.resistance_break
                or self._has_early_evidence(metrics)
            ):
                return EarlyMovementDirection.UP

        if (
            recent_return <= -self.MIN_RETURN_PERCENT
            and acceleration <= -self.MIN_ACCELERATION_PERCENT
        ):
            if price_structure.resistance_break:
                return EarlyMovementDirection.NEUTRAL

            if (
                price_structure.support_break
                or self._has_early_evidence(metrics)
            ):
                return EarlyMovementDirection.DOWN

        return EarlyMovementDirection.NEUTRAL

    def _has_early_evidence(
        self,
        metrics: EarlyMovementMetrics,
    ) -> bool:
        persistence = metrics.persistence_score
        volume_ratio = metrics.abnormal_volume_ratio

        return (
            persistence is not None
            and persistence >= self.MIN_PERSISTENCE_SCORE
            and volume_ratio is not None
            and volume_ratio >= 1.25
        )
