from typing import Optional

from app.ai.assistant_context import (
    AssistantContext,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.radar_ai_asset_answer_composer import (
    RadarAIAssetAnswerComposer,
)
from app.ai.radar_ai_asset_comparison_answer_composer import (
    RadarAIAssetComparisonAnswerComposer,
)
from app.ai.radar_ai_asset_comparison_conclusion_composer import (
    RadarAIAssetComparisonConclusionComposer,
)
from app.ai.radar_ai_asset_focus_resolver import (
    RadarAIAssetFocusResolver,
)


class RadarAIAnswerComposer:
    _UNSUPPORTED_MESSAGE = (
        "Ainda não tenho contexto "
        "suficiente para responder "
        "essa pergunta."
    )

    _EMPTY_CONTEXT_MESSAGE = (
        "Os dados foram processados, "
        "mas não há informações "
        "suficientes para montar "
        "uma resposta."
    )

    def __init__(
        self,
        *,
        asset_focus_resolver: Optional[
            RadarAIAssetFocusResolver
        ] = None,
        comparison_conclusion_composer: Optional[
            RadarAIAssetComparisonConclusionComposer
        ] = None,
    ) -> None:
        self._asset_focus_resolver = (
            asset_focus_resolver
            or RadarAIAssetFocusResolver()
        )

        self._comparison_conclusion_composer = (
            comparison_conclusion_composer
            or RadarAIAssetComparisonConclusionComposer()
        )

        self._asset_answer_composer = (
            RadarAIAssetAnswerComposer(
                asset_focus_resolver=(
                    self._asset_focus_resolver
                ),
            )
        )

        self._asset_comparison_answer_composer = (
            RadarAIAssetComparisonAnswerComposer(
                asset_focus_resolver=(
                    self._asset_focus_resolver
                ),
                comparison_conclusion_composer=(
                    self
                    ._comparison_conclusion_composer
                ),
            )
        )

    def compose(
        self,
        context: AssistantContext,
        question: Optional[str] = None,
    ) -> str:
        if not context.is_supported:
            return self._UNSUPPORTED_MESSAGE

        intent = getattr(
            context,
            "intent",
            None,
        )

        if (
            intent
            == AssistantIntent.ASSET_ANALYSIS
            and question
        ):
            return self._compose_asset_answer(
                context=context,
                question=question,
            )

        if (
            intent
            == AssistantIntent.ASSET_COMPARISON
            and question
        ):
            return (
                self
                ._compose_asset_comparison_answer(
                    context=context,
                    question=question,
                )
            )

        return self._compose_all_items(
            context
        )

    def __call__(
        self,
        context: AssistantContext,
        question: Optional[str] = None,
    ) -> str:
        return self.compose(
            context,
            question,
        )

    def _compose_asset_answer(
        self,
        *,
        context: AssistantContext,
        question: str,
    ) -> str:
        answer = (
            self._asset_answer_composer.compose(
                context=context,
                question=question,
            )
        )

        if answer:
            return answer

        return self._compose_all_items(
            context
        )

    def _compose_asset_comparison_answer(
        self,
        *,
        context: AssistantContext,
        question: str,
    ) -> str:
        answer = (
            self
            ._asset_comparison_answer_composer
            .compose(
                context=context,
                question=question,
            )
        )

        if answer:
            return answer

        return self._compose_all_items(
            context
        )

    @staticmethod
    def _compose_selected_items(
        *,
        context: AssistantContext,
        keys: tuple[str, ...],
    ) -> str:
        return (
            RadarAIAssetAnswerComposer
            ._compose_selected_items(
                context=context,
                keys=keys,
            )
        )

    @staticmethod
    def _content_for_key(
        context: AssistantContext,
        key: str,
    ) -> Optional[str]:
        return (
            RadarAIAssetComparisonAnswerComposer
            ._content_for_key(
                context,
                key,
            )
        )

    @classmethod
    def _compose_all_items(
        cls,
        context: AssistantContext,
    ) -> str:
        contents = [
            item.content.strip()
            for item in context.items
            if item.content.strip()
        ]

        if not contents:
            return (
                cls._EMPTY_CONTEXT_MESSAGE
            )

        return "\n\n".join(
            contents
        )