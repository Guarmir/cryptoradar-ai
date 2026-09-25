from typing import Optional

from app.ai.assistant_context import (
    AssistantContext,
)
from app.ai.radar_ai_asset_comparison_conclusion_composer import (
    RadarAIAssetComparisonConclusionComposer,
)
from app.ai.radar_ai_asset_focus_resolver import (
    RadarAIAssetFocusResolver,
)


class RadarAIAssetComparisonAnswerComposer:
    _SUFFIXES_BY_FOCUS = {
        RadarAIAssetFocusResolver.OVERVIEW: (
            "summary",
            "price",
            "change",
            "volume",
            "score",
            "signal",
        ),
        RadarAIAssetFocusResolver.SCORE: (
            "score",
        ),
        RadarAIAssetFocusResolver.SIGNAL: (
            "signal",
        ),
        RadarAIAssetFocusResolver.RISK: (
            "risk_score",
            "risk_factors",
            "risks",
            "invalidation",
        ),
        RadarAIAssetFocusResolver.MARKET_CAP: (
            "market_cap",
        ),
        RadarAIAssetFocusResolver.PRICE: (
            "price",
        ),
        RadarAIAssetFocusResolver.CHANGE: (
            "change",
        ),
        RadarAIAssetFocusResolver.VOLUME: (
            "volume",
        ),
        RadarAIAssetFocusResolver.INVALIDATION: (
            "invalidation",
        ),
        RadarAIAssetFocusResolver.EXPLANATION: (
            "score",
            "signal",
            "reasons",
            "risks",
            "invalidation",
        ),
    }

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
        *,
        context: AssistantContext,
        question: str,
    ) -> Optional[str]:
        focus = (
            self._asset_focus_resolver.resolve(
                question
            )
        )

        suffixes = (
            self._SUFFIXES_BY_FOCUS.get(
                focus,
                self._SUFFIXES_BY_FOCUS[
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

        return None

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