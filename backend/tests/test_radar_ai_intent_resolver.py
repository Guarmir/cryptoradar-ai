import pytest

from app.ai.radar_ai_intent_resolver import (
    RadarAIIntentResolver,
)


@pytest.mark.parametrize(
    "question",
    [
        "Como está o mercado agora?",
        "Qual o panorama do mercado?",
        "Me dê uma visão geral do mercado.",
        "Como anda o market hoje?",
        "Qual o cenário atual?",
    ],
)
def test_resolves_market_overview(
    question: str,
) -> None:
    resolver = RadarAIIntentResolver()

    assert resolver.resolve(
        question
    ) == "market_overview"


def test_unknown_question_returns_unknown() -> None:
    resolver = RadarAIIntentResolver()

    assert resolver.resolve(
        "Analise o Bitcoin para mim."
    ) == "unknown"


def test_resolver_can_be_called_directly() -> None:
    resolver = RadarAIIntentResolver()

    assert resolver(
        "Como está o mercado?"
    ) == "market_overview"


def test_empty_question_is_rejected() -> None:
    resolver = RadarAIIntentResolver()

    with pytest.raises(
        ValueError,
        match="question must not be empty",
    ):
        resolver.resolve("   ")