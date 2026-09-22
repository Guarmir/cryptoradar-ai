import pytest

from app.ai.radar_ai_asset_focus_resolver import (
    RadarAIAssetFocusResolver,
)


@pytest.mark.parametrize(
    (
        "question",
        "expected",
    ),
    [
        (
            "Como está a UNI?",
            "overview",
        ),
        (
            "Qual o score da UNI?",
            "score",
        ),
        (
            "Qual o sinal do BTC?",
            "signal",
        ),
        (
            "Quais os riscos do Ethereum?",
            "risk",
        ),
        (
            "Qual o preço do ETH?",
            "price",
        ),
        (
            "Quanto a SOL variou hoje?",
            "change",
        ),
        (
            "Qual o volume da UNI?",
            "volume",
        ),
        (
            "O que invalida esse cenário do BTC?",
            "invalidation",
        ),
    ],
)
def test_resolves_asset_focus(
    question: str,
    expected: str,
) -> None:
    resolver = RadarAIAssetFocusResolver()

    assert resolver.resolve(
        question
    ) == expected


def test_rejects_empty_question() -> None:
    resolver = RadarAIAssetFocusResolver()

    with pytest.raises(
        ValueError,
        match="question must not be empty",
    ):
        resolver.resolve("   ")