from typing import Any, Optional

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
            or (
                RadarAIAssetComparisonConclusionComposer()
            )
        )

    def compose(
        self,
        context: Any,
        question: Optional[str] = None,
    ) -> str:
        if not context.is_supported:
            return (
                "Ainda não tenho contexto "
                "suficiente para responder "
                "essa pergunta."
            )

        if (
            question
            and getattr(
                context,
                "intent",
                None,
            )
            == AssistantIntent.ASSET_ANALYSIS
        ):
            return self._compose_asset_answer(
                context,
                question,
            )

        if (
            question
            and getattr(
                context,
                "intent",
                None,
            )
            == AssistantIntent.ASSET_COMPARISON
        ):
            return (
                self
                ._compose_asset_comparison_answer(
                    context,
                    question,
                )
            )

        return self._compose_all_items(
            context
        )

    def __call__(
        self,
        context: Any,
        question: Optional[str] = None,
    ) -> str:
        return self.compose(
            context,
            question,
        )

    def _compose_asset_answer(
        self,
        context: Any,
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
                (),
            )
        )

        selected_contents = [
            item.content.strip()
            for item in context.items
            if (
                item.key in selected_keys
                and item.content.strip()
            )
        ]

        if selected_contents:
            return "\n\n".join(
                selected_contents
            )

        return self._compose_all_items(
            context
        )

    def _compose_asset_comparison_answer(
        self,
        context: Any,
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

        selected_suffixes = (
            suffixes_by_focus.get(
                focus,
                (),
            )
        )

        items_by_key = {
            item.key: item.content.strip()
            for item in context.items
            if item.content.strip()
        }

        asset_blocks = []

        for position in (1, 2):
            prefix = (
                f"comparison_asset_{position}"
            )

            identity = items_by_key.get(
                f"{prefix}_identity",
                f"Ativo {position}",
            )

            contents = []

            for suffix in selected_suffixes:
                content = items_by_key.get(
                    f"{prefix}_{suffix}"
                )

                if content:
                    contents.append(
                        content
                    )

            if contents:
                asset_blocks.append(
                    "\n".join(
                        (
                            identity,
                            *contents,
                        )
                    )
                )

        if not asset_blocks:
            return self._compose_all_items(
                context
            )

        comparison_body = "\n\n".join(
            asset_blocks
        )

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
            return (
                f"{conclusion}\n\n"
                f"{comparison_body}"
            )

        return comparison_body

    @staticmethod
    def _compose_all_items(
        context: Any,
    ) -> str:
        contents = [
            item.content.strip()
            for item in context.items
            if item.content.strip()
        ]

        if not contents:
            return (
                "Os dados foram processados, "
                "mas não há informações "
                "suficientes para montar "
                "uma resposta."
            )

        return "\n\n".join(
            contents
        )