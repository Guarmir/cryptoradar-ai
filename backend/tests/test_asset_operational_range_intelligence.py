from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
)
from app.ai.asset_operational_range_intelligence_assessment import (
    calculate_asset_operational_range_context,
    calculate_asset_operational_range_invalidation,
    calculate_asset_operational_range_quality,
)
from app.ai.asset_operational_range_recurrence_assessment import (
    AssetOperationalRangeRecurrenceAssessment,
)


def _range(
    position: float = 50.0,
):
    return AssetOperationalRangeAssessment(
        current_price=102.5,
        lower_limit=100.0,
        upper_limit=105.0,
        amplitude_percent=5.0,
        position_percent=position,
        distance_to_lower_percent=2.44,
        distance_to_upper_percent=2.44,
        observed_points_count=11,
        is_operational_amplitude=True,
    )


def _organized_recurrence():
    return (
        AssetOperationalRangeRecurrenceAssessment(
            lower_limit_touches=3,
            upper_limit_touches=3,
            observed_points_count=11,
            total_limit_touches=6,
            completed_oscillations=3,
            has_both_limits_tested=True,
            has_minimum_recurrence=True,
            has_strong_recurrence=True,
            is_unbalanced=False,
            suggests_recurring_range=True,
            suggests_organized_oscillation=True,
            state="organized_oscillation",
        )
    )


def _minimum_recurrence():
    return (
        AssetOperationalRangeRecurrenceAssessment(
            lower_limit_touches=2,
            upper_limit_touches=2,
            observed_points_count=9,
            total_limit_touches=4,
            completed_oscillations=2,
            has_both_limits_tested=True,
            has_minimum_recurrence=True,
            has_strong_recurrence=False,
            is_unbalanced=False,
            suggests_recurring_range=True,
            suggests_organized_oscillation=False,
            state="recurring_range",
        )
    )


def test_strong_quality_with_market_support() -> None:
    quality = (
        calculate_asset_operational_range_quality(
            recurrence=(
                _organized_recurrence()
            ),
            current_volume=1_200_000_000,
            market_cap=10_000_000_000,
            historical_average_volume=(
                1_000_000_000
            ),
        )
    )

    assert quality.state == "strong"

    assert (
        quality.volume_confirmation_state
        == "confirmed"
    )

    assert (
        quality.liquidity_state
        == "strong"
    )


def test_quality_stays_under_observation_without_volume_history() -> None:
    quality = (
        calculate_asset_operational_range_quality(
            recurrence=(
                _minimum_recurrence()
            ),
            current_volume=600_000_000,
            market_cap=8_000_000_000,
            historical_average_volume=None,
        )
    )

    assert (
        quality.state
        == "under_observation"
    )

    assert (
        quality.volume_confirmation_state
        == "unavailable"
    )


def test_invalidation_detects_price_outside_range() -> None:
    quality = (
        calculate_asset_operational_range_quality(
            recurrence=(
                _organized_recurrence()
            ),
            current_volume=1_200_000_000,
            market_cap=10_000_000_000,
            historical_average_volume=(
                1_000_000_000
            ),
        )
    )

    invalidation = (
        calculate_asset_operational_range_invalidation(
            range_assessment=(
                _range(
                    position=105.0
                )
            ),
            quality=quality,
        )
    )

    assert invalidation.is_invalidated is True

    assert (
        invalidation.state
        == "invalidated"
    )


def test_strong_range_has_low_structural_invalidation_risk() -> None:
    quality = (
        calculate_asset_operational_range_quality(
            recurrence=(
                _organized_recurrence()
            ),
            current_volume=1_200_000_000,
            market_cap=10_000_000_000,
            historical_average_volume=(
                1_000_000_000
            ),
        )
    )

    invalidation = (
        calculate_asset_operational_range_invalidation(
            range_assessment=_range(),
            quality=quality,
        )
    )

    assert invalidation.is_invalidated is False
    assert invalidation.state == "low"


def test_consolidated_context_detects_organized_structure() -> None:
    range_assessment = _range()

    quality = (
        calculate_asset_operational_range_quality(
            recurrence=(
                _organized_recurrence()
            ),
            current_volume=1_200_000_000,
            market_cap=10_000_000_000,
            historical_average_volume=(
                1_000_000_000
            ),
        )
    )

    invalidation = (
        calculate_asset_operational_range_invalidation(
            range_assessment=(
                range_assessment
            ),
            quality=quality,
        )
    )

    context = (
        calculate_asset_operational_range_context(
            range_assessment=(
                range_assessment
            ),
            quality=quality,
            invalidation=invalidation,
        )
    )

    assert context.state == "organized"
    assert context.position_zone == "middle"


def test_consolidated_context_preserves_invalidation() -> None:
    range_assessment = _range(
        position=110.0
    )

    quality = (
        calculate_asset_operational_range_quality(
            recurrence=(
                _organized_recurrence()
            ),
            current_volume=1_200_000_000,
            market_cap=10_000_000_000,
            historical_average_volume=(
                1_000_000_000
            ),
        )
    )

    invalidation = (
        calculate_asset_operational_range_invalidation(
            range_assessment=(
                range_assessment
            ),
            quality=quality,
        )
    )

    context = (
        calculate_asset_operational_range_context(
            range_assessment=(
                range_assessment
            ),
            quality=quality,
            invalidation=invalidation,
        )
    )

    assert context.state == "invalidated"

    assert (
        context.position_zone
        == "above_range"
    )