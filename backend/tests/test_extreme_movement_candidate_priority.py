
import pytest

from app.early_movement.extreme_movement.extreme_movement_candidate_priority import (
    ExtremeMovementCandidatePriorityEvaluator,
)
from app.early_movement.extreme_movement.extreme_movement_candidate_tracker import (
    ExtremeMovementCandidateEvolution,
)


def make_evolution(
    *,
    observations=2,
    price_change=1.0,
    volume_change=10.0,
    change_delta=1.0,
):
    return ExtremeMovementCandidateEvolution(
        coin_id="test-coin",
        observation_count=observations,
        price_change_since_previous_pct=price_change,
        volume_change_since_previous_pct=volume_change,
        change_24h_delta=change_delta,
        state="rising",
    )


def test_first_observation_remains_observing():
    evaluator = ExtremeMovementCandidatePriorityEvaluator()

    result = evaluator.evaluate(
        make_evolution(observations=1)
    )

    assert result.score == 0
    assert result.state == "observing"
    assert result.direction == "unknown"
    assert result.evidence_count == 0


def test_strong_upward_activity_is_priority():
    evaluator = ExtremeMovementCandidatePriorityEvaluator()

    result = evaluator.evaluate(
        make_evolution(
            price_change=5.0,
            volume_change=30.0,
            change_delta=5.0,
        )
    )

    assert result.score == 100
    assert result.state == "priority"
    assert result.direction == "up"
    assert result.evidence_count == 3


def test_strong_downward_activity_is_priority():
    evaluator = ExtremeMovementCandidatePriorityEvaluator()

    result = evaluator.evaluate(
        make_evolution(
            price_change=-5.0,
            volume_change=30.0,
            change_delta=-5.0,
        )
    )

    assert result.score == 100
    assert result.state == "priority"
    assert result.direction == "down"
    assert result.evidence_count == 3


def test_moderate_activity_is_strengthening():
    evaluator = ExtremeMovementCandidatePriorityEvaluator()

    result = evaluator.evaluate(
        make_evolution(
            price_change=1.0,
            volume_change=10.0,
            change_delta=1.0,
        )
    )

    assert result.score == pytest.approx(24.0)
    assert result.state == "strengthening"
    assert result.evidence_count == 3


def test_low_activity_is_weakening():
    evaluator = ExtremeMovementCandidatePriorityEvaluator()

    result = evaluator.evaluate(
        make_evolution(
            price_change=0.1,
            volume_change=0.0,
            change_delta=0.0,
        )
    )

    assert result.score == pytest.approx(0.8)
    assert result.state == "weakening"
    assert result.evidence_count == 0


def test_missing_price_data_remains_observing():
    evaluator = ExtremeMovementCandidatePriorityEvaluator()

    result = evaluator.evaluate(
        make_evolution(price_change=None)
    )

    assert result.score == 0
    assert result.state == "observing"
    assert result.direction == "unknown"


def test_volume_and_delta_do_not_override_opposite_direction():
    evaluator = ExtremeMovementCandidatePriorityEvaluator()

    result = evaluator.evaluate(
        make_evolution(
            price_change=1.0,
            volume_change=30.0,
            change_delta=-5.0,
        )
    )

    assert result.score == pytest.approx(38.0)
    assert result.direction == "up"
    assert result.evidence_count == 2
    assert result.state == "strengthening"


def test_score_is_capped_at_100():
    evaluator = ExtremeMovementCandidatePriorityEvaluator()

    result = evaluator.evaluate(
        make_evolution(
            price_change=50.0,
            volume_change=500.0,
            change_delta=50.0,
        )
    )

    assert result.score == 100
    assert result.state == "priority"
