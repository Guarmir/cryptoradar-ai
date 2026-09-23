import pytest

from app.ai.asset_operational_range_assessment import (
    calculate_asset_operational_range,
)


def test_calculates_operational_range_metrics() -> None:
    assessment = (
        calculate_asset_operational_range(
            current_price=101.0,
            prices=(
                100.0,
                103.0,
                105.0,
                102.0,
            ),
        )
    )

    assert assessment is not None

    assert assessment.lower_limit == 100.0
    assert assessment.upper_limit == 105.0

    assert assessment.amplitude_percent == (
        pytest.approx(5.0)
    )

    assert assessment.position_percent == (
        pytest.approx(20.0)
    )

    assert (
        assessment
        .distance_to_lower_percent
        == pytest.approx(
            0.990099,
            rel=1e-5,
        )
    )

    assert (
        assessment
        .distance_to_upper_percent
        == pytest.approx(
            3.960396,
            rel=1e-5,
        )
    )

    assert (
        assessment.observed_points_count
        == 4
    )

    assert (
        assessment.is_operational_amplitude
        is True
    )


def test_detects_range_outside_operational_amplitude() -> None:
    assessment = (
        calculate_asset_operational_range(
            current_price=102.0,
            prices=(
                100.0,
                101.0,
                102.0,
            ),
        )
    )

    assert assessment is not None

    assert assessment.amplitude_percent == (
        pytest.approx(2.0)
    )

    assert (
        assessment.is_operational_amplitude
        is False
    )


def test_position_can_show_price_above_range() -> None:
    assessment = (
        calculate_asset_operational_range(
            current_price=106.0,
            prices=(
                100.0,
                103.0,
                105.0,
            ),
        )
    )

    assert assessment is not None

    assert (
        assessment.position_percent
        > 100.0
    )

    assert (
        assessment
        .distance_to_upper_percent
        < 0
    )


def test_returns_none_with_insufficient_history() -> None:
    assessment = (
        calculate_asset_operational_range(
            current_price=100.0,
            prices=(100.0,),
        )
    )

    assert assessment is None


def test_ignores_invalid_prices() -> None:
    assessment = (
        calculate_asset_operational_range(
            current_price=101.0,
            prices=(
                100.0,
                None,
                105.0,
                -1.0,
                float("nan"),
            ),
        )
    )

    assert assessment is not None

    assert (
        assessment.observed_points_count
        == 2
    )

    assert assessment.lower_limit == 100.0
    assert assessment.upper_limit == 105.0