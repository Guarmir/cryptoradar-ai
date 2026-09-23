from app.ai.asset_operational_range_assessment import (
    calculate_asset_operational_range,
)
from app.ai.asset_operational_range_recurrence_assessment import (
    calculate_asset_operational_range_recurrence,
)


def test_detects_minimum_recurrence() -> None:
    prices = (
        100.0,
        100.5,
        102.5,
        104.5,
        105.0,
        102.5,
        100.4,
        102.5,
        104.2,
    )

    range_assessment = (
        calculate_asset_operational_range(
            current_price=102.5,
            prices=prices,
        )
    )

    assert range_assessment is not None

    recurrence = (
        calculate_asset_operational_range_recurrence(
            prices=prices,
            range_assessment=(
                range_assessment
            ),
        )
    )

    assert recurrence is not None

    assert (
        recurrence.lower_limit_touches
        == 2
    )

    assert (
        recurrence.upper_limit_touches
        == 2
    )

    assert (
        recurrence.observed_points_count
        == 9
    )

    assert (
        recurrence.total_limit_touches
        == 4
    )

    assert (
        recurrence.completed_oscillations
        == 2
    )

    assert (
        recurrence.has_both_limits_tested
        is True
    )

    assert (
        recurrence.has_minimum_recurrence
        is True
    )

    assert (
        recurrence.has_strong_recurrence
        is False
    )

    assert (
        recurrence.suggests_recurring_range
        is True
    )

    assert (
        recurrence
        .suggests_organized_oscillation
        is False
    )

    assert (
        recurrence.state
        == "recurring_range"
    )


def test_detects_organized_oscillation() -> None:
    prices = (
        100.0,
        102.5,
        105.0,
        102.5,
        100.4,
        102.5,
        104.5,
        102.5,
        100.2,
        102.5,
        104.8,
    )

    range_assessment = (
        calculate_asset_operational_range(
            current_price=102.5,
            prices=prices,
        )
    )

    assert range_assessment is not None

    recurrence = (
        calculate_asset_operational_range_recurrence(
            prices=prices,
            range_assessment=(
                range_assessment
            ),
        )
    )

    assert recurrence is not None

    assert (
        recurrence.lower_limit_touches
        == 3
    )

    assert (
        recurrence.upper_limit_touches
        == 3
    )

    assert (
        recurrence.has_strong_recurrence
        is True
    )

    assert (
        recurrence.is_unbalanced
        is False
    )

    assert (
        recurrence
        .suggests_organized_oscillation
        is True
    )

    assert (
        recurrence.state
        == "organized_oscillation"
    )


def test_detects_insufficient_recurrence() -> None:
    prices = (
        100.0,
        102.5,
        105.0,
    )

    range_assessment = (
        calculate_asset_operational_range(
            current_price=102.5,
            prices=prices,
        )
    )

    assert range_assessment is not None

    recurrence = (
        calculate_asset_operational_range_recurrence(
            prices=prices,
            range_assessment=(
                range_assessment
            ),
        )
    )

    assert recurrence is not None

    assert (
        recurrence.has_minimum_recurrence
        is False
    )

    assert (
        recurrence.suggests_recurring_range
        is False
    )

    assert (
        recurrence.state
        == "insufficient_recurrence"
    )


def test_collapses_consecutive_limit_points_into_one_touch() -> None:
    prices = (
        100.0,
        100.2,
        100.4,
        102.5,
        105.0,
        104.8,
        104.5,
    )

    range_assessment = (
        calculate_asset_operational_range(
            current_price=102.5,
            prices=prices,
        )
    )

    assert range_assessment is not None

    recurrence = (
        calculate_asset_operational_range_recurrence(
            prices=prices,
            range_assessment=(
                range_assessment
            ),
        )
    )

    assert recurrence is not None

    assert (
        recurrence.lower_limit_touches
        == 1
    )

    assert (
        recurrence.upper_limit_touches
        == 1
    )