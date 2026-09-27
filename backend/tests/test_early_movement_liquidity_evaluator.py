from app.early_movement.liquidity import (
    EarlyMovementLiquidityEvaluator,
)


def test_high_liquidity_market_receives_high_score() -> None:
    evaluator = EarlyMovementLiquidityEvaluator()

    result = evaluator.evaluate(
        {
            "total_volume": 500_000_000,
            "market_cap": 5_000_000_000,
        }
    )

    assert result.available is True
    assert result.score == 86.0

    assert (
        result.volume_to_market_cap_ratio
        == 0.10
    )


def test_medium_liquidity_market_can_be_usable() -> None:
    evaluator = EarlyMovementLiquidityEvaluator()

    result = evaluator.evaluate(
        {
            "total_volume": 60_000_000,
            "market_cap": 3_000_000_000,
        }
    )

    assert result.available is True
    assert result.score == 56.0

    assert (
        result.volume_to_market_cap_ratio
        == 0.02
    )


def test_low_liquidity_market_receives_low_score() -> None:
    evaluator = EarlyMovementLiquidityEvaluator()

    result = evaluator.evaluate(
        {
            "total_volume": 2_000_000,
            "market_cap": 200_000_000,
        }
    )

    assert result.available is True
    assert result.score == 24.0

    assert (
        result.volume_to_market_cap_ratio
        == 0.01
    )


def test_high_volume_can_still_be_scored_without_market_cap() -> None:
    evaluator = EarlyMovementLiquidityEvaluator()

    result = evaluator.evaluate(
        {
            "total_volume": 300_000_000,
            "market_cap": None,
        }
    )

    assert result.available is True
    assert result.score == 52.0
    assert result.market_cap is None

    assert (
        result.volume_to_market_cap_ratio
        is None
    )


def test_missing_volume_does_not_create_fake_liquidity() -> None:
    evaluator = EarlyMovementLiquidityEvaluator()

    result = evaluator.evaluate(
        {
            "market_cap": 5_000_000_000,
        }
    )

    assert result.available is False
    assert result.score is None
    assert result.total_volume is None