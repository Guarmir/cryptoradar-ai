from datetime import (
    datetime,
    timezone,
)

from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)
from app.ai.radar_ai_asset_context_service import (
    RadarAIAssetContextService,
)


class FakeAssetResolver:
    def resolve(
        self,
        question: str,
    ):
        return "uniswap"


class FakeAssetProvider:
    def fetch(
        self,
        asset_id: str,
    ):
        assert asset_id == "uniswap"

        return {
            "id": "uniswap",
            "symbol": "uni",
            "name": "Uniswap",
            "current_price": 12.50,
            "market_cap": 7_500_000_000,
            "total_volume": 650_000_000,
            "price_change_percentage_24h": 4.2,
        }


class FakeMarketOverviewProvider:
    def fetch(
        self,
    ) -> MarketOverviewSnapshot:
        return MarketOverviewSnapshot(
            total_market_cap_usd=(
                3_500_000_000_000
            ),
            total_volume_24h_usd=(
                150_000_000_000
            ),
            market_cap_change_24h_percent=1.5,
            btc_dominance_percent=58.0,
            eth_dominance_percent=12.0,
            assets=(
                MarketOverviewAsset(
                    symbol="BTC",
                    name="Bitcoin",
                    price_usd=100_000.0,
                    change_24h_percent=2.6,
                    market_cap_usd=(
                        2_000_000_000_000
                    ),
                    volume_24h_usd=(
                        60_000_000_000
                    ),
                ),
                MarketOverviewAsset(
                    symbol="ETH",
                    name="Ethereum",
                    price_usd=4_000.0,
                    change_24h_percent=1.2,
                    market_cap_usd=(
                        480_000_000_000
                    ),
                    volume_24h_usd=(
                        25_000_000_000
                    ),
                ),
                MarketOverviewAsset(
                    symbol="SOL",
                    name="Solana",
                    price_usd=250.0,
                    change_24h_percent=3.0,
                    market_cap_usd=(
                        120_000_000_000
                    ),
                    volume_24h_usd=(
                        8_000_000_000
                    ),
                ),
            ),
            observed_at=datetime.now(
                timezone.utc
            ),
        )


def test_asset_overview_builds_operational_scenario():
    service = RadarAIAssetContextService(
        provider=FakeAssetProvider(),
        asset_resolver=FakeAssetResolver(),
        market_overview_provider=(
            FakeMarketOverviewProvider()
        ),
    )

    context = service.build_context(
        "Como está a UNI?"
    )

    item_by_key = {
        item.key: item
        for item in context.items
    }

    assert (
        "asset_operational_scenario"
        in item_by_key
    )

    assert (
        "asset_operational_scenario_support"
        in item_by_key
    )

    assert (
        "asset_operational_scenario_warnings"
        in item_by_key
    )

    scenario = item_by_key[
        "asset_operational_scenario"
    ].content

    assert "Uniswap" in scenario
    assert "viés de alta" in scenario
    assert "+5" in scenario

    support = item_by_key[
        "asset_operational_scenario_support"
    ].content

    assert (
        "contexto externo de mercado favorável"
        in support
    )

    assert (
        "desempenho superior ao BTC"
        in support
    )