from types import SimpleNamespace
from unittest.mock import patch

from app.ai.asset_market_context_items_builder import (
    build_asset_market_context_items,
    build_asset_market_context_unavailable_item,
)


def _assessment(**changes):
    values = {
        "state": "favorable",
        "btc_change_24h_percent": 2.5,
        "btc_dominance_percent": 54.3,
        "market_cap_change_24h_percent": 1.2,
        "advancing_asset_count": 12,
        "declining_asset_count": 5,
        "unchanged_asset_count": 3,
        "breadth_state": "positive",
        "relative_change_vs_btc_pp": -1.0,
        "relative_strength_state": "underperforming",
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_context_items_keep_keys_and_market_numbers():
    with patch(
        "app.ai.asset_market_context_items_builder.calculate_asset_market_context",
        return_value=_assessment(),
    ):
        items = build_asset_market_context_items(
            name="Bitcoin",
            asset_change_24h_percent=1.5,
            snapshot=object(),
        )

    assert [item.key for item in items] == [
        "asset_market_context", "asset_market_btc",
        "asset_market_breadth", "asset_relative_strength",
    ]
    assert items[0].title == "Cenário geral do mercado"
    assert "favorável" in items[0].content
    assert "+2.50%" in items[1].content
    assert "54.30%" in items[1].content
    assert "+1.20%" in items[2].content
    assert "12" in items[2].content
    assert "-1.00" in items[3].content
    assert "regras V1" not in items[3].content


def test_unavailable_market_information_is_explained():
    item = build_asset_market_context_unavailable_item(name="ETH")
    assert item.key == "asset_market_context"
    assert "indisponíveis" in item.content
    assert "ETH" in item.content


def test_missing_btc_variation_does_not_invent_comparison():
    with patch(
        "app.ai.asset_market_context_items_builder.calculate_asset_market_context",
        return_value=_assessment(
            btc_change_24h_percent=None,
            relative_change_vs_btc_pp=None,
        ),
    ):
        items = build_asset_market_context_items(
            name="ETH", asset_change_24h_percent=1.0, snapshot=object()
        )
    assert "não está disponível" in items[1].content
    assert "Não foi possível comparar" in items[3].content
