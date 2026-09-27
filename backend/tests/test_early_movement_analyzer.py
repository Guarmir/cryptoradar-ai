from app.early_movement import (
    EarlyMovementAnalyzer,
    EarlyMovementState,
)


def _series(
    values: list[float],
) -> list[list[float]]:
    return [
        [
            float(index),
            value,
        ]
        for index, value in enumerate(values)
    ]


def test_analyzer_connects_market_chart_to_evaluator() -> None:
    analyzer = EarlyMovementAnalyzer()

    result = analyzer.analyze(
        {
            "prices": _series(
                [
                    100.0,
                    100.2,
                    100.4,
                    100.6,
                    100.8,
                    101.0,
                    101.2,
                    102.5,
                    104.0,
                    106.0,
                ]
            ),
            "total_volumes": _series(
                [
                    100.0,
                    100.0,
                    110.0,
                    90.0,
                    100.0,
                    100.0,
                    180.0,
                    220.0,
                    200.0,
                ]
            ),
        },
        liquidity_score=75.0,
        resistance_break=True,
        false_breakout_risk=20.0,
    )

    assert (
        result.evidence.state
        is EarlyMovementState.EARLY_MOVEMENT
    )

    assert (
        result.metrics.price_acceleration
        is not None
    )

    assert (
        result.metrics.abnormal_volume_ratio
        is not None
    )

    assert (
        result.metrics.persistence_score
        is not None
    )


def test_analyzer_does_not_fake_missing_context() -> None:
    analyzer = EarlyMovementAnalyzer()

    result = analyzer.analyze(
        {
            "prices": _series(
                [
                    100.0,
                    100.2,
                    100.4,
                    100.6,
                    100.8,
                    101.0,
                    101.2,
                    102.5,
                    104.0,
                    106.0,
                ]
            ),
            "total_volumes": _series(
                [
                    100.0,
                    100.0,
                    110.0,
                    90.0,
                    100.0,
                    100.0,
                    180.0,
                    220.0,
                    200.0,
                ]
            ),
        }
    )

    assert (
        result.evidence.state
        is EarlyMovementState.OBSERVATION
    )

    assert result.evidence.liquidity_score is None
    assert result.evidence.resistance_break is False
    assert result.evidence.support_break is False


def test_analyzer_preserves_downward_market_direction() -> None:
    analyzer = EarlyMovementAnalyzer()

    result = analyzer.analyze(
        {
            "prices": _series(
                [
                    100.0,
                    99.9,
                    99.8,
                    99.7,
                    99.6,
                    99.5,
                    99.4,
                    98.0,
                    96.0,
                    93.0,
                ]
            ),
            "total_volumes": _series(
                [
                    100.0,
                    100.0,
                    100.0,
                    100.0,
                    100.0,
                    100.0,
                    160.0,
                    190.0,
                    220.0,
                ]
            ),
        },
        liquidity_score=80.0,
        support_break=True,
        false_breakout_risk=15.0,
    )

    assert (
        result.evidence.state
        is EarlyMovementState.EARLY_MOVEMENT
    )

    assert result.metrics.price_acceleration is not None
    assert result.metrics.price_acceleration < 0

    assert result.evidence.support_break is True


def test_analyzer_handles_insufficient_market_data_safely() -> None:
    analyzer = EarlyMovementAnalyzer()

    result = analyzer.analyze(
        {
            "prices": _series(
                [
                    100.0,
                    101.0,
                ]
            ),
            "total_volumes": _series(
                [
                    100.0,
                ]
            ),
        }
    )

    assert (
        result.evidence.state
        is EarlyMovementState.NORMAL
    )

    assert result.metrics.price_acceleration is None
    assert result.metrics.abnormal_volume_ratio is None
    assert result.metrics.volatility_expansion is None
    assert result.metrics.persistence_score is None