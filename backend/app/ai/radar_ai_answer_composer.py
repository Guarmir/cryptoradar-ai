from typing import Optional

from app.ai.assistant_context import (
    AssistantContext,
)
from app.ai.assistant_intent import (
    AssistantIntent,
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
        focus = (
            self._asset_focus_resolver.resolve(
                question
            )
        )

        keys_by_focus = {
            (
                RadarAIAssetFocusResolver
                .OVERVIEW
            ): (
                "asset_summary",
                "asset_price",
                "asset_change",
                "asset_score",
                "asset_signal",
            ),
            (
                RadarAIAssetFocusResolver
                .SCORE
            ): (
                "asset_score",
            ),
            (
                RadarAIAssetFocusResolver
                .SIGNAL
            ): (
                "asset_signal",
            ),
            (
                RadarAIAssetFocusResolver
                .RISK
            ): (
                "asset_risk_score",
                "asset_risk_factors",
                "asset_risks",
                "asset_invalidation",
            ),
            (
                RadarAIAssetFocusResolver
                .MARKET_CAP
            ): (
                "asset_market_cap",
            ),
            (
                RadarAIAssetFocusResolver
                .OPERATIONAL_RANGE
            ): (
                "asset_operational_range",
                "asset_operational_range_position",
                "asset_operational_range_space",
            ),
            (
                RadarAIAssetFocusResolver
                .RANGE_POSITION
            ): (
                "asset_operational_range",
                "asset_operational_range_position",
            ),
            (
                RadarAIAssetFocusResolver
                .RANGE_SPACE
            ): (
                "asset_operational_range",
                "asset_operational_range_space",
            ),
            (
                RadarAIAssetFocusResolver
                .PRICE
            ): (
                "asset_price",
            ),
            (
                RadarAIAssetFocusResolver
                .CHANGE
            ): (
                "asset_change",
            ),
            (
                RadarAIAssetFocusResolver
                .VOLUME
            ): (
                "asset_volume",
            ),
            (
                RadarAIAssetFocusResolver
                .INVALIDATION
            ): (
                "asset_invalidation",
            ),
            (
                RadarAIAssetFocusResolver
                .EXPLANATION
            ): (
                "asset_score",
                "asset_signal",
                "asset_reasons",
                "asset_risks",
                "asset_invalidation",
            ),
        }

        selected_keys = (
            keys_by_focus.get(
                focus,
                keys_by_focus[
                    RadarAIAssetFocusResolver
                    .OVERVIEW
                ],
            )
        )

        answer = self._compose_selected_items(
            context=context,
            keys=selected_keys,
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
        focus = (
            self._asset_focus_resolver.resolve(
                question
            )
        )

        suffixes_by_focus = {
            (
                RadarAIAssetFocusResolver
                .OVERVIEW
            ): (
                "summary",
                "price",
                "change",
                "volume",
                "score",
                "signal",
            ),
            (
                RadarAIAssetFocusResolver
                .SCORE
            ): (
                "score",
            ),
            (
                RadarAIAssetFocusResolver
                .SIGNAL
            ): (
                "signal",
            ),
            (
                RadarAIAssetFocusResolver
                .RISK
            ): (
                "risk_score",
                "risk_factors",
                "risks",
                "invalidation",
            ),
            (
                RadarAIAssetFocusResolver
                .MARKET_CAP
            ): (
                "market_cap",
            ),
            (
                RadarAIAssetFocusResolver
                .PRICE
            ): (
                "price",
            ),
            (
                RadarAIAssetFocusResolver
                .CHANGE
            ): (
                "change",
            ),
            (
                RadarAIAssetFocusResolver
                .VOLUME
            ): (
                "volume",
            ),
            (
                RadarAIAssetFocusResolver
                .INVALIDATION
            ): (
                "invalidation",
            ),
            (
                RadarAIAssetFocusResolver
                .EXPLANATION
            ): (
                "score",
                "signal",
                "reasons",
                "risks",
                "invalidation",
            ),
        }

        suffixes = (
            suffixes_by_focus.get(
                focus,
                suffixes_by_focus[
                    RadarAIAssetFocusResolver
                    .OVERVIEW
                ],
            )
        )

        sections = []

        conclusion = (
            self
            ._comparison_conclusion_composer
            .compose(
                context=context,
                question=question,
                focus=focus,
            )
        )

        if conclusion:
            sections.append(
                conclusion
            )

        for position in (
            1,
            2,
        ):
            prefix = (
                f"comparison_asset_{position}"
            )

            identity = (
                self._content_for_key(
                    context,
                    f"{prefix}_identity",
                )
            )

            contents = []

            for suffix in suffixes:
                content = (
                    self._content_for_key(
                        context,
                        f"{prefix}_{suffix}",
                    )
                )

                if content:
                    contents.append(
                        content
                    )

            if not contents:
                continue

            if identity:
                block = "\n".join(
                    (
                        identity,
                        *contents,
                    )
                )

            else:
                block = "\n".join(
                    contents
                )

            sections.append(
                block
            )

        if sections:
            return "\n\n".join(
                sections
            )

        return self._compose_all_items(
            context
        )

    @staticmethod
    def _compose_selected_items(
        *,
        context: AssistantContext,
        keys: tuple[str, ...],
    ) -> str:
        selected_contents = []

        item_by_key = {
            item.key: item.content.strip()
            for item in context.items
            if item.content.strip()
        }

        for key in keys:
            content = item_by_key.get(
                key
            )

            if content:
                selected_contents.append(
                    content
                )

        return "\n".join(
            selected_contents
        )

    @staticmethod
    def _content_for_key(
        context: AssistantContext,
        key: str,
    ) -> Optional[str]:
        for item in context.items:
            if item.key != key:
                continue

            content = (
                item.content.strip()
            )

            if content:
                return content

        return None

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