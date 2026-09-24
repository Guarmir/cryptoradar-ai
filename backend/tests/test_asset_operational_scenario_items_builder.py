from app.ai.asset_operational_scenario_assessment import (
    AssetOperationalScenarioAssessment,
)
from app.ai.asset_operational_scenario_items_builder import (
    build_asset_operational_scenario_items,
)


def test_builds_scenario_item():
    assessment = (
        AssetOperationalScenarioAssessment(
            state="bullish",
            strength="strong",
            directional_score=6,
            supporting_factors=(),
            warning_factors=(),
        )
    )

    items = (
        build_asset_operational_scenario_items(
            name="Uniswap",
            assessment=assessment,
        )
    )

    item_by_key = {
        item.key: item
        for item in items
    }

    content = (
        item_by_key[
            "asset_operational_scenario"
        ].content
    )

    assert "Uniswap" in content
    assert "viés de alta" in content
    assert "confirmação forte" in content
    assert "+6" in content
    assert (
        "recomendação de compra ou venda"
        in content
    )


def test_maps_supporting_factors():
    assessment = (
        AssetOperationalScenarioAssessment(
            state="bullish",
            strength="moderate",
            directional_score=4,
            supporting_factors=(
                "market_context_favorable",
                "outperforming_btc",
                "range_quality_strong",
            ),
            warning_factors=(),
        )
    )

    items = (
        build_asset_operational_scenario_items(
            name="Uniswap",
            assessment=assessment,
        )
    )

    support = next(
        item
        for item in items
        if (
            item.key
            == "asset_operational_scenario_support"
        )
    )

    assert (
        "contexto externo de mercado favorável"
        in support.content
    )

    assert (
        "desempenho superior ao BTC"
        in support.content
    )

    assert (
        "faixa operacional com qualidade forte"
        in support.content
    )


def test_maps_warning_factors():
    assessment = (
        AssetOperationalScenarioAssessment(
            state="bearish",
            strength="weak",
            directional_score=-4,
            supporting_factors=(),
            warning_factors=(
                "market_context_unfavorable",
                "observed_risk_high",
                "range_invalidated",
            ),
        )
    )

    items = (
        build_asset_operational_scenario_items(
            name="Uniswap",
            assessment=assessment,
        )
    )

    warning = next(
        item
        for item in items
        if (
            item.key
            == "asset_operational_scenario_warnings"
        )
    )

    assert (
        "contexto externo de mercado desfavorável"
        in warning.content
    )

    assert (
        "Risk Score observado em nível alto"
        in warning.content
    )

    assert (
        "faixa operacional observada invalidada"
        in warning.content
    )


def test_conflicted_scenario_is_explained():
    assessment = (
        AssetOperationalScenarioAssessment(
            state="conflicted",
            strength="weak",
            directional_score=0,
            supporting_factors=(
                "score_supports_upside",
            ),
            warning_factors=(
                "market_context_unfavorable",
            ),
        )
    )

    items = (
        build_asset_operational_scenario_items(
            name="Uniswap",
            assessment=assessment,
        )
    )

    scenario = next(
        item
        for item in items
        if (
            item.key
            == "asset_operational_scenario"
        )
    )

    assert (
        "cenário conflitante"
        in scenario.content
    )

    assert (
        "confirmação fraca"
        in scenario.content
    )