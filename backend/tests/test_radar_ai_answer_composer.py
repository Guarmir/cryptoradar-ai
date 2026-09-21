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