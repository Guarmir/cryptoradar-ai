from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)
from app.ai.radar_ai_answer_composer import (
    RadarAIAnswerComposer,
)
from app.ai.radar_ai_asset_context_service import (
    RadarAIAssetContextService,
)


class FakeBTCAssetProvider:
    def fetch(
        self,
        asset_id: str,
    ):
        assert asset_id == "bitcoin"

        return {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 100_000.0,
            "market_cap": 2_000_000_000_000,
            "total_volume": 60_000_000_000,
            "price_change_percentage_24h": 2.0,
        }


class FakeBTCResolver:
    def resolve(
        self,
        question: str,
    ):
        return "bitcoin"


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
            market_cap_change_24h_percent=(
                1.5
            ),
            btc_dominance_percent=58.0,
            eth_dominance_percent=12.0,
            assets=(
                MarketOverviewAsset(
                    symbol="BTC",
                    name="Bitcoin",
                    price_usd=100_000.0,
                    change_24h_percent=2.0,
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
                    change_24h_percent=1.0,
                    market_cap_usd=(
                        480_000_000_000
                    ),
                    volume_24h_usd=(
                        25_000_000_000
                    ),
                ),
            ),
            observed_at=None,
        )


def test_btc_does_not_compare_against_itself():
    question = "analise BTC"

    service = RadarAIAssetContextService(
        provider=FakeBTCAssetProvider(),
        asset_resolver=FakeBTCResolver(),
        market_overview_provider=(
            FakeMarketOverviewProvider()
        ),
    )

    context = service.build_context(
        question
    )

    keys = {
        item.key
        for item in context.items
    }

    assert (
        "asset_market_context"
        in keys
    )
    assert (
        "asset_market_btc"
        in keys
    )
    assert (
        "asset_market_breadth"
        in keys
    )

    assert (
        "asset_relative_strength"
        not in keys
    )

    answer = (
        RadarAIAnswerComposer()
        .compose(
            context,
            question,
        )
    )

    assert (
        "ponto(s) percentual(is) "
        "em relação ao BTC"
        not in answer
    )