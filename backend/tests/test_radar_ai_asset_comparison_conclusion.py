import pytest

from app.ai.assistant_context import (
    AssistantContext,
    AssistantContextItem,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.radar_ai_answer_composer import (
    RadarAIAnswerComposer,
)
from app.ai.radar_ai_asset_focus_resolver import (
    RadarAIAssetFocusResolver,
)


def _context() -> AssistantContext:
    return AssistantContext(
        intent=(
            AssistantIntent.ASSET_COMPARISON
        ),
        source=(
            "cryptoradar_asset_comparison"
        ),
        source_version="v1",
        items=(
            AssistantContextItem(
                key=(
                    "comparison_asset_1_identity"
                ),
                title="Ativo 1",
                content="Uniswap (UNI)",
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_price"
                ),
                title="Preço",
                content=(
                    "Uniswap: "
                    "US$ 12.50000000."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_change"
                ),
                title="Variação",
                content=(
                    "Uniswap: "
                    "+4.20% em 24h."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_volume"
                ),
                title="Volume",
                content=(
                    "Uniswap: "
                    "US$ 650,000,000 "
                    "de volume em 24h."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_market_cap"
                ),
                title="Capitalização",
                content=(
                    "Uniswap: "
                    "US$ 7,500,000,000 "
                    "de capitalização."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_score"
                ),
                title="Score",
                content=(
                    "Uniswap: score 77/100."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_risks"
                ),
                title="Riscos",
                content=(
                    "Risco de correção."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_invalidation"
                ),
                title="Invalidação",
                content=(
                    "Perda de força "
                    "invalida o cenário."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_identity"
                ),
                title="Ativo 2",
                content="Solana (SOL)",
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_price"
                ),
                title="Preço",
                content=(
                    "Solana: "
                    "US$ 180.00000000."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_change"
                ),
                title="Variação",
                content=(
                    "Solana: "
                    "+2.10% em 24h."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_volume"
                ),
                title="Volume",
                content=(
                    "Solana: "
                    "US$ 4,500,000,000 "
                    "de volume em 24h."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_market_cap"
                ),
                title="Capitalização",
                content=(
                    "Solana: "
                    "US$ 85,000,000,000 "
                    "de capitalização."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_score"
                ),
                title="Score",
                content=(
                    "Solana: score 70/100."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_risks"
                ),
                title="Riscos",
                content=(
                    "Risco de volatilidade."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_invalidation"
                ),
                title="Invalidação",
                content=(
                    "Queda de momentum "
                    "invalida o cenário."
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    (
        "question",
        "expected",
        "difference",
    ),
    [
        (
            (
                "Qual está com maior "
                "score, UNI ou SOL?"
            ),
            "Uniswap (UNI)",
            "7 pontos",
        ),
        (
            (
                "Qual tem maior volume "
                "entre UNI e SOL?"
            ),
            "Solana (SOL)",
            "US$ 3,850,000,000",
        ),
        (
            (
                "Qual teve maior alta "
                "em 24h, UNI ou SOL?"
            ),
            "Uniswap (UNI)",
            "2.10 pontos percentuais",
        ),
        (
            (
                "Qual tem maior "
                "capitalização, "
                "UNI ou SOL?"
            ),
            "Solana (SOL)",
            "US$ 77,500,000,000",
        ),
        (
            (
                "Qual tem menor preço, "
                "UNI ou SOL?"
            ),
            "Uniswap (UNI)",
            "US$ 167.50000000",
        ),
    ],
)
def test_quantitative_comparison_conclusion(
    question: str,
    expected: str,
    difference: str,
) -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _context(),
        question,
    )

    first_line = answer.splitlines()[0]

    assert expected in first_line

    assert difference in answer


def test_risk_does_not_invent_numeric_winner() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _context(),
        (
            "Qual apresenta menor risco, "
            "UNI ou SOL?"
        ),
    )

    assert (
        "ainda não possui uma "
        "métrica numérica de risco"
        in answer
    )

    assert "Risco de correção" in answer

    assert (
        "Risco de volatilidade"
        in answer
    )


def test_plain_score_comparison_does_not_force_winner() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _context(),
        "Compare o score de UNI e SOL",
    )

    assert (
        "apresenta maior score"
        not in answer
    )

    assert "77/100" in answer
    assert "70/100" in answer


def test_market_cap_focus_is_detected() -> None:
    resolver = (
        RadarAIAssetFocusResolver()
    )

    assert resolver.resolve(
        (
            "Qual tem maior "
            "capitalização, "
            "UNI ou SOL?"
        )
    ) == "market_cap"