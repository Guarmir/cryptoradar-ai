import pytest

from app.early_movement.early_movement_confirmation_blocker_selector import (
    EarlyMovementConfirmationBlockerSelector,
)
from app.early_movement.early_movement_confirmation_criterion import (
    EarlyMovementConfirmationCriterion,
)


def test_zro_selects_persistence_as_main_blocker() -> None:
    selector = (
        EarlyMovementConfirmationBlockerSelector()
    )

    criteria = (
        EarlyMovementConfirmationCriterion(
            key="abnormal_volume_ratio",
            label="Abnormal volume",
            passed=False,
            value=1.0018353709629115,
            threshold=1.5,
        ),
        EarlyMovementConfirmationCriterion(
            key="persistence_score",
            label="Persistence",
            passed=False,
            value=18.66703865598201,
            threshold=50.0,
        ),
    )

    result = selector.select(
        criteria,
    )

    assert result is not None

    assert (
        result.key
        == "persistence_score"
    )

    assert result.value == pytest.approx(
        18.66703865598201,
    )

    assert result.threshold == 50.0

    assert result.distance_ratio == pytest.approx(
        0.6266592269,
    )

    assert result.proximity == "far"


def test_near_selects_persistence_as_main_blocker() -> None:
    selector = (
        EarlyMovementConfirmationBlockerSelector()
    )

    criteria = (
        EarlyMovementConfirmationCriterion(
            key="abnormal_volume_ratio",
            label="Abnormal volume",
            passed=False,
            value=1.0860258476805806,
            threshold=1.5,
        ),
        EarlyMovementConfirmationCriterion(
            key="persistence_score",
            label="Persistence",
            passed=False,
            value=37.776819958297594,
            threshold=50.0,
        ),
        EarlyMovementConfirmationCriterion(
            key="false_breakout_risk",
            label="False-breakout risk",
            passed=False,
            value=51.0,
            threshold=50.0,
        ),
    )

    result = selector.select(
        criteria,
    )

    assert result is not None

    assert (
        result.key
        == "abnormal_volume_ratio"
    )

    assert result.distance_ratio == pytest.approx(
        0.2759827682,
    )

    assert result.proximity == "insufficient"


def test_returns_none_when_all_criteria_pass() -> None:
    selector = (
        EarlyMovementConfirmationBlockerSelector()
    )

    criteria = (
        EarlyMovementConfirmationCriterion(
            key="liquidity_score",
            label="Liquidity",
            passed=True,
            value=80.0,
            threshold=50.0,
        ),
        EarlyMovementConfirmationCriterion(
            key="persistence_score",
            label="Persistence",
            passed=True,
            value=75.0,
            threshold=50.0,
        ),
    )

    result = selector.select(
        criteria,
    )

    assert result is None