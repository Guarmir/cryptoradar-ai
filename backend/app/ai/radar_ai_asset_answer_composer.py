from typing import Optional

from app.ai.assistant_context import (
    AssistantContext,
)
from app.ai.radar_ai_asset_focus_resolver import (
    RadarAIAssetFocusResolver,
)


class RadarAIAssetAnswerComposer:
    _KEYS_BY_FOCUS = {
        RadarAIAssetFocusResolver.OVERVIEW: (
            "asset_summary",
            "asset_price",
            "asset_change",
            "asset_score",
            "asset_signal",
            "asset_market_context",
            "asset_relative_strength",
            "asset_operational_scenario",
            "asset_operational_scenario_support",
            "asset_operational_scenario_warnings",
        ),
        RadarAIAssetFocusResolver.SCORE: (
            "asset_score",
        ),
        RadarAIAssetFocusResolver.SIGNAL: (
            "asset_signal",
            "asset_market_context",
            "asset_market_btc",
            "asset_relative_strength",
            "asset_operational_scenario",
            "asset_operational_scenario_support",
            "asset_operational_scenario_warnings",
        ),
        RadarAIAssetFocusResolver.RISK: (
            "asset_risk_score",
            "asset_risk_factors",
            "asset_market_context",
            "asset_operational_scenario",
            "asset_operational_scenario_warnings",
            "asset_risks",
            "asset_invalidation",
        ),
        RadarAIAssetFocusResolver.MARKET_CAP: (
            "asset_market_cap",
        ),
        RadarAIAssetFocusResolver.RANGE_POSITION: (
            "asset_operational_range",
            "asset_operational_range_position",
        ),
        RadarAIAssetFocusResolver.RANGE_SPACE: (
            "asset_operational_range",
            "asset_operational_range_space",
        ),
        RadarAIAssetFocusResolver.PRICE: (
            "asset_price",
        ),
        RadarAIAssetFocusResolver.CHANGE: (
            "asset_change",
        ),
        RadarAIAssetFocusResolver.VOLUME: (
            "asset_volume",
        ),
        RadarAIAssetFocusResolver.INVALIDATION: (
            "asset_invalidation",
        ),
        RadarAIAssetFocusResolver.EXPLANATION: (
            "asset_score",
            "asset_signal",
            "asset_reasons",
            "asset_market_context",
            "asset_market_btc",
            "asset_market_breadth",
            "asset_relative_strength",
            "asset_operational_scenario",
            "asset_operational_scenario_support",
            "asset_operational_scenario_warnings",
            "asset_risks",
            "asset_invalidation",
        ),
        RadarAIAssetFocusResolver.OPERATIONAL_RANGE: (
            "asset_operational_range",
            "asset_operational_range_position",
            "asset_operational_range_space",
            "asset_operational_range_quality",
            "asset_operational_range_invalidation",
            "asset_operational_range_context",
        ),
        RadarAIAssetFocusResolver.RANGE_QUALITY: (
            "asset_operational_range",
            "asset_operational_range_quality",
        ),
        RadarAIAssetFocusResolver.RANGE_INVALIDATION: (
            "asset_operational_range",
            "asset_operational_range_invalidation",
        ),
        RadarAIAssetFocusResolver.RANGE_CONTEXT: (
            "asset_operational_range",
            "asset_operational_range_position",
            "asset_operational_range_space",
            "asset_operational_range_quality",
            "asset_operational_range_invalidation",
            "asset_operational_range_context",
            "asset_market_context",
            "asset_relative_strength",
            "asset_operational_scenario",
        ),
    }

    def __init__(
        self,
        *,
        asset_focus_resolver: Optional[
            RadarAIAssetFocusResolver
        ] = None,
    ) -> None:
        self._asset_focus_resolver = (
            asset_focus_resolver
            or RadarAIAssetFocusResolver()
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

        selected_keys = (
            self._KEYS_BY_FOCUS.get(
                focus,
                self._KEYS_BY_FOCUS[
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

        return None

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