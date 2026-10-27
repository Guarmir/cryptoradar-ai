import pytest

from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturity,
)
from app.early_movement.extreme_movement.extreme_movement_observation_tracker import (
    ExtremeMovementObservationTracker,
)


def make_entry(
    *,
    direction="up",
    relevance=20.0,
    maturity="early",
):
    return ExtremeMovementAnalysisEntry(
        coin_id="test-coin",
        symbol="TEST",
        name="Test Coin",
        assessment=ExtremeMovementAssessment(
            state="movement_pressure",
            direction=direction,
            relevance_score=relevance,
            supporting_evidence_count=1,
        ),
        maturity=ExtremeMovementMaturity(
            level=maturity,
            evidence_count=1,
            relevance_score=relevance,
        ),
    )


def test_new_observation():
    result = ExtremeMovementObservationTracker().compare(
        None,
        make_entry(),
    )

    assert result.change == "new_observation"


def test_detects_strengthening_by_relevance():
    result = ExtremeMovementObservationTracker().compare(
        make_entry(relevance=20.0),
        make_entry(relevance=40.0),
    )

    assert result.change == "strengthening"


def test_detects_weakening_by_relevance():
    result = ExtremeMovementObservationTracker().compare(
        make_entry(relevance=60.0),
        make_entry(relevance=30.0),
    )

    assert result.change == "weakening"


def test_detects_maturity_progression():
    result = ExtremeMovementObservationTracker().compare(
        make_entry(maturity="early"),
        make_entry(maturity="developing"),
    )

    assert result.change == "strengthening"


def test_detects_maturity_regression():
    result = ExtremeMovementObservationTracker().compare(
        make_entry(maturity="supported"),
        make_entry(maturity="developing"),
    )

    assert result.change == "weakening"


def test_detects_direction_change():
    result = ExtremeMovementObservationTracker().compare(
        make_entry(direction="up"),
        make_entry(direction="down"),
    )

    assert result.change == "direction_change"


def test_ignores_small_fluctuations():
    result = ExtremeMovementObservationTracker().compare(
        make_entry(relevance=20.0),
        make_entry(relevance=24.0),
    )

    assert result.change == "stable"


@pytest.mark.parametrize(
    "previous_direction,current_direction",
    [
        ("neutral", "up"),
        ("up", "neutral"),
    ],
)
def test_neutral_transition_is_not_direction_reversal(
    previous_direction,
    current_direction,
):
    result = ExtremeMovementObservationTracker().compare(
        make_entry(direction=previous_direction),
        make_entry(direction=current_direction),
    )

    assert result.change == "stable"