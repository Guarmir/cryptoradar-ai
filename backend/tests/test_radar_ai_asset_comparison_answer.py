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


def _comparison_context() -> AssistantContext:
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
                    "comparison_asset_1_summary"
                ),
                title="Resumo",
                content=(
                    "Movimento positivo."
                ),
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
                    "Uniswap: +4.20% em 24h."
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
                    "comparison_asset_1_score"
                ),
                title="Score",
                content=(
                    "Uniswap: score 77/100."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_signal"
                ),
                title="Sinal",
                content=(
                    "Uniswap: sinal bullish."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_reasons"
                ),
                title="Fatores",
                content=(
                    "Volume relevante."
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
                    "Perda de força invalida "
                    "o cenário."
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
                    "comparison_asset_2_summary"
                ),
                title="Resumo",
                content=(
                    "Movimento moderado."
                ),
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
                    "Solana: +2.10% em 24h."
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
                    "comparison_asset_2_score"
                ),
                title="Score",
                content=(
                    "Solana: score 70/100."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_signal"
                ),
                title="Sinal",
                content=(
                    "Solana: sinal bullish."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_reasons"
                ),
                title="Fatores",
                content=(
                    "Liquidez elevada."
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


def test_composes_general_comparison() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _comparison_context(),
        "Compare UNI e SOL",
    )

    assert "Uniswap (UNI)" in answer
    assert "Solana (SOL)" in answer

    assert "12.50000000" in answer
    assert "180.00000000" in answer

    assert "77/100" in answer
    assert "70/100" in answer


def test_composes_score_only_comparison() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _comparison_context(),
        (
            "Qual está com melhor "
            "score, UNI ou SOL?"
        ),
    )

    assert "Uniswap (UNI)" in answer
    assert "Solana (SOL)" in answer

    assert "77/100" in answer
    assert "70/100" in answer

    assert "12.50000000" not in answer
    assert "180.00000000" not in answer


def test_composes_volume_only_comparison() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _comparison_context(),
        (
            "Qual tem maior volume "
            "entre UNI e SOL?"
        ),
    )

    assert "650,000,000" in answer
    assert "4,500,000,000" in answer

    assert "77/100" not in answer
    assert "70/100" not in answer


def test_composes_risk_comparison() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _comparison_context(),
        (
            "Compare o risco "
            "de UNI e SOL"
        ),
    )

    assert "Risco de correção" in answer

    assert (
        "Risco de volatilidade"
        in answer
    )

    assert "invalida o cenário" in answer

    assert "12.50000000" not in answer


def test_composes_explanatory_comparison() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _comparison_context(),
        (
            "Por que UNI e SOL estão "
            "com esses sinais?"
        ),
    )

    assert "77/100" in answer
    assert "70/100" in answer

    assert "Volume relevante" in answer
    assert "Liquidez elevada" in answer

    assert "Risco de correção" in answer

    assert "12.50000000" not in answer