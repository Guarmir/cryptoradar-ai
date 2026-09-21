import pytest

from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.market_domain import (
    MarketDomain,
)
from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)
from app.ai.radar_ai_market_overview_context_service_adapter import (
    RadarAIMarketOverviewContextServiceAdapter,
)


def _snapshot() -> MarketOverviewSnapshot:
    return MarketOverviewSnapshot(
        total_market_cap_usd=(
            2_500_000_000_000
        ),
        total_volume_24h_usd=(
            120_000_000_000
        ),
        market_cap_change_24h_percent=2.5,
        btc_dominance_percent=55.0,
        eth_dominance_percent=12.0,
        assets=(
            MarketOverviewAsset(
                symbol="btc",
                name="Bitcoin",
                price_usd=100_000,
                change_24h_percent=3.0,
                market_cap_usd=(
                    2_000_000_000_000
                ),
                volume_24h_usd=(
                    50_000_000_000
                ),
            ),
        ),
    )


def test_adapter_builds_context_with_real_service() -> None:
    class FakeProvider:
        def __init__(self) -> None:
            self.fetch_count = 0

        @property
        def domain(self):
            return MarketDomain.CRYPTO

        def fetch(self):
            self.fetch_count += 1
            return _snapshot()

    provider = FakeProvider()

    adapter = (
        RadarAIMarketOverviewContextServiceAdapter()
    )

    context = adapter(
        "Como está o mercado cripto?",
        provider,
    )

    assert context.is_supported

    assert context.intent == (
        AssistantIntent.MARKET_OVERVIEW
    )

    assert provider.fetch_count == 1


def test_adapter_rejects_empty_question() -> None:
    adapter = (
        RadarAIMarketOverviewContextServiceAdapter()
    )

    with pytest.raises(
        ValueError,
        match="question must not be empty",
    ):
        adapter(
            "   ",
            object(),
        )