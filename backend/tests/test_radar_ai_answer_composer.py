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


class FakeItem:
    def __init__(
        self,
        content: str,
    ) -> None:
        self.content = content


class FakeContext:
    def __init__(
        self,
        *,
        is_supported: bool,
        items,
    ) -> None:
        self.is_supported = is_supported
        self.items = items


def _asset_context() -> AssistantContext:
    return AssistantContext(
        intent=(
            AssistantIntent.ASSET_ANALYSIS
        ),
        source=(
            "cryptoradar_asset_analysis"
        ),
        source_version="v1",
        items=(
            AssistantContextItem(
                key="asset_summary",
                title="Resumo",
                content=(
                    "Uniswap apresenta "
                    "cenário positivo."
                ),
            ),
            AssistantContextItem(
                key="asset_price",
                title="Preço",
                content=(
                    "Uniswap está cotado "
                    "em US$ 12.50."
                ),
            ),
            AssistantContextItem(
                key="asset_change",
                title="Variação",
                content=(
                    "A variação em 24h "
                    "é +4.20%."
                ),
            ),
            AssistantContextItem(
                key="asset_volume",
                title="Volume",
                content=(
                    "O volume em 24h é "
                    "US$ 650,000,000."
                ),
            ),
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
                key="asset_risks",
                title="Riscos",
                content=(
                    "Possível correção "
                    "após movimento de alta."
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


def test_composes_answer_from_context_items() -> None:
    context = FakeContext(
        is_supported=True,
        items=(
            FakeItem(
                "O mercado apresenta "
                "movimento positivo."
            ),
            FakeItem(
                "O Bitcoin mantém "
                "dominância elevada."
            ),
        ),
    )

    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        context
    )

    assert answer == (
        "O mercado apresenta "
        "movimento positivo."
        "\n\n"
        "O Bitcoin mantém "
        "dominância elevada."
    )


def test_ignores_empty_context_items() -> None:
    context = FakeContext(
        is_supported=True,
        items=(
            FakeItem(""),
            FakeItem("Dados disponíveis."),
            FakeItem("   "),
        ),
    )

    composer = RadarAIAnswerComposer()

    assert composer(
        context
    ) == "Dados disponíveis."


def test_returns_message_for_unsupported_context() -> None:
    context = FakeContext(
        is_supported=False,
        items=(),
    )

    composer = RadarAIAnswerComposer()

    assert composer.compose(
        context
    ) == (
        "Ainda não tenho contexto "
        "suficiente para responder "
        "essa pergunta."
    )


def test_returns_message_when_context_is_empty() -> None:
    context = FakeContext(
        is_supported=True,
        items=(),
    )

    composer = RadarAIAnswerComposer()

    assert composer.compose(
        context
    ) == (
        "Os dados foram processados, "
        "mas não há informações "
        "suficientes para montar "
        "uma resposta."
    )


@pytest.mark.parametrize(
    (
        "question",
        "expected_fragment",
        "unexpected_fragment",
    ),
    [
        (
            "Qual o preço da UNI?",
            "US$ 12.50",
            "77/100",
        ),
        (
            "Qual o score da UNI?",
            "77/100",
            "US$ 12.50",
        ),
        (
            "Qual o sinal da UNI?",
            "bullish",
            "US$ 12.50",
        ),
        (
            "Quanto a UNI variou hoje?",
            "+4.20%",
            "77/100",
        ),
        (
            "Qual o volume da UNI?",
            "650,000,000",
            "77/100",
        ),
        (
            "O que invalida o cenário da UNI?",
            "invalida o cenário",
            "US$ 12.50",
        ),
    ],
)
def test_composes_focused_asset_answer(
    question: str,
    expected_fragment: str,
    unexpected_fragment: str,
) -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _asset_context(),
        question,
    )

    assert expected_fragment in answer

    assert unexpected_fragment not in answer


def test_risk_answer_includes_risk_and_invalidation() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _asset_context(),
        "Quais os riscos da UNI?",
    )

    assert "Possível correção" in answer

    assert "invalida o cenário" in answer


def test_overview_answer_contains_core_asset_data() -> None:
    composer = RadarAIAnswerComposer()

    answer = composer.compose(
        _asset_context(),
        "Como está a UNI?",
    )

    assert "cenário positivo" in answer
    assert "US$ 12.50" in answer
    assert "+4.20%" in answer
    assert "77/100" in answer
    assert "bullish" in answer