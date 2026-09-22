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
from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)


@pytest.mark.parametrize(
    "question",
    [
        "Por que a UNI está com esse sinal?",
        "Por que o Bitcoin está bullish?",
        "O que está sustentando esse score da UNI?",
        "Explique o sinal do ETH.",
        "Qual o motivo desse sinal da SOL?",
    ],
)
def test_explanatory_questions_are_detected(
    question: str,
) -> None:
    resolver = (
        RadarAIAssetFocusResolver()
    )

    assert resolver.resolve(
        question
    ) == "explanation"


def test_regular_signal_question_remains_signal() -> None:
    resolver = (
        RadarAIAssetFocusResolver()
    )

    assert resolver.resolve(
        "Qual o sinal da UNI?"
    ) == "signal"


def test_invalidation_question_remains_invalidation() -> None:
    resolver = (
        RadarAIAssetFocusResolver()
    )

    assert resolver.resolve(
        "O que pode invalidar essa análise da UNI?"
    ) == "invalidation"


def test_dynamic_asset_supports_explanatory_signal_question() -> None:
    received = []

    def dynamic_coin_resolver(
        candidate: str,
    ):
        received.append(
            candidate
        )

        if candidate == "pippin":
            return "pippin"

        return None

    resolver = RadarAIAssetResolver(
        dynamic_coin_resolver=(
            dynamic_coin_resolver
        ),
    )

    assert resolver.resolve(
        "Por que PIPPIN está bullish?"
    ) == "pippin"

    assert "pippin" in received


def test_explanatory_answer_contains_analysis_evidence() -> None:
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
                key="asset_score",
                title="Score",
                content=(
                    "O score atual de "
                    "Uniswap é 77/100."
                ),
            ),
            AssistantContextItem(
                key="asset_signal",
                title="Sinal",
                content=(
                    "O sinal atual de "
                    "Uniswap é bullish."
                ),
            ),
            AssistantContextItem(
                key="asset_reasons",
                title="Fatores observados",
                content=(
                    "Variação positiva e "
                    "volume relevante."
                ),
            ),
            AssistantContextItem(
                key="asset_risks",
                title="Riscos",
                content=(
                    "Existe risco de "
                    "correção de curto prazo."
                ),
            ),
            AssistantContextItem(
                key="asset_invalidation",
                title="Invalidação",
                content=(
                    "Perda de força "
                    "compradora invalida "
                    "o cenário."
                ),
            ),
        ),
    )

    composer = (
        RadarAIAnswerComposer()
    )

    answer = composer.compose(
        context,
        (
            "Por que a UNI está "
            "com esse sinal?"
        ),
    )

    assert "77/100" in answer
    assert "bullish" in answer

    assert (
        "Variação positiva"
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


def test_explanatory_answer_does_not_include_unrelated_price() -> None:
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
                key="asset_signal",
                title="Sinal",
                content=(
                    "O sinal atual de "
                    "Uniswap é bullish."
                ),
            ),
            AssistantContextItem(
                key="asset_reasons",
                title="Fatores",
                content=(
                    "Movimento positivo."
                ),
            ),
        ),
    )

    composer = (
        RadarAIAnswerComposer()
    )

    answer = composer.compose(
        context,
        "Por que a UNI está bullish?",
    )

    assert "bullish" in answer

    assert "Movimento positivo" in (
        answer
    )

    assert "US$ 12.50" not in (
        answer
    )