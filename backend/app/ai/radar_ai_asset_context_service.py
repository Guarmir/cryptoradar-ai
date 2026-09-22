from typing import Optional

from app.ai.assistant_context import (
    AssistantContext,
    AssistantContextItem,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.crypto_asset_analysis_provider import (
    CryptoAssetAnalysisProvider,
)
from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
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


ASSET_ANALYSIS_SOURCE = (
    "cryptoradar_asset_analysis"
)

ASSET_ANALYSIS_VERSION = "v1"


class RadarAIAssetContextService:
    def __init__(
        self,
        *,
        provider: Optional[
            CryptoAssetAnalysisProvider
        ] = None,
        asset_resolver: Optional[
            RadarAIAssetResolver
        ] = None,
    ) -> None:
        self._provider = (
            provider
            or CryptoAssetAnalysisProvider()
        )

        self._asset_resolver = (
            asset_resolver
            or RadarAIAssetResolver()
        )

    def build_context(
        self,
        question: str,
    ) -> AssistantContext:
        asset_id = (
            self._asset_resolver.resolve(
                question
            )
        )

        if asset_id is None:
            raise ValueError(
                "asset not found in question"
            )

        market = self._provider.fetch(
            asset_id
        )

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

        symbol = str(
            market.get(
                "symbol",
                asset_id,
            )
        ).upper()

        name = str(
            market.get(
                "name",
                asset_id,
            )
        )

        items = (
            AssistantContextItem(
                key="asset_summary",
                title="Resumo do ativo",
                content=(
                    f"{name} ({symbol}): "
                    f"{summary}"
                ),
            ),
            AssistantContextItem(
                key="asset_price",
                title="Preço",
                content=(
                    f"{name} ({symbol}) está "
                    f"cotado em US$ {price:,.8f}."
                ),
            ),
            AssistantContextItem(
                key="asset_change",
                title="Variação em 24h",
                content=(
                    f"A variação de {name} "
                    f"nas últimas 24 horas é "
                    f"{change_24h:+.2f}%."
                ),
            ),
            AssistantContextItem(
                key="asset_volume",
                title="Volume em 24h",
                content=(
                    f"O volume negociado de "
                    f"{name} em 24 horas é "
                    f"US$ {volume:,.0f}."
                ),
            ),
            AssistantContextItem(
                key="asset_market_cap",
                title="Capitalização",
                content=(
                    f"A capitalização de "
                    f"{name} é "
                    f"US$ {market_cap:,.0f}."
                ),
            ),
            AssistantContextItem(
                key="asset_score",
                title="Score",
                content=(
                    f"O score atual de "
                    f"{name} é "
                    f"{score}/100."
                ),
            ),
            AssistantContextItem(
                key="asset_signal",
                title="Sinal",
                content=(
                    f"O sinal atual de "
                    f"{name} é {signal}, "
                    f"com confiança de "
                    f"{confidence:.0%}."
                ),
            ),
            AssistantContextItem(
                key="asset_reasons",
                title="Fatores observados",
                content="; ".join(
                    reasons
                ),
            ),
            AssistantContextItem(
                key="asset_risks",
                title="Riscos",
                content="; ".join(
                    risks
                ),
            ),
            AssistantContextItem(
                key="asset_invalidation",
                title="Invalidação",
                content=invalidation,
            ),
        )

        return AssistantContext(
            intent=(
                AssistantIntent
                .ASSET_ANALYSIS
            ),
            source=(
                ASSET_ANALYSIS_SOURCE
            ),
            source_version=(
                ASSET_ANALYSIS_VERSION
            ),
            items=items,
        )