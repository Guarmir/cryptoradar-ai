import pytest

from app.early_movement.early_movement_confirmation_criterion import (
    EarlyMovementConfirmationCriterion,
)
from app.early_movement.early_movement_confirmation_distance_calculator import (
    EarlyMovementConfirmationDistanceCalculator,
)


def test_near_false_breakout_risk_is_near() -> None:
    calculator = (
        EarlyMovementConfirmationDistanceCalculator()
    )

    result = calculator.calculate(
        EarlyMovementConfirmationCriterion(
            key="false_breakout_risk",
            label="False-breakout risk",
            passed=False,
            value=51.0,
            threshold=50.0,
        )
    )

    assert result.distance_ratio == pytest.approx(
        0.02,
    )
    assert result.proximity == "near"


def test_near_volume_is_insufficient() -> None:
    calculator = (
        EarlyMovementConfirmationDistanceCalculator()
    )

    result = calculator.calculate(
        EarlyMovementConfirmationCriterion(
            key="abnormal_volume_ratio",
            label="Abnormal volume",
            passed=False,
            value=1.0860258476805806,
            threshold=1.5,
        )
    )

    assert result.distance_ratio == pytest.approx(
        0.2759827682,
    )
    assert result.proximity == "insufficient"


def test_zro_persistence_is_far() -> None:
    calculator = (
        EarlyMovementConfirmationDistanceCalculator()
    )

    result = calculator.calculate(
        EarlyMovementConfirmationCriterion(
            key="persistence_score",
            label="Persistence",
            passed=False,
            value=18.66703865598201,
            threshold=50.0,
        )
    )

    assert result.distance_ratio == pytest.approx(
        0.6266592269,
    )
    assert result.proximity == "far"


def test_negative_acceleration_uses_movement_strength() -> None:
    calculator = (
        EarlyMovementConfirmationDistanceCalculator()
    )

    result = calculator.calculate(
        EarlyMovementConfirmationCriterion(
            key="price_acceleration",
            label="Price acceleration",
            passed=False,
            value=-0.75,
            threshold=1.0,
        )
    )

    assert result.distance_ratio == pytest.approx(
        0.25,
    )
    assert result.proximity == "insufficient"


def test_passed_criterion_has_zero_distance() -> None:
    calculator = (
        EarlyMovementConfirmationDistanceCalculator()
    )

    result = calculator.calculate(
        EarlyMovementConfirmationCriterion(
            key="liquidity_score",
            label="Liquidity",
            passed=True,
            value=80.0,
            threshold=50.0,
        )
    )

    assert result.distance_ratio == 0.0
    assert result.proximity == "confirmed"