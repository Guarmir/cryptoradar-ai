from typing import Any, Optional

from app.ai.assistant_context import (
    AssistantContext,
    AssistantContextItem,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.radar_ai_asset_comparison_resolver import (
    RadarAIAssetComparisonResolver,
)
from app.services.asset_analysis_service import (
    calculate_ai_score,
    generate_ai_analysis,
    get_ai_confidence,
    get_ai_signal,
)
from app.services.market_data_service import (
    safe_float,
)


ASSET_COMPARISON_SOURCE = (
    "cryptoradar_asset_comparison"
)

ASSET_COMPARISON_VERSION = "v1"


class RadarAIAssetComparisonContextService:
    def __init__(
        self,
        *,
        provider: Any,
        comparison_resolver: Optional[
            RadarAIAssetComparisonResolver
        ] = None,
    ) -> None:
        self._provider = provider

        self._comparison_resolver = (
            comparison_resolver
            or RadarAIAssetComparisonResolver()
        )

    def build_context(
        self,
        question: str,
    ) -> AssistantContext:
        asset_ids = (
            self._comparison_resolver.resolve(
                question
            )
        )

        if len(asset_ids) != 2:
            raise ValueError(
                "comparison requires exactly two assets"
            )

        first_market = (
            self._provider.fetch(
                asset_ids[0]
            )
        )

        second_market = (
            self._provider.fetch(
                asset_ids[1]
            )
        )

        items = (
            *self._build_asset_items(
                position=1,
                market=first_market,
            ),
            *self._build_asset_items(
                position=2,
                market=second_market,
            ),
        )

        return AssistantContext(
            intent=(
                AssistantIntent
                .ASSET_COMPARISON
            ),
            source=(
                ASSET_COMPARISON_SOURCE
            ),
            source_version=(
                ASSET_COMPARISON_VERSION
            ),
            items=items,
        )

    @staticmethod
    def _build_asset_items(
        *,
        position: int,
        market: dict,
    ) -> tuple[
        AssistantContextItem,
        ...,
    ]:
        price = safe_float(
            market.get("current_price")
        )

        market_cap = safe_float(
            market.get("market_cap")
        )

        volume = safe_float(
            market.get("total_volume")
        )

        change_24h = safe_float(
            market.get(
                "price_change_percentage_24h"
            )
        )

        score = calculate_ai_score(
            change_24h,
            volume,
            market_cap,
        )

        signal = get_ai_signal(
            score
        )

        confidence = get_ai_confidence(
            score,
            market_cap,
            volume,
        )

        (
            summary,
            reasons,
            risks,
            invalidation,
        ) = generate_ai_analysis(
            score,
            change_24h,
            volume,
            market_cap,
        )

        name = str(
            market.get(
                "name",
                "Unknown",
            )
        )

        symbol = str(
            market.get(
                "symbol",
                "",
            )
        ).upper()

        prefix = (
            f"comparison_asset_{position}"
        )

        return (
            AssistantContextItem(
                key=f"{prefix}_identity",
                title=(
                    f"Ativo {position}"
                ),
                content=(
                    f"{name} ({symbol})"
                ),
            ),
            AssistantContextItem(
                key=f"{prefix}_summary",
                title="Resumo",
                content=summary,
            ),
            AssistantContextItem(
                key=f"{prefix}_price",
                title="Preço",
                content=(
                    f"{name}: "
                    f"US$ {price:,.8f}."
                ),
            ),
            AssistantContextItem(
                key=f"{prefix}_change",
                title="Variação em 24h",
                content=(
                    f"{name}: "
                    f"{change_24h:+.2f}% "
                    f"em 24h."
                ),
            ),
            AssistantContextItem(
                key=f"{prefix}_volume",
                title="Volume em 24h",
                content=(
                    f"{name}: "
                    f"US$ {volume:,.0f} "
                    f"de volume em 24h."
                ),
            ),
            AssistantContextItem(
                key=f"{prefix}_market_cap",
                title="Capitalização",
                content=(
                    f"{name}: "
                    f"US$ {market_cap:,.0f} "
                    f"de capitalização."
                ),
            ),
            AssistantContextItem(
                key=f"{prefix}_score",
                title="Score",
                content=(
                    f"{name}: "
                    f"score {score}/100."
                ),
            ),
            AssistantContextItem(
                key=f"{prefix}_signal",
                title="Sinal",
                content=(
                    f"{name}: "
                    f"sinal {signal}, "
                    f"confiança "
                    f"{confidence:.0%}."
                ),
            ),
            AssistantContextItem(
                key=f"{prefix}_reasons",
                title="Fatores observados",
                content=(
                    "; ".join(reasons)
                ),
            ),
            AssistantContextItem(
                key=f"{prefix}_risks",
                title="Riscos",
                content=(
                    "; ".join(risks)
                ),
            ),
            AssistantContextItem(
                key=(
                    f"{prefix}_invalidation"
                ),
                title="Invalidação",
                content=invalidation,
            ),
        )