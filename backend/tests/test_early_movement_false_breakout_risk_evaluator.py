from app.early_movement import (
    EarlyMovementBreakoutConfirmation,
    EarlyMovementFalseBreakoutRiskEvaluator,
    EarlyMovementMetrics,
    EarlyMovementPriceStructure,
)


def test_strong_confirmed_breakout_has_low_risk() -> None:
    evaluator = (
        EarlyMovementFalseBreakoutRiskEvaluator()
    )

    result = evaluator.evaluate(
        metrics=EarlyMovementMetrics(
            abnormal_volume_ratio=2.2,
            volatility_expansion=1.8,
            persistence_score=82.0,
        ),
        price_structure=EarlyMovementPriceStructure(
            current_price=103.0,
            support_level=99.0,
            resistance_level=102.0,
            resistance_break=True,
            resistance_break_distance_percent=0.98,
        ),
        breakout_confirmation=(
            EarlyMovementBreakoutConfirmation(
                retest_confirmed=True,
                breakout_direction="up",
                breakout_level=102.0,
                breakout_price=103.0,
                retest_price=102.2,
                holding_breakout_level=True,
            )
        ),
    )

    assert result.applicable is True
    assert result.breakout_direction == "up"
    assert result.score is not None
    assert result.score <= 35.0


def test_weak_breakout_has_high_false_breakout_risk() -> None:
    evaluator = (
        EarlyMovementFalseBreakoutRiskEvaluator()
    )

    result = evaluator.evaluate(
        metrics=EarlyMovementMetrics(
            abnormal_volume_ratio=0.8,
            volatility_expansion=0.7,
            persistence_score=20.0,
        ),
        price_structure=EarlyMovementPriceStructure(
            current_price=102.3,
            support_level=99.0,
            resistance_level=102.0,
            resistance_break=True,
            resistance_break_distance_percent=0.29,
        ),
        breakout_confirmation=(
            EarlyMovementBreakoutConfirmation()
        ),
    )

    assert result.applicable is True
    assert result.score is not None
    assert result.score >= 70.0


def test_no_breakout_has_no_false_breakout_score() -> None:
    evaluator = (
        EarlyMovementFalseBreakoutRiskEvaluator()
    )

    result = evaluator.evaluate(
        metrics=EarlyMovementMetrics(
            abnormal_volume_ratio=1.5,
            volatility_expansion=1.4,
            persistence_score=60.0,
        ),
        price_structure=EarlyMovementPriceStructure(
            current_price=101.0,
            support_level=99.0,
            resistance_level=102.0,
        ),
        breakout_confirmation=(
            EarlyMovementBreakoutConfirmation()
        ),
    )

    assert result.applicable is False
    assert result.score is None
    assert result.breakout_direction is None


def test_downward_breakout_is_supported() -> None:
    evaluator = (
        EarlyMovementFalseBreakoutRiskEvaluator()
    )

    result = evaluator.evaluate(
        metrics=EarlyMovementMetrics(
            abnormal_volume_ratio=1.8,
            volatility_expansion=1.5,
            persistence_score=75.0,
        ),
        price_structure=EarlyMovementPriceStructure(
            current_price=97.5,
            support_level=98.8,
            resistance_level=101.0,
            support_break=True,
            support_break_distance_percent=-1.31,
        ),
        breakout_confirmation=(
            EarlyMovementBreakoutConfirmation()
        ),
    )

    assert result.applicable is True
    assert result.breakout_direction == "down"
    assert result.breakout_distance_percent is not None
    assert result.breakout_distance_percent > 0


def test_confirmed_retest_can_supply_breakout_context() -> None:
    evaluator = (
        EarlyMovementFalseBreakoutRiskEvaluator()
    )

    result = evaluator.evaluate(
        metrics=EarlyMovementMetrics(
            abnormal_volume_ratio=2.0,
            volatility_expansion=1.6,
            persistence_score=78.0,
        ),
        price_structure=EarlyMovementPriceStructure(
            current_price=103.2,
            support_level=100.0,
            resistance_level=103.0,
        ),
        breakout_confirmation=(
            EarlyMovementBreakoutConfirmation(
                retest_confirmed=True,
                breakout_direction="up",
                breakout_level=102.0,
                breakout_price=103.0,
                retest_price=102.2,
                holding_breakout_level=True,
            )
        ),
    )

    assert result.applicable is True
    assert result.breakout_direction == "up"

    assert result.breakout_distance_percent is not None
    assert result.breakout_distance_percent > 0

    assert result.score is not None
    assert 0.0 <= result.score <= 100.0