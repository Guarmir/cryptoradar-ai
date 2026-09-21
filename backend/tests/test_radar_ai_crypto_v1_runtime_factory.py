from app.ai.radar_ai_crypto_v1_runtime_factory import (
    RadarAICryptoV1RuntimeFactory,
)


def test_runtime_factory_wires_real_provider_resolver() -> None:
    provider = object()
    received = {}

    def build_market_overview_context(
        question: str,
        selected_provider,
    ):
        received["question"] = question
        received["provider"] = selected_provider

        return {
            "status": "ready",
        }

    orchestrator = RadarAICryptoV1RuntimeFactory.create(
        crypto_market_overview_provider=provider,
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
        "question": (
            "Como está o mercado cripto agora?"
        ),
        "provider": provider,
    }


def test_runtime_factory_uses_crypto_default_market() -> None:
    provider = object()

    orchestrator = RadarAICryptoV1RuntimeFactory.create(
        crypto_market_overview_provider=provider,
        build_market_overview_context=(
            lambda question, selected_provider: {
                "question": question,
            }
        ),
    )

    result = orchestrator.orchestrate(
        "Como está o mercado agora?"
    )

    assert result.intent == "market_overview"
    assert result.market == "crypto"
    assert result.provider is provider