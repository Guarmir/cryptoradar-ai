from app.early_movement.early_movement_confirmation_explainer import (
    EarlyMovementConfirmationExplainer,
)
from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)


def _criteria_by_key(
    explanation,
):
    return {
        criterion.key: criterion
        for criterion in explanation.criteria
    }


def test_explains_observation_missing_volume_confirmation() -> None:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.OBSERVATION,
        price_acceleration=1.07,
        abnormal_volume_ratio=0.99,
        liquidity_score=80.0,
        volatility_expansion=1.68,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=100.0,
        false_breakout_risk=30.0,
    )

    explanation = (
        EarlyMovementConfirmationExplainer()
        .explain(
            evidence,
        )
    )

    assert (
        explanation.current_state
        is EarlyMovementState.OBSERVATION
    )

    assert (
        explanation.target_state
        is EarlyMovementState.EARLY_MOVEMENT
    )

    criteria = _criteria_by_key(
        explanation,
    )

    assert criteria["trigger"].passed
    assert criteria["price_acceleration"].passed
    assert not criteria["abnormal_volume_ratio"].passed
    assert criteria["liquidity_score"].passed
    assert criteria["persistence_score"].passed
    assert criteria["false_breakout_risk"].passed

    assert explanation.passed_count == 5
    assert explanation.failed_count == 1
    assert not explanation.is_confirmed

    assert (
        explanation.failed_criteria[0].key
        == "abnormal_volume_ratio"
    )


def test_explains_exhaustion_with_weak_confirmation() -> None:
    evidence = EarlyMovementEvidence(
        state=(
            EarlyMovementState
            .EXHAUSTION_OR_POSSIBLE_REVERSAL
        ),
        price_acceleration=0.38,
        abnormal_volume_ratio=0.78,
        liquidity_score=80.0,
        volatility_expansion=0.86,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=22.66,
        false_breakout_risk=83.0,
    )

    explanation = (
        EarlyMovementConfirmationExplainer()
        .explain(
            evidence,
        )
    )

    criteria = _criteria_by_key(
        explanation,
    )

    assert (
        explanation.target_state
        is EarlyMovementState.EARLY_MOVEMENT
    )

    assert criteria["trigger"].passed
    assert not criteria["price_acceleration"].passed
    assert not criteria["abnormal_volume_ratio"].passed
    assert criteria["liquidity_score"].passed
    assert not criteria["persistence_score"].passed
    assert not criteria["false_breakout_risk"].passed

    assert explanation.passed_count == 2
    assert explanation.failed_count == 4
    assert not explanation.is_confirmed


def test_explains_early_movement_requirements_for_confirmation() -> None:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.EARLY_MOVEMENT,
        price_acceleration=1.40,
        abnormal_volume_ratio=1.80,
        liquidity_score=70.0,
        volatility_expansion=1.45,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=60.0,
        false_breakout_risk=25.0,
    )

    explanation = (
        EarlyMovementConfirmationExplainer()
        .explain(
            evidence,
        )
    )

    criteria = _criteria_by_key(
        explanation,
    )

    assert (
        explanation.target_state
        is EarlyMovementState.CONFIRMED_MOVEMENT
    )

    assert criteria["breakout"].passed
    assert criteria["retest_confirmed"].passed
    assert not criteria["price_acceleration"].passed
    assert not criteria["abnormal_volume_ratio"].passed
    assert criteria["liquidity_score"].passed
    assert not criteria["persistence_score"].passed
    assert criteria["false_breakout_risk"].passed

    assert explanation.passed_count == 4
    assert explanation.failed_count == 3
    assert not explanation.is_confirmed


def test_explains_fully_confirmed_movement() -> None:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.CONFIRMED_MOVEMENT,
        price_acceleration=2.40,
        abnormal_volume_ratio=2.60,
        liquidity_score=80.0,
        volatility_expansion=1.70,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=82.0,
        false_breakout_risk=18.0,
    )

    explanation = (
        EarlyMovementConfirmationExplainer()
        .explain(
            evidence,
        )
    )

    assert (
        explanation.target_state
        is EarlyMovementState.CONFIRMED_MOVEMENT
    )

    assert explanation.passed_count == 7
    assert explanation.failed_count == 0
    assert explanation.is_confirmed
    assert explanation.failed_criteria == ()