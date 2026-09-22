import pytest

from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)
from app.ai.radar_ai_crypto_v1_application_factory import (
    RadarAICryptoV1ApplicationFactory,
)


@pytest.mark.parametrize(
    (
        "question",
        "candidate",
        "asset_id",
        "symbol",
        "name",
    ),
    [
        (
            "Analise AAVE",
            "aave",
            "aave",
            "aave",
            "Aave",
        ),
        (
            "Como está Render?",
            "render",
            "render-token",
            "render",
            "Render",
        ),
        (
            "Qual o preço da SUI?",
            "sui",
            "sui",
            "sui",
            "Sui",
        ),
        (
            "Como está PIPPIN?",
            "pippin",
            "pippin",
            "pippin",
            "Pippin",
        ),
    ],
)
def test_dynamic_asset_runs_through_application(
    question: str,
    candidate: str,
    asset_id: str,
    symbol: str,
    name: str,
) -> None:
    resolver_calls = []
    provider_calls = []

    def dynamic_coin_resolver(
        value: str,
    ):
        resolver_calls.append(
            value
        )

        if value == candidate:
            return asset_id

        return None

    asset_resolver = (
        RadarAIAssetResolver(
            dynamic_coin_resolver=(
                dynamic_coin_resolver
            ),
        )
    )

    class FakeAssetProvider:
        def fetch(
            self,
            received_asset_id: str,
        ):
            provider_calls.append(
                received_asset_id
            )

            return {
                "id": asset_id,
                "symbol": symbol,
                "name": name,
                "current_price": 10.0,
                "market_cap": 1_500_000_000,
                "total_volume": 250_000_000,
                "price_change_percentage_24h": 2.5,
            }

    asset_provider = FakeAssetProvider()

    orchestrator = (
        RadarAICryptoV1ApplicationFactory.create(
            crypto_market_overview_provider=(
                object()
            ),
            crypto_asset_analysis_provider=(
                asset_provider
            ),
            asset_resolver=(
                asset_resolver
            ),
        )
    )

    result = orchestrator.orchestrate(
        question
    )

    assert result.intent == (
        "asset_analysis"
    )

    assert result.market == "crypto"

    assert result.provider is (
        asset_provider
    )

    assert result.context.is_supported

    assert result.context.source == (
        "cryptoradar_asset_analysis"
    )

    assert provider_calls == [
        asset_id,
    ]

    # O mesmo resolver é usado novamente
    # pelo contexto, mas a pergunta já
    # está em cache.
    assert resolver_calls.count(
        candidate
    ) == 1