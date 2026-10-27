import pytest

from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturityEvaluator,
)


def make_assessment(
    *,
    evidence_count,
    relevance_score,
):
    return ExtremeMovementAssessment(
        state="movement_pressure",
        direction="up",
        relevance_score=relevance_score,
        supporting_evidence_count=evidence_count,
    )


@pytest.mark.parametrize(
    "evidence_count,relevance_score,expected",
    [
        (0, 2.9, "early"),
        (0, 24.9, "early"),
        (0, 25.0, "developing"),
        (1, 5.0, "developing"),
        (2, 49.0, "developing"),
        (3, 49.0, "developing"),
        (3, 50.0, "supported"),
        (4, 85.0, "supported"),
    ],
)
def test_maturity_classification(
    evidence_count,
    relevance_score,
    expected,
):
    result = ExtremeMovementMaturityEvaluator().evaluate(
        make_assessment(
            evidence_count=evidence_count,
            relevance_score=relevance_score,
        )
    )

    assert result.level == expected


def test_preserves_weak_signal():
    result = ExtremeMovementMaturityEvaluator().evaluate(
        make_assessment(
            evidence_count=0,
            relevance_score=2.9,
        )
    )

    assert result.level == "early"
    assert result.evidence_count == 0


def test_limits_relevance_score():
    result = ExtremeMovementMaturityEvaluator().evaluate(
        make_assessment(
            evidence_count=4,
            relevance_score=150.0,
        )
    )

    assert result.relevance_score == 100.0