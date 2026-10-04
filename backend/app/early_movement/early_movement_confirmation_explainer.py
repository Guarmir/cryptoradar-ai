from app.early_movement.early_movement_confirmation_criterion import (
    EarlyMovementConfirmationCriterion,
)
from app.early_movement.early_movement_confirmation_explanation import (
    EarlyMovementConfirmationExplanation,
)
from app.early_movement.early_movement_evaluator import (
    EarlyMovementEvaluator,
)
from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)


class EarlyMovementConfirmationExplainer:
    def explain(
        self,
        evidence: EarlyMovementEvidence,
    ) -> EarlyMovementConfirmationExplanation:
        target_state = self._target_state(
            evidence.state,
        )

        if target_state is EarlyMovementState.CONFIRMED_MOVEMENT:
            criteria = self._confirmed_criteria(
                evidence,
            )
        else:
            criteria = self._early_criteria(
                evidence,
            )

        return EarlyMovementConfirmationExplanation(
            current_state=evidence.state,
            target_state=target_state,
            criteria=criteria,
        )

    @staticmethod
    def _target_state(
        state: EarlyMovementState,
    ) -> EarlyMovementState:
        if state is EarlyMovementState.EARLY_MOVEMENT:
            return EarlyMovementState.CONFIRMED_MOVEMENT

        if state is EarlyMovementState.CONFIRMED_MOVEMENT:
            return EarlyMovementState.CONFIRMED_MOVEMENT

        if (
            state
            is EarlyMovementState.EXHAUSTION_OR_POSSIBLE_REVERSAL
        ):
            return EarlyMovementState.EARLY_MOVEMENT

        return EarlyMovementState.EARLY_MOVEMENT

    def _early_criteria(
        self,
        evidence: EarlyMovementEvidence,
    ) -> tuple[
        EarlyMovementConfirmationCriterion,
        ...,
    ]:
        evaluator = EarlyMovementEvaluator

        breakout_detected = (
            evidence.support_break
            or evidence.resistance_break
        )

        volatility_trigger = self._at_least(
            evidence.volatility_expansion,
            evaluator.EARLY_VOLATILITY_EXPANSION,
        )

        return (
            EarlyMovementConfirmationCriterion(
                key="trigger",
                label="Breakout or volatility expansion",
                passed=(
                    breakout_detected
                    or volatility_trigger
                ),
                reason=(
                    "Requires breakout or sufficient "
                    "volatility expansion."
                ),
            ),
            EarlyMovementConfirmationCriterion(
                key="price_acceleration",
                label="Price acceleration",
                passed=(
                    abs(
                        evidence.price_acceleration
                        or 0.0
                    )
                    >= evaluator.EARLY_PRICE_ACCELERATION
                ),
                value=evidence.price_acceleration,
                threshold=(
                    evaluator.EARLY_PRICE_ACCELERATION
                ),
            ),
            EarlyMovementConfirmationCriterion(
                key="abnormal_volume_ratio",
                label="Abnormal volume",
                passed=self._at_least(
                    evidence.abnormal_volume_ratio,
                    evaluator.EARLY_VOLUME_RATIO,
                ),
                value=evidence.abnormal_volume_ratio,
                threshold=evaluator.EARLY_VOLUME_RATIO,
            ),
            EarlyMovementConfirmationCriterion(
                key="liquidity_score",
                label="Liquidity",
                passed=self._at_least(
                    evidence.liquidity_score,
                    evaluator.EARLY_LIQUIDITY_SCORE,
                ),
                value=evidence.liquidity_score,
                threshold=evaluator.EARLY_LIQUIDITY_SCORE,
            ),
            EarlyMovementConfirmationCriterion(
                key="persistence_score",
                label="Persistence",
                passed=self._at_least(
                    evidence.persistence_score,
                    evaluator.EARLY_PERSISTENCE_SCORE,
                ),
                value=evidence.persistence_score,
                threshold=evaluator.EARLY_PERSISTENCE_SCORE,
            ),
            EarlyMovementConfirmationCriterion(
                key="false_breakout_risk",
                label="False-breakout risk",
                passed=self._at_most(
                    evidence.false_breakout_risk,
                    evaluator.EARLY_MAX_FALSE_BREAKOUT_RISK,
                ),
                value=evidence.false_breakout_risk,
                threshold=(
                    evaluator.EARLY_MAX_FALSE_BREAKOUT_RISK
                ),
            ),
        )

    def _confirmed_criteria(
        self,
        evidence: EarlyMovementEvidence,
    ) -> tuple[
        EarlyMovementConfirmationCriterion,
        ...,
    ]:
        evaluator = EarlyMovementEvaluator

        breakout_detected = (
            evidence.support_break
            or evidence.resistance_break
        )

        return (
            EarlyMovementConfirmationCriterion(
                key="breakout",
                label="Breakout",
                passed=breakout_detected,
            ),
            EarlyMovementConfirmationCriterion(
                key="retest_confirmed",
                label="Retest confirmation",
                passed=evidence.retest_confirmed,
            ),
            EarlyMovementConfirmationCriterion(
                key="price_acceleration",
                label="Price acceleration",
                passed=(
                    abs(
                        evidence.price_acceleration
                        or 0.0
                    )
                    >= evaluator.CONFIRMED_PRICE_ACCELERATION
                ),
                value=evidence.price_acceleration,
                threshold=(
                    evaluator.CONFIRMED_PRICE_ACCELERATION
                ),
            ),
            EarlyMovementConfirmationCriterion(
                key="abnormal_volume_ratio",
                label="Abnormal volume",
                passed=self._at_least(
                    evidence.abnormal_volume_ratio,
                    evaluator.CONFIRMED_VOLUME_RATIO,
                ),
                value=evidence.abnormal_volume_ratio,
                threshold=(
                    evaluator.CONFIRMED_VOLUME_RATIO
                ),
            ),
            EarlyMovementConfirmationCriterion(
                key="liquidity_score",
                label="Liquidity",
                passed=self._at_least(
                    evidence.liquidity_score,
                    evaluator.CONFIRMED_LIQUIDITY_SCORE,
                ),
                value=evidence.liquidity_score,
                threshold=(
                    evaluator.CONFIRMED_LIQUIDITY_SCORE
                ),
            ),
            EarlyMovementConfirmationCriterion(
                key="persistence_score",
                label="Persistence",
                passed=self._at_least(
                    evidence.persistence_score,
                    evaluator.CONFIRMED_PERSISTENCE_SCORE,
                ),
                value=evidence.persistence_score,
                threshold=(
                    evaluator.CONFIRMED_PERSISTENCE_SCORE
                ),
            ),
            EarlyMovementConfirmationCriterion(
                key="false_breakout_risk",
                label="False-breakout risk",
                passed=self._at_most(
                    evidence.false_breakout_risk,
                    evaluator.CONFIRMED_MAX_FALSE_BREAKOUT_RISK,
                ),
                value=evidence.false_breakout_risk,
                threshold=(
                    evaluator.CONFIRMED_MAX_FALSE_BREAKOUT_RISK
                ),
            ),
        )

    @staticmethod
    def _at_least(
        value: float | None,
        threshold: float,
    ) -> bool:
        return (
            value is not None
            and value >= threshold
        )

    @staticmethod
    def _at_most(
        value: float | None,
        threshold: float,
    ) -> bool:
        return (
            value is not None
            and value <= threshold
        )