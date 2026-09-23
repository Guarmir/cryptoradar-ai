from app.ai.asset_risk_assessment import (
    calculate_asset_risk_assessment,
)


def test_large_liquid_asset_has_lower_risk_score() -> None:
    result = (
        calculate_asset_risk_assessment(
            change_24h=2.1,
            volume=4_500_000_000,
            market_cap=85_000_000_000,
        )
    )

    assert result.score == 26
    assert result.level == "moderado"

    assert (
        result.market_cap_component
        == 10
    )

    assert (
        result.liquidity_component
        == 40
    )

    assert (
        result.volatility_component
        == 30
    )


def test_smaller_more_volatile_asset_has_higher_risk() -> None:
    lower_risk = (
        calculate_asset_risk_assessment(
            change_24h=2.1,
            volume=4_500_000_000,
            market_cap=85_000_000_000,
        )
    )

    higher_risk = (
        calculate_asset_risk_assessment(
            change_24h=12.0,
            volume=25_000_000,
            market_cap=120_000_000,
        )
    )

    assert (
        higher_risk.score
        > lower_risk.score
    )


def test_negative_change_uses_absolute_volatility() -> None:
    positive = (
        calculate_asset_risk_assessment(
            change_24h=8.0,
            volume=500_000_000,
            market_cap=5_000_000_000,
        )
    )

    negative = (
        calculate_asset_risk_assessment(
            change_24h=-8.0,
            volume=500_000_000,
            market_cap=5_000_000_000,
        )
    )

    assert (
        positive.volatility_component
        == negative.volatility_component
    )

    assert (
        positive.score
        == negative.score
    )


def test_risk_assessment_contains_explanation() -> None:
    result = (
        calculate_asset_risk_assessment(
            change_24h=4.2,
            volume=650_000_000,
            market_cap=7_500_000_000,
        )
    )

    assert len(result.factors) == 3

    assert all(
        factor.strip()
        for factor in result.factors
    )