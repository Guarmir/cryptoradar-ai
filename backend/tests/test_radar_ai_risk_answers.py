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


def test_individual_risk_answer_uses_risk_score() -> None:
    context = AssistantContext(
        intent=(
            AssistantIntent.ASSET_ANALYSIS
        ),
        source=(
            "cryptoradar_asset_analysis"
        ),
        source_version="v1",
        items=(
            AssistantContextItem(
                key="asset_price",
                title="Preço",
                content=(
                    "Uniswap está cotado "
                    "em US$ 12.50."
                ),
            ),
            AssistantContextItem(
                key="asset_risk_score",
                title="Risk Score",
                content=(
                    "Risk Score de Uniswap: "
                    "42/100 — risco moderado."
                ),
            ),
            AssistantContextItem(
                key="asset_risk_factors",
                title="Fatores de risco",
                content=(
                    "Capitalização intermediária; "
                    "boa atividade relativa; "
                    "volatilidade moderada."
                ),
            ),
            AssistantContextItem(
                key="asset_risks",
                title="Riscos",
                content=(
                    "Existe risco de correção."
                ),
            ),
            AssistantContextItem(
                key="asset_invalidation",
                title="Invalidação",
                content=(
                    "Perda de força invalida "
                    "o cenário."
                ),
            ),
        ),
    )

    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        context,
        "Qual o risco da UNI?",
    )

    assert "42/100" in answer

    assert (
        "Capitalização intermediária"
        in answer
    )

    assert (
        "risco de correção"
        in answer
    )

    assert (
        "invalida o cenário"
        in answer
    )

    assert "US$ 12.50" not in answer


def test_comparison_risk_answer_uses_both_risk_scores() -> None:
    context = AssistantContext(
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
                    "comparison_asset_1_risk_score"
                ),
                title="Risk Score",
                content=(
                    "Uniswap: Risk Score "
                    "42/100 — risco moderado."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_1_risk_factors"
                ),
                title="Fatores",
                content=(
                    "Capitalização intermediária."
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
                    "comparison_asset_2_risk_score"
                ),
                title="Risk Score",
                content=(
                    "Solana: Risk Score "
                    "31/100 — risco moderado."
                ),
            ),
            AssistantContextItem(
                key=(
                    "comparison_asset_2_risk_factors"
                ),
                title="Fatores",
                content=(
                    "Capitalização muito elevada."
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

    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        context,
        (
            "Qual apresenta menor risco, "
            "UNI ou SOL?"
        ),
    )

    assert (
        "Solana (SOL) apresenta "
        "menor Risk Score"
        in answer
    )

    assert "11 pontos" in answer

    assert "42/100" in answer
    assert "31/100" in answer

    assert (
        "Capitalização intermediária"
        in answer
    )

    assert (
        "Capitalização muito elevada"
        in answer
    )