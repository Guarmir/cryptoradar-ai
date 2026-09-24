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


class FakeAssetProvider:
    def fetch(
        self,
        asset_id: str,
    ) -> dict:
        assert asset_id == "uniswap"

        return {
            "symbol": "uni",
            "name": "Uniswap",
            "current_price": 12.0,
            "market_cap": 7_000_000_000.0,
            "total_volume": 700_000_000.0,
            "price_change_percentage_24h": 3.0,
        }


class FakeAssetResolver:
    def resolve(
        self,
        question: str,
    ) -> str:
        return "uniswap"


class FakeMarketOverviewProvider:
    def fetch(
        self,
    ) -> MarketOverviewSnapshot:
        return MarketOverviewSnapshot(
            total_market_cap_usd=(
                3_000_000_000_000.0
            ),
            total_volume_24h_usd=(
                150_000_000_000.0
            ),
            market_cap_change_24h_percent=(
                1.20
            ),
            btc_dominance_percent=57.50,
            eth_dominance_percent=12.0,
            assets=(
                _asset("BTC", 1.40),
                _asset("ETH", 2.00),
                _asset("SOL", 3.00),
                _asset("XRP", 0.80),
            ),
        )


class FailingMarketOverviewProvider:
    def fetch(
        self,
    ) -> MarketOverviewSnapshot:
        raise RuntimeError(
            "market overview unavailable"
        )


def _asset(
    symbol: str,
    change: float | None,
) -> MarketOverviewAsset:
    return MarketOverviewAsset(
        symbol=symbol,
        name=symbol,
        price_usd=100.0,
        change_24h_percent=change,
        market_cap_usd=1_000_000_000.0,
        volume_24h_usd=100_000_000.0,
    )


def _service(
    market_overview_provider,
) -> RadarAIAssetContextService:
    return RadarAIAssetContextService(
        provider=FakeAssetProvider(),
        asset_resolver=FakeAssetResolver(),
        market_overview_provider=(
            market_overview_provider
        ),
    )


def test_overview_adds_market_context_items():
    context = _service(
        FakeMarketOverviewProvider()
    ).build_context(
        "analise UNI"
    )

    item_by_key = {
        item.key: item
        for item in context.items
    }

    assert "asset_market_context" in item_by_key
    assert "asset_market_btc" in item_by_key
    assert "asset_market_breadth" in item_by_key
    assert "asset_relative_strength" in item_by_key

    assert (
        "favorável"
        in item_by_key[
            "asset_market_context"
        ].content
    )

    assert (
        "+1.60"
        in item_by_key[
            "asset_relative_strength"
        ].content
    )


def test_overview_answer_exposes_market_context():
    question = "analise UNI"

    context = _service(
        FakeMarketOverviewProvider()
    ).build_context(
        question
    )

    answer = RadarAIAnswerComposer().compose(
        context,
        question,
    )

    assert (
        "contexto externo observado"
        in answer.lower()
    )

    assert (
        "desempenho relativo superior"
        in answer.lower()
    )


def test_signal_answer_uses_market_context():
    question = "qual o sinal da UNI?"

    context = _service(
        FakeMarketOverviewProvider()
    ).build_context(
        question
    )

    answer = RadarAIAnswerComposer().compose(
        context,
        question,
    )

    assert "sinal atual" in answer.lower()

    assert (
        "contexto externo observado"
        in answer.lower()
    )

    assert "btc" in answer.lower()


def test_market_overview_failure_does_not_break_asset_analysis():
    context = _service(
        FailingMarketOverviewProvider()
    ).build_context(
        "analise UNI"
    )

    item_by_key = {
        item.key: item
        for item in context.items
    }

    assert "asset_summary" in item_by_key
    assert "asset_market_context" in item_by_key

    assert (
        "indisponível"
        in item_by_key[
            "asset_market_context"
        ].content
    )
