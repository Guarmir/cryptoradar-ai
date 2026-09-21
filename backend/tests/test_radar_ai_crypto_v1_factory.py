from app.ai.radar_ai_crypto_v1_factory import (
    RadarAICryptoV1Factory,
)


def test_crypto_v1_uses_real_resolvers() -> None:
    provider = object()
    received = {}

    def provider_resolver(
        intent: str,
        market: str,
    ):
        received["intent"] = intent
        received["market"] = market
        return provider

    def build_market_overview_context(
        question: str,
        selected_provider,
    ):
        received["question"] = question
        received["provider"] = selected_provider

        return {
            "status": "ready",
        }

    orchestrator = RadarAICryptoV1Factory.create(
        provider_resolver=provider_resolver,
        build_market_overview_context=(
            build_market_overview_context
        ),
    )

    result = orchestrator.orchestrate(
        "Como está o mercado cripto agora?"
    )

    assert result.intent == "market_overview"
    assert result.market == "crypto"
    assert result.provider is provider
    assert result.context == {
        "status": "ready",
    }

    assert received == {
        "intent": "market_overview",
        "market": "crypto",
        "question": (
            "Como está o mercado cripto agora?"
        ),
        "provider": provider,
    }


def test_crypto_v1_defaults_to_crypto_market() -> None:
    provider = object()
    received = {}

    def provider_resolver(
        intent: str,
        market: str,
    ):
        received["intent"] = intent
        received["market"] = market
        return provider

    def build_market_overview_context(
        question: str,
        selected_provider,
    ):
        return {
            "question": question,
        }

    orchestrator = RadarAICryptoV1Factory.create(
        provider_resolver=provider_resolver,
        build_market_overview_context=(
            build_market_overview_context
        ),
    )

    result = orchestrator.orchestrate(
        "Como está o mercado agora?"
    )

    assert result.intent == "market_overview"
    assert result.market == "crypto"

    assert received == {
        "intent": "market_overview",
        "market": "crypto",
    }