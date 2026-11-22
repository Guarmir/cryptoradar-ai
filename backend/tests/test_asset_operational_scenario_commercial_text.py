from types import SimpleNamespace

from app.ai.asset_operational_scenario_items_builder import (
    build_asset_operational_scenario_items,
)


def _assessment(**changes):
    values = {
        "state": "bearish",
        "strength": "moderate",
        "directional_score": -6,
        "supporting_factors": ("score_supports_downside", "market_context_favorable"),
        "warning_factors": ("range_quality_weak", "observed_risk_elevated"),
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_scenario_preserves_direction_score_and_keys():
    items = build_asset_operational_scenario_items(
        name="ETH", assessment=_assessment()
    )
    assert [item.key for item in items] == [
        "asset_operational_scenario",
        "asset_operational_scenario_support",
        "asset_operational_scenario_warnings",
    ]
    assert "viés de baixa" in items[0].content
    assert "confirmação moderada" in items[0].content
    assert "-6" in items[0].content
    assert "V1" not in items[0].content
    assert "pontuação favorece a baixa" in items[1].content
    assert "confirmação fraca" in items[2].content
    assert "risco estimado" in items[2].content


def test_empty_factors_keep_explanatory_messages():
    items = build_asset_operational_scenario_items(
        name="BTC",
        assessment=_assessment(supporting_factors=(), warning_factors=()),
    )
    assert "Não foram identificados fatores" in items[1].content
    assert "Não foram identificados alertas" in items[2].content
