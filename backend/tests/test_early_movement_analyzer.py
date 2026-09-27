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


def test_analyzer_detects_upward_breakout_automatically() -> None:
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
    )

    assert result.price_structure.resistance_break is True
    assert result.evidence.resistance_break is True

    assert result.false_breakout_risk.applicable is True
    assert result.false_breakout_risk.score is not None

    assert (
        result.evidence.false_breakout_risk
        == result.false_breakout_risk.score
    )

    assert (
        result.evidence.state
        is EarlyMovementState.EARLY_MOVEMENT
    )


def test_analyzer_detects_downward_breakout_automatically() -> None:
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
    )

    assert result.price_structure.support_break is True
    assert result.evidence.support_break is True

    assert result.metrics.price_acceleration is not None
    assert result.metrics.price_acceleration < 0

    assert result.false_breakout_risk.applicable is True
    assert result.false_breakout_risk.score is not None

    assert (
        result.evidence.false_breakout_risk
        == result.false_breakout_risk.score
    )

    assert (
        result.evidence.state
        is EarlyMovementState.EARLY_MOVEMENT
    )


def test_analyzer_uses_upward_retest_automatically() -> None:
    analyzer = EarlyMovementAnalyzer()

    result = analyzer.analyze(
        {
            "prices": _series(
                [
                    100.0,
                    100.5,
                    101.0,
                    101.2,
                    101.5,
                    102.0,
                    103.0,
                    102.2,
                    103.2,
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
                    140.0,
                    130.0,
                    150.0,
                ]
            ),
        }
    )

    assert result.price_structure.resistance_break is False

    assert (
        result.breakout_confirmation.retest_confirmed
        is True
    )

    assert (
        result.breakout_confirmation.breakout_direction
        == "up"
    )

    assert result.evidence.resistance_break is True
    assert result.evidence.retest_confirmed is True

    assert result.false_breakout_risk.applicable is True
    assert result.false_breakout_risk.score is not None

    assert (
        result.evidence.false_breakout_risk
        == result.false_breakout_risk.score
    )


def test_analyzer_uses_downward_retest_automatically() -> None:
    analyzer = EarlyMovementAnalyzer()

    result = analyzer.analyze(
        {
            "prices": _series(
                [
                    100.0,
                    99.8,
                    99.5,
                    99.2,
                    99.0,
                    98.8,
                    97.8,
                    98.6,
                    97.6,
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
                    140.0,
                    130.0,
                    150.0,
                ]
            ),
        }
    )

    assert result.price_structure.support_break is False

    assert (
        result.breakout_confirmation.retest_confirmed
        is True
    )

    assert (
        result.breakout_confirmation.breakout_direction
        == "down"
    )

    assert result.evidence.support_break is True
    assert result.evidence.retest_confirmed is True

    assert result.false_breakout_risk.applicable is True
    assert result.false_breakout_risk.score is not None


def test_analyzer_does_not_create_false_breakout_risk_without_breakout() -> None:
    analyzer = EarlyMovementAnalyzer()

    result = analyzer.analyze(
        {
            "prices": _series(
                [
                    100.0,
                    100.4,
                    100.8,
                    101.0,
                    100.7,
                    100.5,
                    100.9,
                    100.6,
                    100.8,
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
                    100.0,
                    100.0,
                    100.0,
                ]
            ),
        }
    )

    assert result.price_structure.support_break is False
    assert result.price_structure.resistance_break is False

    assert result.false_breakout_risk.applicable is False
    assert result.false_breakout_risk.score is None

    assert result.evidence.false_breakout_risk is None


def test_manual_false_breakout_risk_override_is_preserved() -> None:
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
        false_breakout_risk=12.0,
    )

    assert result.false_breakout_risk.applicable is True
    assert result.false_breakout_risk.score is not None

    assert result.evidence.false_breakout_risk == 12.0


def test_manual_confirmation_override_is_preserved() -> None:
    analyzer = EarlyMovementAnalyzer()

    result = analyzer.analyze(
        {
            "prices": _series(
                [
                    100.0,
                    100.5,
                    101.0,
                    101.2,
                    101.5,
                    102.0,
                    103.0,
                    102.2,
                    103.2,
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
                    140.0,
                    130.0,
                    150.0,
                ]
            ),
        },
        resistance_break=False,
        retest_confirmed=False,
    )

    assert (
        result.breakout_confirmation.retest_confirmed
        is True
    )

    assert result.evidence.resistance_break is False
    assert result.evidence.retest_confirmed is False


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

    assert result.evidence.liquidity_score is None

    assert (
        result.evidence.state
        is EarlyMovementState.OBSERVATION
    )


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

    assert (
        result.breakout_confirmation.retest_confirmed
        is False
    )

    assert result.false_breakout_risk.applicable is False
    assert result.false_breakout_risk.score is None

    assert result.price_structure.support_level is None
    assert result.price_structure.resistance_level is None

    assert result.metrics.price_acceleration is None
    assert result.metrics.abnormal_volume_ratio is None
    assert result.metrics.volatility_expansion is None
    assert result.metrics.persistence_score is None