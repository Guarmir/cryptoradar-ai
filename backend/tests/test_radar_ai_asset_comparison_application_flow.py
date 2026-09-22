from app.ai.radar_ai_asset_comparison_resolver import (
    RadarAIAssetComparisonResolver,
)
from app.ai.radar_ai_crypto_v1_application_factory import (
    RadarAICryptoV1ApplicationFactory,
)


def test_comparison_runs_through_application() -> None:
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
        "aave": {
            "id": "aave",
            "symbol": "aave",
            "name": "Aave",
            "current_price": 320.0,
            "market_cap": 4_800_000_000,
            "total_volume": 500_000_000,
            "price_change_percentage_24h": 1.7,
        },
    }

    calls = []

    class FakeAssetProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            calls.append(asset_id)
            return markets[asset_id]

    comparison_resolver = (
        RadarAIAssetComparisonResolver(
            dynamic_coin_resolver=(
                lambda candidate: (
                    "aave"
                    if candidate == "aave"
                    else None
                )
            ),
        )
    )

    provider = FakeAssetProvider()

    orchestrator = (
        RadarAICryptoV1ApplicationFactory.create(
            crypto_market_overview_provider=(
                object()
            ),
            crypto_asset_analysis_provider=(
                provider
            ),
            asset_comparison_resolver=(
                comparison_resolver
            ),
        )
    )

    result = orchestrator.orchestrate(
        "Compare UNI e AAVE"
    )

    assert result.intent == (
        "asset_comparison"
    )

    assert result.market == "crypto"

    assert result.provider is provider

    assert result.context.is_supported

    assert result.context.source == (
        "cryptoradar_asset_comparison"
    )

    assert calls == [
        "uniswap",
        "aave",
    ]