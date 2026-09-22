import pytest

from app.ai.radar_ai_intent_resolver import (
    RadarAIIntentResolver,
)


@pytest.mark.parametrize(
    "question",
    [
        "Como está o mercado agora?",
        "Qual o panorama do mercado?",
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


@pytest.mark.parametrize(
    "question",
    [
        "Analise o Bitcoin para mim.",
        "Como está BTC?",
        "Como está a UNI?",
        "O que está acontecendo com ETH?",
    ],
)
def test_resolves_asset_analysis(
    question: str,
) -> None:
    resolver = RadarAIIntentResolver()

    assert resolver.resolve(
        question
    ) == "asset_analysis"


def test_unknown_question_returns_unknown() -> None:
    resolver = RadarAIIntentResolver()

    assert resolver.resolve(
        "Quero informações gerais."
    ) == "unknown"


def test_empty_question_is_rejected() -> None:
    resolver = RadarAIIntentResolver()

    with pytest.raises(
        ValueError,
        match="question must not be empty",
    ):
        resolver.resolve("   ")