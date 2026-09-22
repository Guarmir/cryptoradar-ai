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
def test_resolves_known_asset_from_question(
    question: str,
    expected: str,
) -> None:
    calls = []

    resolver = RadarAIAssetResolver(
        dynamic_coin_resolver=(
            lambda candidate: (
                calls.append(candidate)
                or None
            )
        ),
    )

    assert resolver.resolve(
        question
    ) == expected

    assert calls == []


@pytest.mark.parametrize(
    (
        "question",
        "candidate",
        "resolved_id",
    ),
    [
        (
            "Analise AAVE",
            "aave",
            "aave",
        ),
        (
            "Como está Render?",
            "render",
            "render-token",
        ),
        (
            "Qual o preço da SUI?",
            "sui",
            "sui",
        ),
        (
            "Como está PIPPIN?",
            "pippin",
            "pippin",
        ),
    ],
)
def test_resolves_dynamic_asset(
    question: str,
    candidate: str,
    resolved_id: str,
) -> None:
    received = []

    def dynamic_coin_resolver(
        value: str,
    ):
        received.append(value)

        if value == candidate:
            return resolved_id

        return None

    resolver = RadarAIAssetResolver(
        dynamic_coin_resolver=(
            dynamic_coin_resolver
        ),
    )

    assert resolver.resolve(
        question
    ) == resolved_id

    assert candidate in received


def test_returns_none_when_dynamic_asset_is_not_found() -> None:
    resolver = RadarAIAssetResolver(
        dynamic_coin_resolver=(
            lambda candidate: None
        ),
    )

    assert resolver.resolve(
        "Quero informações gerais."
    ) is None


def test_rejects_empty_question() -> None:
    resolver = RadarAIAssetResolver()

    with pytest.raises(
        ValueError,
        match="question must not be empty",
    ):
        resolver.resolve("   ")