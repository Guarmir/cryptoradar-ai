from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.radar_ai_asset_comparison_context_service import (
    RadarAIAssetComparisonContextService,
)
from app.ai.radar_ai_asset_comparison_resolver import (
    RadarAIAssetComparisonResolver,
)


def test_builds_context_for_two_assets() -> None:
    markets = {
        "uniswap": {
            "id": "uniswap",
            "symbol": "uni",
            "name": "Uniswap",
            "current_price": 12.50,
            "market_cap": 7_500_000_000,
            "total_volume": 650_000_000,
            "price_change_percentage_24h": 4.2,
        },
        "solana": {
            "id": "solana",
            "symbol": "sol",
            "name": "Solana",
            "current_price": 180.0,
            "market_cap": 85_000_000_000,
            "total_volume": 4_500_000_000,
            "price_change_percentage_24h": 2.1,
        },
    }

    received = []

    class FakeProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            received.append(asset_id)
            return markets[asset_id]

    resolver = (
        RadarAIAssetComparisonResolver(
            dynamic_coin_resolver=(
                lambda candidate: None
            ),
        )
    )

    service = (
        RadarAIAssetComparisonContextService(
            provider=FakeProvider(),
            comparison_resolver=resolver,
        )
    )

    context = service.build_context(
        "Compare UNI e SOL"
    )

    assert context.is_supported

    assert context.intent == (
        AssistantIntent.ASSET_COMPARISON
    )

    assert context.source == (
        "cryptoradar_asset_comparison"
    )

    assert context.source_version == "v1"

    assert received == [
        "uniswap",
        "solana",
    ]

    items = {
        item.key: item.content
        for item in context.items
    }

    assert (
        items[
            "comparison_asset_1_identity"
        ]
        == "Uniswap (UNI)"
    )

    assert (
        items[
            "comparison_asset_2_identity"
        ]
        == "Solana (SOL)"
    )

    assert "12.50000000" in (
        items[
            "comparison_asset_1_price"
        ]
    )

    assert "180.00000000" in (
        items[
            "comparison_asset_2_price"
        ]
    )

    assert "/100" in (
        items[
            "comparison_asset_1_score"
        ]
    )

    assert "/100" in (
        items[
            "comparison_asset_2_score"
        ]
    )