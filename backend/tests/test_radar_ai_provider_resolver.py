import pytest

from app.ai.radar_ai_provider_resolver import (
    RadarAIProviderResolver,
)


def test_resolves_crypto_market_overview_provider() -> None:
    provider = object()

    resolver = RadarAIProviderResolver(
        crypto_market_overview_provider=provider,
    )

    result = resolver.resolve(
        "market_overview",
        "crypto",
    )

    assert result is provider


def test_resolver_can_be_called_directly() -> None:
    provider = object()

    resolver = RadarAIProviderResolver(
        crypto_market_overview_provider=provider,
    )

    result = resolver(
        "market_overview",
        "crypto",
    )

    assert result is provider


@pytest.mark.parametrize(
    (
        "intent",
        "market",
    ),
    [
        (
            "asset_analysis",
            "crypto",
        ),
        (
            "market_overview",
            "stocks",
        ),
        (
            "unknown",
            "crypto",
        ),
    ],
)
def test_rejects_unsupported_routes(
    intent: str,
    market: str,
) -> None:
    resolver = RadarAIProviderResolver(
        crypto_market_overview_provider=object(),
    )

    with pytest.raises(
        ValueError,
        match="unsupported Radar AI provider route",
    ):
        resolver.resolve(
            intent,
            market,
        )