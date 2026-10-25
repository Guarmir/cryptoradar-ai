import pytest

from app.early_movement.early_movement_metrics import (
    EarlyMovementMetrics,
)
from app.early_movement.extreme_movement.extreme_movement_evaluator import (
    ExtremeMovementEvaluator,
)


def make_metrics(
    *,
    recent_return=5.0,
    acceleration=3.0,
    volume=2.0,
    volatility=2.0,
    persistence=70.0,
):
    return EarlyMovementMetrics(
        recent_price_return=recent_return,
        price_acceleration=acceleration,
        abnormal_volume_ratio=volume,
        volatility_expansion=volatility,
        persistence_score=persistence,
    )


def test_detects_extreme_upward_acceleration():
    result = ExtremeMovementEvaluator().evaluate(
        make_metrics()
    )

    assert result.state == "extreme_acceleration"
    assert result.direction == "up"
    assert result.supporting_evidence_count == 4


def test_detects_extreme_downward_acceleration():
    result = ExtremeMovementEvaluator().evaluate(
        make_metrics(
            recent_return=-8.0,
            acceleration=-4.0,
        )
    )

    assert result.state == "extreme_acceleration"
    assert result.direction == "down"


def test_detects_possible_bearish_reversal():
    result = ExtremeMovementEvaluator().evaluate(
        make_metrics(
            recent_return=8.0,
            acceleration=-5.0,
        )
    )

    assert result.state == "possible_reversal"
    assert result.direction == "up"


def test_detects_possible_bullish_reversal():
    result = ExtremeMovementEvaluator().evaluate(
        make_metrics(
            recent_return=-8.0,
            acceleration=5.0,
        )
    )

    assert result.state == "possible_reversal"
    assert result.direction == "down"


def test_detects_movement_pressure():
    result = ExtremeMovementEvaluator().evaluate(
        make_metrics(
            recent_return=4.0,
            acceleration=0.2,
            volume=1.0,
            volatility=1.0,
            persistence=20.0,
        )
    )

    assert result.state == "movement_pressure"


def test_rejects_insufficient_data():
    result = ExtremeMovementEvaluator().evaluate(
        EarlyMovementMetrics()
    )

    assert result.state == "insufficient_evidence"
    assert result.direction == "neutral"


def test_rejects_small_movement():
    result = ExtremeMovementEvaluator().evaluate(
        make_metrics(
            recent_return=0.2,
        )
    )

    assert result.state == "insufficient_evidence"


def test_relevance_score_is_bounded():
    result = ExtremeMovementEvaluator().evaluate(
        make_metrics(
            recent_return=400.0,
            acceleration=200.0,
            volume=5.0,
            volatility=4.0,
            persistence=100.0,
        )
    )

    assert 0.0 <= result.relevance_score <= 100.0


@pytest.mark.parametrize(
    "invalid_value",
    [float("nan"), float("inf"), float("-inf")],
)
def test_rejects_invalid_acceleration(invalid_value):
    result = ExtremeMovementEvaluator().evaluate(
        make_metrics(acceleration=invalid_value)
    )

    assert result.state == "insufficient_evidence"