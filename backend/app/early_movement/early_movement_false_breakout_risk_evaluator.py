from typing import Optional

from app.early_movement.early_movement_breakout_confirmation import (
    EarlyMovementBreakoutConfirmation,
)
from app.early_movement.early_movement_false_breakout_risk import (
    EarlyMovementFalseBreakoutRisk,
)
from app.early_movement.early_movement_metrics import EarlyMovementMetrics
from app.early_movement.early_movement_price_structure import (
    EarlyMovementPriceStructure,
)


class EarlyMovementFalseBreakoutRiskEvaluator:
    BASE_RISK = 50.0

    def evaluate(
        self,
        *,
        metrics: EarlyMovementMetrics,
        price_structure: EarlyMovementPriceStructure,
        breakout_confirmation: EarlyMovementBreakoutConfirmation,
    ) -> EarlyMovementFalseBreakoutRisk:
        direction = self._resolve_direction(
            price_structure=price_structure,
            breakout_confirmation=breakout_confirmation,
        )

        if direction is None:
            return EarlyMovementFalseBreakoutRisk()

        breakout_distance = self._resolve_breakout_distance(
            direction=direction,
            price_structure=price_structure,
            breakout_confirmation=breakout_confirmation,
        )

        score = self.BASE_RISK
        factors: list[str] = []

        score = self._apply_retest(
            score=score,
            breakout_confirmation=breakout_confirmation,
            factors=factors,
        )

        score = self._apply_volume(
            score=score,
            abnormal_volume_ratio=metrics.abnormal_volume_ratio,
            factors=factors,
        )

        score = self._apply_persistence(
            score=score,
            persistence_score=metrics.persistence_score,
            factors=factors,
        )

        score = self._apply_volatility(
            score=score,
            volatility_expansion=metrics.volatility_expansion,
            factors=factors,
        )

        score = self._apply_breakout_distance(
            score=score,
            breakout_distance=breakout_distance,
            factors=factors,
        )

        return EarlyMovementFalseBreakoutRisk(
            score=self._clamp(score),
            applicable=True,
            breakout_direction=direction,
            breakout_distance_percent=breakout_distance,
            factors=tuple(factors),
        )

    @staticmethod
    def _resolve_direction(
        *,
        price_structure: EarlyMovementPriceStructure,
        breakout_confirmation: EarlyMovementBreakoutConfirmation,
    ) -> Optional[str]:
        if price_structure.resistance_break:
            return "up"

        if price_structure.support_break:
            return "down"

        if breakout_confirmation.retest_confirmed:
            return breakout_confirmation.breakout_direction

        return None

    @staticmethod
    def _resolve_breakout_distance(
        *,
        direction: str,
        price_structure: EarlyMovementPriceStructure,
        breakout_confirmation: EarlyMovementBreakoutConfirmation,
    ) -> Optional[float]:
        if direction == "up":
            distance = (
                price_structure
                .resistance_break_distance_percent
            )

            if distance is not None:
                return abs(distance)

        if direction == "down":
            distance = (
                price_structure
                .support_break_distance_percent
            )

            if distance is not None:
                return abs(distance)

        level = breakout_confirmation.breakout_level
        breakout_price = breakout_confirmation.breakout_price

        if (
            level is None
            or breakout_price is None
            or level <= 0
        ):
            return None

        return abs(
            (
                breakout_price - level
            )
            / level
            * 100.0
        )

    @staticmethod
    def _apply_retest(
        *,
        score: float,
        breakout_confirmation: EarlyMovementBreakoutConfirmation,
        factors: list[str],
    ) -> float:
        if breakout_confirmation.retest_confirmed:
            factors.append(
                "Confirmed retest reduces false-breakout risk."
            )
            return score - 15.0

        factors.append(
            "Breakout has no confirmed retest yet."
        )
        return score + 10.0

    @staticmethod
    def _apply_volume(
        *,
        score: float,
        abnormal_volume_ratio: Optional[float],
        factors: list[str],
    ) -> float:
        if abnormal_volume_ratio is None:
            factors.append(
                "Volume confirmation is unavailable."
            )
            return score + 5.0

        if abnormal_volume_ratio >= 2.0:
            factors.append(
                "Strong abnormal volume supports the breakout."
            )
            return score - 15.0

        if abnormal_volume_ratio >= 1.5:
            factors.append(
                "Above-normal volume supports the breakout."
            )
            return score - 10.0

        if abnormal_volume_ratio < 1.0:
            factors.append(
                "Volume is below its recent baseline."
            )
            return score + 15.0

        if abnormal_volume_ratio < 1.25:
            factors.append(
                "Volume confirmation is weak."
            )
            return score + 8.0

        return score

    @staticmethod
    def _apply_persistence(
        *,
        score: float,
        persistence_score: Optional[float],
        factors: list[str],
    ) -> float:
        if persistence_score is None:
            factors.append(
                "Movement persistence is unavailable."
            )
            return score + 5.0

        if persistence_score >= 70.0:
            factors.append(
                "Strong directional persistence supports the breakout."
            )
            return score - 15.0

        if persistence_score >= 50.0:
            factors.append(
                "Directional persistence supports the breakout."
            )
            return score - 8.0

        if persistence_score < 35.0:
            factors.append(
                "Low directional persistence increases failure risk."
            )
            return score + 15.0

        return score

    @staticmethod
    def _apply_volatility(
        *,
        score: float,
        volatility_expansion: Optional[float],
        factors: list[str],
    ) -> float:
        if volatility_expansion is None:
            factors.append(
                "Volatility context is unavailable."
            )
            return score + 5.0

        if volatility_expansion >= 3.5:
            factors.append(
                "Extreme volatility increases breakout instability."
            )
            return score + 8.0

        if volatility_expansion >= 1.3:
            factors.append(
                "Controlled volatility expansion supports movement."
            )
            return score - 5.0

        if volatility_expansion < 1.0:
            factors.append(
                "Lack of volatility expansion weakens the breakout."
            )
            return score + 8.0

        return score

    @staticmethod
    def _apply_breakout_distance(
        *,
        score: float,
        breakout_distance: Optional[float],
        factors: list[str],
    ) -> float:
        if breakout_distance is None:
            factors.append(
                "Breakout distance is unavailable."
            )
            return score + 5.0

        if breakout_distance < 0.40:
            factors.append(
                "Breakout distance is still very small."
            )
            return score + 10.0

        if 0.75 <= breakout_distance <= 3.0:
            factors.append(
                "Breakout has meaningful distance from its level."
            )
            return score - 10.0

        if breakout_distance > 5.0:
            factors.append(
                "Movement is extended far beyond the breakout level."
            )
            return score + 10.0

        return score

    @staticmethod
    def _clamp(
        value: float,
    ) -> float:
        return max(
            0.0,
            min(100.0, value),
        )