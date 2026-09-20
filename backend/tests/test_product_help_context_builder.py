import pytest

from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.product_help_context_builder import (
    PRODUCT_KNOWLEDGE_SOURCE,
    build_product_help_context,
)


def test_builds_supported_score_context():
    context = build_product_help_context(
        "O que significa o score?"
    )

    assert context.is_supported

    assert context.intent == (
        AssistantIntent
        .PRODUCT_HELP
    )

    assert context.source == (
        PRODUCT_KNOWLEDGE_SOURCE
    )

    assert (
        context.source_version
        == "v1"
    )

    assert context.items[0].key == (
        "score"
    )


def test_builds_notification_context():
    context = build_product_help_context(
        "Como funcionam os alertas "
        "e notificacoes?"
    )

    keys = {
        item.key
        for item in context.items
    }

    assert "notifications" in keys


def test_builds_position_monitor_context():
    context = build_product_help_context(
        "Como configuro uma "
        "posicao aberta no monitor?"
    )

    keys = {
        item.key
        for item in context.items
    }

    assert "position_monitor" in keys


def test_unknown_question_is_not_supported():
    context = build_product_help_context(
        "banana azul"
    )

    assert not context.is_supported
    assert context.items == ()
    assert context.render() == ""


def test_render_contains_official_content():
    context = build_product_help_context(
        "O que significa o score?"
    )

    rendered = context.render()

    assert "Score do ativo" in rendered
    assert "apoio a analise" in rendered


def test_render_does_not_include_unrelated_content():
    context = build_product_help_context(
        "O que significa o score?"
    )

    rendered = context.render()

    assert "Monitor de posicao" not in (
        rendered
    )


def test_limit_is_respected():
    context = build_product_help_context(
        (
            "Como funciona score, "
            "alerta, notificacao, "
            "monitor e posicao?"
        ),
        limit=2,
    )

    assert len(
        context.items
    ) <= 2


def test_invalid_limit_is_rejected():
    with pytest.raises(
        ValueError
    ):
        build_product_help_context(
            "Como funciona o score?",
            limit=0,
        )