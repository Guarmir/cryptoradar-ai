from typing import Optional

from app.early_movement.early_movement_evidence import EarlyMovementEvidence
from app.early_movement.early_movement_state import EarlyMovementState


class EarlyMovementEvaluator:
    OBSERVATION_VOLUME_RATIO = 1.25
    OBSERVATION_PRICE_ACCELERATION = 0.50
    OBSERVATION_VOLATILITY_EXPANSION = 1.15
    OBSERVATION_PERSISTENCE_SCORE = 35.0

    EARLY_VOLUME_RATIO = 1.50
    EARLY_PRICE_ACCELERATION = 1.00
    EARLY_VOLATILITY_EXPANSION = 1.30
    EARLY_LIQUIDITY_SCORE = 50.0
    EARLY_PERSISTENCE_SCORE = 50.0
    EARLY_MAX_FALSE_BREAKOUT_RISK = 50.0

    CONFIRMED_VOLUME_RATIO = 2.00
    CONFIRMED_PRICE_ACCELERATION = 2.00
    CONFIRMED_LIQUIDITY_SCORE = 60.0
    CONFIRMED_PERSISTENCE_SCORE = 70.0
    CONFIRMED_MAX_FALSE_BREAKOUT_RISK = 35.0

    EXHAUSTION_FALSE_BREAKOUT_RISK = 70.0

    def evaluate(
        self,
        *,
        price_acceleration: Optional[float] = None,
        abnormal_volume_ratio: Optional[float] = None,
        liquidity_score: Optional[float] = None,
        volatility_expansion: Optional[float] = None,
        support_break: bool = False,
        resistance_break: bool = False,
        retest_confirmed: bool = False,
        persistence_score: Optional[float] = None,
        false_breakout_risk: Optional[float] = None,
    ) -> EarlyMovementEvidence:
        movement_strength = abs(price_acceleration or 0.0)
        breakout_detected = support_break or resistance_break

        if (
            breakout_detected
            and false_breakout_risk is not None
            and false_breakout_risk >= self.EXHAUSTION_FALSE_BREAKOUT_RISK
        ):
            return self._build_evidence(
                state=EarlyMovementState.EXHAUSTION_OR_POSSIBLE_REVERSAL,
                price_acceleration=price_acceleration,
                abnormal_volume_ratio=abnormal_volume_ratio,
                liquidity_score=liquidity_score,
                volatility_expansion=volatility_expansion,
                support_break=support_break,
                resistance_break=resistance_break,
                retest_confirmed=retest_confirmed,
                persistence_score=persistence_score,
                false_breakout_risk=false_breakout_risk,
                reason="Breakout structure has high false-breakout risk.",
                invalidation_reason=(
                    "Risk decreases if the breakout regains persistence "
                    "and confirmation."
                ),
            )

        if (
            breakout_detected
            and retest_confirmed
            and movement_strength >= self.CONFIRMED_PRICE_ACCELERATION
            and self._at_least(
                abnormal_volume_ratio,
                self.CONFIRMED_VOLUME_RATIO,
            )
            and self._at_least(
                liquidity_score,
                self.CONFIRMED_LIQUIDITY_SCORE,
            )
            and self._at_least(
                persistence_score,
                self.CONFIRMED_PERSISTENCE_SCORE,
            )
            and self._at_most(
                false_breakout_risk,
                self.CONFIRMED_MAX_FALSE_BREAKOUT_RISK,
            )
        ):
            return self._build_evidence(
                state=EarlyMovementState.CONFIRMED_MOVEMENT,
                price_acceleration=price_acceleration,
                abnormal_volume_ratio=abnormal_volume_ratio,
                liquidity_score=liquidity_score,
                volatility_expansion=volatility_expansion,
                support_break=support_break,
                resistance_break=resistance_break,
                retest_confirmed=retest_confirmed,
                persistence_score=persistence_score,
                false_breakout_risk=false_breakout_risk,
                reason=(
                    "Movement has breakout, retest, volume, liquidity "
                    "and persistence confirmation."
                ),
                invalidation_reason=(
                    "Movement loses confirmation if breakout structure "
                    "or persistence fails."
                ),
            )

        early_trigger = breakout_detected or self._at_least(
            volatility_expansion,
            self.EARLY_VOLATILITY_EXPANSION,
        )

        if (
            early_trigger
            and movement_strength >= self.EARLY_PRICE_ACCELERATION
            and self._at_least(
                abnormal_volume_ratio,
                self.EARLY_VOLUME_RATIO,
            )
            and self._at_least(
                liquidity_score,
                self.EARLY_LIQUIDITY_SCORE,
            )
            and self._at_least(
                persistence_score,
                self.EARLY_PERSISTENCE_SCORE,
            )
            and self._at_most(
                false_breakout_risk,
                self.EARLY_MAX_FALSE_BREAKOUT_RISK,
            )
        ):
            return self._build_evidence(
                state=EarlyMovementState.EARLY_MOVEMENT,
                price_acceleration=price_acceleration,
                abnormal_volume_ratio=abnormal_volume_ratio,
                liquidity_score=liquidity_score,
                volatility_expansion=volatility_expansion,
                support_break=support_break,
                resistance_break=resistance_break,
                retest_confirmed=retest_confirmed,
                persistence_score=persistence_score,
                false_breakout_risk=false_breakout_risk,
                reason=(
                    "Price, volume and persistence indicate an "
                    "early market movement."
                ),
                invalidation_reason=(
                    "Signal is invalidated if acceleration, volume "
                    "or persistence weakens."
                ),
            )

        observation_trigger = (
            movement_strength >= self.OBSERVATION_PRICE_ACCELERATION
            or self._at_least(
                abnormal_volume_ratio,
                self.OBSERVATION_VOLUME_RATIO,
            )
            or self._at_least(
                volatility_expansion,
                self.OBSERVATION_VOLATILITY_EXPANSION,
            )
            or self._at_least(
                persistence_score,
                self.OBSERVATION_PERSISTENCE_SCORE,
            )
        )

        if observation_trigger:
            return self._build_evidence(
                state=EarlyMovementState.OBSERVATION,
                price_acceleration=price_acceleration,
                abnormal_volume_ratio=abnormal_volume_ratio,
                liquidity_score=liquidity_score,
                volatility_expansion=volatility_expansion,
                support_break=support_break,
                resistance_break=resistance_break,
                retest_confirmed=retest_confirmed,
                persistence_score=persistence_score,
                false_breakout_risk=false_breakout_risk,
                reason=(
                    "Market behavior is changing but does not yet "
                    "confirm an early movement."
                ),
                invalidation_reason=None,
            )

        return self._build_evidence(
            state=EarlyMovementState.NORMAL,
            price_acceleration=price_acceleration,
            abnormal_volume_ratio=abnormal_volume_ratio,
            liquidity_score=liquidity_score,
            volatility_expansion=volatility_expansion,
            support_break=support_break,
            resistance_break=resistance_break,
            retest_confirmed=retest_confirmed,
            persistence_score=persistence_score,
            false_breakout_risk=false_breakout_risk,
            reason="No relevant early-movement evidence detected.",
            invalidation_reason=None,
        )

    @staticmethod
    def _at_least(
        value: Optional[float],
        threshold: float,
    ) -> bool:
        return value is not None and value >= threshold

    @staticmethod
    def _at_most(
        value: Optional[float],
        threshold: float,
    ) -> bool:
        return value is not None and value <= threshold

    @staticmethod
    def _build_evidence(
        *,
        state: EarlyMovementState,
        price_acceleration: Optional[float],
        abnormal_volume_ratio: Optional[float],
        liquidity_score: Optional[float],
        volatility_expansion: Optional[float],
        support_break: bool,
        resistance_break: bool,
        retest_confirmed: bool,
        persistence_score: Optional[float],
        false_breakout_risk: Optional[float],
        reason: str,
        invalidation_reason: Optional[str],
    ) -> EarlyMovementEvidence:
        return EarlyMovementEvidence(
            state=state,
            price_acceleration=price_acceleration,
            abnormal_volume_ratio=abnormal_volume_ratio,
            liquidity_score=liquidity_score,
            volatility_expansion=volatility_expansion,
            support_break=support_break,
            resistance_break=resistance_break,
            retest_confirmed=retest_confirmed,
            persistence_score=persistence_score,
            false_breakout_risk=false_breakout_risk,
            reason=reason,
            invalidation_reason=invalidation_reason,
        )