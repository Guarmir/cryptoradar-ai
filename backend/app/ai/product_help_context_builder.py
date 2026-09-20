from app.ai.assistant_context import (
    AssistantContext,
    AssistantContextItem,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.product_knowledge import (
    PRODUCT_KNOWLEDGE_VERSION,
    search_product_knowledge,
)


PRODUCT_KNOWLEDGE_SOURCE = (
    "cryptoradar_product_knowledge"
)


def build_product_help_context(
    question: str,
    *,
    limit: int = 3,
) -> AssistantContext:
    entries = search_product_knowledge(
        question,
        limit=limit,
    )

    items = tuple(
        AssistantContextItem(
            key=entry.key,
            title=entry.title,
            content=entry.content,
        )
        for entry in entries
    )

    return AssistantContext(
        intent=(
            AssistantIntent
            .PRODUCT_HELP
        ),
        source=(
            PRODUCT_KNOWLEDGE_SOURCE
        ),
        source_version=(
            PRODUCT_KNOWLEDGE_VERSION
        ),
        items=items,
    )