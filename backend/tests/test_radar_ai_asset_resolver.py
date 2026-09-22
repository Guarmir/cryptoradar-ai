import pytest

from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)


@pytest.mark.parametrize(
    (
        "question",
        "expected",
    ),
    [
        (
            "Analise o Bitcoin",
            "bitcoin",
        ),
        (
            "Como está BTC agora?",
            "bitcoin",
        ),
        (
            "O que está acontecendo com ETH?",
            "ethereum",
        ),
        (
            "Como está a UNI?",
            "uniswap",
        ),
        (
            "Analise Solana para mim",
            "solana",
        ),
    ],
)
def test_resolves_asset_from_question(
    question: str,
    expected: str,
) -> None:
    resolver = RadarAIAssetResolver()

    assert resolver.resolve(
        question
    ) == expected


def test_returns_none_when_asset_is_not_found() -> None:
    resolver = RadarAIAssetResolver()

    assert resolver.resolve(
        "Como está o mercado hoje?"
    ) is None


def test_rejects_empty_question() -> None:
    resolver = RadarAIAssetResolver()

    with pytest.raises(
        ValueError,
        match="question must not be empty",
    ):
        resolver.resolve("   ")