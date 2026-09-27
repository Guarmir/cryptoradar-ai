from app.early_movement import EarlyMovementEvaluator, EarlyMovementState


def test_returns_normal_without_relevant_evidence() -> None:
    evaluator = EarlyMovementEvaluator()

    result = evaluator.evaluate(
        price_acceleration=0.20,
        abnormal_volume_ratio=1.05,
        liquidity_score=70.0,
        volatility_expansion=1.02,
        persistence_score=20.0,
        false_breakout_risk=20.0,
    )

    assert result.state is EarlyMovementState.NORMAL


def test_returns_observation_when_market_starts_changing() -> None:
    evaluator = EarlyMovementEvaluator()

    result = evaluator.evaluate(
        price_acceleration=0.60,
        abnormal_volume_ratio=1.30,
        liquidity_score=65.0,
        volatility_expansion=1.18,
        persistence_score=40.0,
        false_breakout_risk=30.0,
    )

    assert result.state is EarlyMovementState.OBSERVATION


def test_returns_early_movement_for_initial_breakout_evidence() -> None:
    evaluator = EarlyMovementEvaluator()

    result = evaluator.evaluate(
        price_acceleration=1.30,
        abnormal_volume_ratio=1.80,
        liquidity_score=68.0,
        volatility_expansion=1.40,
        resistance_break=True,
        persistence_score=58.0,
        false_breakout_risk=28.0,
    )

    assert result.state is EarlyMovementState.EARLY_MOVEMENT


def test_supports_downward_early_movement() -> None:
    evaluator = EarlyMovementEvaluator()

    result = evaluator.evaluate(
        price_acceleration=-1.40,
        abnormal_volume_ratio=1.90,
        liquidity_score=70.0,
        volatility_expansion=1.45,
        support_break=True,
        persistence_score=60.0,
        false_breakout_risk=25.0,
    )

    assert result.state is EarlyMovementState.EARLY_MOVEMENT
    assert result.support_break is True


def test_returns_confirmed_movement_with_strong_confirmation() -> None:
    evaluator = EarlyMovementEvaluator()

    result = evaluator.evaluate(
        price_acceleration=2.40,
        abnormal_volume_ratio=2.60,
        liquidity_score=80.0,
        volatility_expansion=1.70,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=82.0,
        false_breakout_risk=18.0,
    )

    assert result.state is EarlyMovementState.CONFIRMED_MOVEMENT


def test_returns_exhaustion_when_breakout_risk_becomes_high() -> None:
    evaluator = EarlyMovementEvaluator()

    result = evaluator.evaluate(
        price_acceleration=2.10,
        abnormal_volume_ratio=2.30,
        liquidity_score=75.0,
        volatility_expansion=1.80,
        resistance_break=True,
        persistence_score=42.0,
        false_breakout_risk=78.0,
    )

    assert (
        result.state
        is EarlyMovementState.EXHAUSTION_OR_POSSIBLE_REVERSAL
    )


def test_missing_information_does_not_create_false_signal() -> None:
    evaluator = EarlyMovementEvaluator()

    result = evaluator.evaluate(
        abnormal_volume_ratio=1.60,
    )

    assert result.state is EarlyMovementState.OBSERVATION