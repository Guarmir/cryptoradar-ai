from app.ai.assistant_intent import (
    AssistantIntent,
    classify_assistant_intent,
)
from app.ai.product_knowledge import (
    PRODUCT_KNOWLEDGE_VERSION,
    search_product_knowledge,
)


def test_classifies_market_overview():
    result = classify_assistant_intent(
        "Como esta o mercado de "
        "criptomoedas hoje?"
    )

    assert result == (
        AssistantIntent
        .MARKET_OVERVIEW
    )


def test_classifies_market_opportunities():
    result = classify_assistant_intent(
        "Quais oportunidades do mercado "
        "estao chamando atencao?"
    )

    assert result == (
        AssistantIntent
        .MARKET_OVERVIEW
    )


def test_classifies_product_help():
    result = classify_assistant_intent(
        "Como configuro uma posicao aberta?"
    )

    assert result == (
        AssistantIntent
        .PRODUCT_HELP
    )


def test_classifies_score_as_product_help():
    result = classify_assistant_intent(
        "O que significa o score?"
    )

    assert result == (
        AssistantIntent
        .PRODUCT_HELP
    )


def test_empty_question_is_unknown():
    result = classify_assistant_intent(
        "   "
    )

    assert result == (
        AssistantIntent.UNKNOWN
    )


def test_unrelated_question_is_unknown():
    result = classify_assistant_intent(
        "Qual e a capital da Franca?"
    )

    assert result == (
        AssistantIntent.UNKNOWN
    )


def test_finds_score_knowledge():
    results = search_product_knowledge(
        "O que significa o score?"
    )

    assert results
    assert results[0].key == "score"


def test_finds_notification_knowledge():
    results = search_product_knowledge(
        "Como funcionam os alertas "
        "e notificacoes?"
    )

    keys = {
        result.key
        for result in results
    }

    assert "notifications" in keys


def test_unknown_product_question_returns_empty():
    results = search_product_knowledge(
        "banana azul"
    )

    assert results == ()


def test_product_knowledge_has_version():
    assert (
        PRODUCT_KNOWLEDGE_VERSION
        == "v1"
    )