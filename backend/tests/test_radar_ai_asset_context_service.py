import pytest

from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.crypto_asset_analysis_provider import (
    AssetAnalysisDataError,
    CryptoAssetAnalysisProvider,
)
from app.ai.market_domain import (
    MarketDomain,
)
from app.ai.radar_ai_asset_context_service import (
    RadarAIAssetContextService,
)


def _market() -> dict:
    return {
        "id": "uniswap",
        "symbol": "uni",
        "name": "Uniswap",
        "current_price": 12.50,
        "market_cap": 7_500_000_000,
        "total_volume": 650_000_000,
        "price_change_percentage_24h": 4.2,
    }


def test_assistant_intent_supports_asset_analysis() -> None:
    assert (
        AssistantIntent.ASSET_ANALYSIS.value
        == "asset_analysis"
    )


def test_asset_provider_fetches_market_data() -> None:
    received = {}

    def fetch_market_data(
        asset_id: str,
    ):
        received["asset_id"] = asset_id
        return _market()

    provider = CryptoAssetAnalysisProvider(
        fetch_market_data=(
            fetch_market_data
        ),
    )

    result = provider.fetch(
        "uniswap"
    )

    assert (
        provider.domain
        == MarketDomain.CRYPTO
    )

    assert result["symbol"] == "uni"

    assert received == {
        "asset_id": "uniswap",
    }


def test_asset_provider_rejects_missing_data() -> None:
    provider = CryptoAssetAnalysisProvider(
        fetch_market_data=(
            lambda asset_id: None
        ),
    )

    with pytest.raises(
        AssetAnalysisDataError,
        match=(
            "Dados do ativo indisponíveis"
        ),
    ):
        provider.fetch(
            "uniswap"
        )


def test_asset_context_is_built_from_question() -> None:
    received = {}

    class FakeProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            received["asset_id"] = asset_id
            return _market()

    service = RadarAIAssetContextService(
        provider=FakeProvider(),
    )

    context = service.build_context(
        "Como está a UNI?"
    )

    assert received == {
        "asset_id": "uniswap",
    }

    assert context.is_supported

    assert context.intent == (
        AssistantIntent.ASSET_ANALYSIS
    )

    assert context.source == (
        "cryptoradar_asset_analysis"
    )

    assert context.source_version == "v1"

    keys = [
        item.key
        for item in context.items
    ]

    assert keys == [
        "asset_summary",
        "asset_price",
        "asset_change",
        "asset_volume",
        "asset_market_cap",
        "asset_score",
        "asset_signal",
        "asset_reasons",
        "asset_risks",
        "asset_invalidation",
    ]


def test_asset_context_contains_specific_data_items() -> None:
    class FakeProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            return _market()

    service = RadarAIAssetContextService(
        provider=FakeProvider(),
    )

    context = service.build_context(
        "Como está a UNI?"
    )

    items = {
        item.key: item.content
        for item in context.items
    }

    assert "12.50000000" in (
        items["asset_price"]
    )

    assert "+4.20%" in (
        items["asset_change"]
    )

    assert "650,000,000" in (
        items["asset_volume"]
    )

    assert "/100" in (
        items["asset_score"]
    )

    assert (
        items["asset_signal"]
    )


def test_asset_context_rejects_question_without_asset() -> None:
    service = RadarAIAssetContextService(
        provider=object(),
    )

    with pytest.raises(
        ValueError,
        match="asset not found in question",
    ):
        service.build_context(
            "Quero informações gerais."
        )