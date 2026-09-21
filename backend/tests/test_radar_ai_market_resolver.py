import pytest

from app.ai.radar_ai_market_resolver import (
    RadarAIMarketResolver,
)


@pytest.mark.parametrize(
    "question",
    [
        "Como está o mercado cripto agora?",
        "Qual o cenário do crypto hoje?",
        "Como está o Bitcoin?",
        "Analise BTC para mim.",
        "Como anda o Ethereum?",
        "O que está acontecendo com ETH?",
        "Como estão as altcoins?",
        "Quero analisar uma criptomoeda.",
    ],
)
def test_resolves_crypto_market(
    question: str,
) -> None:
    resolver = RadarAIMarketResolver()

    assert resolver.resolve(
        question
    ) == "crypto"


def test_unknown_market_returns_unknown() -> None:
    resolver = RadarAIMarketResolver()

    assert resolver.resolve(
        "Como está o mercado hoje?"
    ) == "unknown"


def test_resolver_can_be_called_directly() -> None:
    resolver = RadarAIMarketResolver()

    assert resolver(
        "Como está o Bitcoin?"
    ) == "crypto"


def test_empty_question_is_rejected() -> None:
    resolver = RadarAIMarketResolver()

    with pytest.raises(
        ValueError,
        match="question must not be empty",
    ):
        resolver.resolve("   ")