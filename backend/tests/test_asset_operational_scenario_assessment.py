import pytest

from app.ai.asset_operational_scenario_assessment import (
    calculate_asset_operational_scenario,
)


def test_builds_strong_bullish_scenario():
    assessment = (
        calculate_asset_operational_scenario(
            score=75,
            change_24h_percent=3.5,
            risk_score=25,
            range_quality_state="strong",
            range_invalidation_state="low",
            market_context_state="favorable",
            relative_strength_state=(
                "outperforming"
            ),
        )
    )

    assert assessment.state == "bullish"
    assert assessment.strength == "strong"
    assert assessment.directional_score == 6

    assert (
        "market_context_favorable"
        in assessment.supporting_factors
    )

    assert (
        "outperforming_btc"
        in assessment.supporting_factors
    )


def test_builds_strong_bearish_scenario():
    assessment = (
        calculate_asset_operational_scenario(
            score=25,
            change_24h_percent=-4.0,
            risk_score=30,
            range_quality_state="strong",
            range_invalidation_state="low",
            market_context_state=(
                "unfavorable"
            ),
            relative_strength_state=(
                "underperforming"
            ),
        )
    )

    assert assessment.state == "bearish"
    assert assessment.strength == "strong"
    assert assessment.directional_score == -6


def test_conflicting_evidence_is_not_forced():
    assessment = (
        calculate_asset_operational_scenario(
            score=72,
            change_24h_percent=-3.0,
            risk_score=45,
            range_quality_state=(
                "acceptable"
            ),
            range_invalidation_state=(
                "moderate"
            ),
            market_context_state=(
                "unfavorable"
            ),
            relative_strength_state=(
                "outperforming"
            ),
        )
    )

    assert (
        assessment.directional_score
        == 0
    )

    assert (
        assessment.state
        == "conflicted"
    )

    assert (
        assessment.strength
        == "weak"
    )


def test_neutral_when_direction_is_insufficient():
    assessment = (
        calculate_asset_operational_scenario(
            score=50,
            change_24h_percent=0.2,
            risk_score=45,
            market_context_state="mixed",
            relative_strength_state="aligned",
        )
    )

    assert assessment.state == "neutral"
    assert assessment.strength == "weak"
    assert assessment.directional_score == 0


def test_high_risk_and_fragile_range_reduce_strength():
    assessment = (
        calculate_asset_operational_scenario(
            score=75,
            change_24h_percent=4.0,
            risk_score=85,
            range_quality_state="weak",
            range_invalidation_state="high",
            market_context_state="favorable",
            relative_strength_state=(
                "outperforming"
            ),
        )
    )

    assert assessment.state == "bullish"

    assert assessment.strength == "weak"

    assert (
        "observed_risk_high"
        in assessment.warning_factors
    )

    assert (
        "range_invalidation_high"
        in assessment.warning_factors
    )


def test_invalidated_range_is_preserved_as_warning():
    assessment = (
        calculate_asset_operational_scenario(
            score=75,
            change_24h_percent=3.0,
            risk_score=45,
            range_quality_state="strong",
            range_invalidation_state=(
                "invalidated"
            ),
            market_context_state="favorable",
            relative_strength_state=(
                "outperforming"
            ),
        )
    )

    assert assessment.state == "bullish"

    assert (
        "range_invalidated"
        in assessment.warning_factors
    )

    assert assessment.strength == "moderate"


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("score", -1),
        ("score", 101),
        ("risk_score", -1),
        ("risk_score", 101),
    ),
)
def test_rejects_invalid_percent_scores(
    field,
    value,
):
    arguments = {
        "score": 50,
        "change_24h_percent": 0,
        "risk_score": 50,
    }

    arguments[field] = value

    with pytest.raises(
        ValueError
    ):
        calculate_asset_operational_scenario(
            **arguments
        )