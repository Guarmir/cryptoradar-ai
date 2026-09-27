from app.early_movement import EarlyMovementEvidence, EarlyMovementState


def test_early_movement_states_have_stable_values() -> None:
    assert EarlyMovementState.NORMAL.value == "normal"
    assert EarlyMovementState.OBSERVATION.value == "observation"
    assert EarlyMovementState.EARLY_MOVEMENT.value == "early_movement"
    assert EarlyMovementState.CONFIRMED_MOVEMENT.value == "confirmed_movement"
    assert (
        EarlyMovementState.EXHAUSTION_OR_POSSIBLE_REVERSAL.value
        == "exhaustion_or_possible_reversal"
    )


def test_early_movement_evidence_keeps_market_evidence() -> None:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.EARLY_MOVEMENT,
        price_acceleration=1.8,
        abnormal_volume_ratio=2.4,
        liquidity_score=82.0,
        volatility_expansion=1.5,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=76.0,
        false_breakout_risk=18.0,
        reason="Price acceleration with abnormal volume.",
        invalidation_reason="Price returned below the breakout level.",
    )

    assert evidence.state is EarlyMovementState.EARLY_MOVEMENT
    assert evidence.price_acceleration == 1.8
    assert evidence.abnormal_volume_ratio == 2.4
    assert evidence.liquidity_score == 82.0
    assert evidence.volatility_expansion == 1.5
    assert evidence.resistance_break is True
    assert evidence.retest_confirmed is True
    assert evidence.persistence_score == 76.0
    assert evidence.false_breakout_risk == 18.0
    assert evidence.reason == "Price acceleration with abnormal volume."
    assert (
        evidence.invalidation_reason
        == "Price returned below the breakout level."
    )


def test_early_movement_evidence_accepts_partial_information() -> None:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.OBSERVATION,
        abnormal_volume_ratio=1.6,
        reason="Volume is rising but movement is not confirmed.",
    )

    assert evidence.state is EarlyMovementState.OBSERVATION
    assert evidence.abnormal_volume_ratio == 1.6
    assert evidence.price_acceleration is None
    assert evidence.resistance_break is False
    assert evidence.support_break is False