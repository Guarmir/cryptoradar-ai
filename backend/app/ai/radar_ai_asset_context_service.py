from typing import Optional

from app.ai.asset_operational_range_intelligence_assessment import (
    calculate_asset_operational_range_context,
    calculate_asset_operational_range_invalidation,
    calculate_asset_operational_range_quality,
)
from app.ai.asset_operational_range_items_builder import (
    build_asset_operational_range_context_text,
    build_asset_operational_range_invalidation_text,
    build_asset_operational_range_items,
    build_asset_operational_range_quality_text,
    build_asset_operational_range_recurrence_text,
)
from app.ai.asset_market_context_assessment import (
    calculate_asset_market_context,
)
from app.ai.asset_operational_scenario_assessment import (
    calculate_asset_operational_scenario,
)
from app.ai.asset_operational_scenario_items_builder import (
    build_asset_operational_scenario_items,
)
from app.ai.asset_market_context_items_builder import (
    build_asset_market_context_items,
    build_asset_market_context_unavailable_item,
)
from app.ai.asset_risk_assessment import (
    calculate_asset_risk_assessment,
)
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
from app.ai.crypto_asset_operational_range_provider import (
    CryptoAssetOperationalRangeProvider,
)
from app.ai.market_overview_provider import (
    MarketOverviewProvider,
)
from app.ai.radar_ai_asset_focus_resolver import (
    RadarAIAssetFocusResolver,
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
        operational_range_provider: Optional[
            CryptoAssetOperationalRangeProvider
        ] = None,
        asset_focus_resolver: Optional[
            RadarAIAssetFocusResolver
        ] = None,
        market_overview_provider: Optional[
            MarketOverviewProvider
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

        self._operational_range_provider = (
            operational_range_provider
            or CryptoAssetOperationalRangeProvider()
        )

        self._asset_focus_resolver = (
            asset_focus_resolver
            or RadarAIAssetFocusResolver()
        )

        self._market_overview_provider = (
            market_overview_provider
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

        risk_assessment = (
            calculate_asset_risk_assessment(
                change_24h=change_24h,
                volume=volume,
                market_cap=market_cap,
            )
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

        items = [
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
                    f"cotado em US$ "
                    f"{price:,.8f}."
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
                key="asset_risk_score",
                title="Risk Score",
                content=(
                    f"Risk Score de {name}: "
                    f"{risk_assessment.score}/100 "
                    f"— risco "
                    f"{risk_assessment.level}."
                ),
            ),
            AssistantContextItem(
                key="asset_risk_factors",
                title="Fatores de risco",
                content="; ".join(
                    risk_assessment.factors
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
        ]

        focus = (
            self._asset_focus_resolver.resolve(
                question
            )
        )

        market_context_assessment = None
        quality_assessment = None
        invalidation_assessment = None

        market_context_focuses = {
            RadarAIAssetFocusResolver.OVERVIEW,
            RadarAIAssetFocusResolver.SIGNAL,
            RadarAIAssetFocusResolver.RISK,
            RadarAIAssetFocusResolver.EXPLANATION,
            RadarAIAssetFocusResolver.RANGE_CONTEXT,
        }

        if (
            self._market_overview_provider
            is not None
            and focus in market_context_focuses
        ):
            fetch_market_overview = getattr(
                self._market_overview_provider,
                "fetch",
                None,
            )

            if callable(
                fetch_market_overview
            ):
                try:
                   market_overview = (
                       fetch_market_overview()
                    )
                except RuntimeError:
                    items.append(
                        build_asset_market_context_unavailable_item(
                            name=name,
                        )
                    )
                else:
                    market_context_assessment = (
                        calculate_asset_market_context(
                            asset_change_24h_percent=(
                                change_24h
                            ),
                            snapshot=market_overview,
                        )
                    )

                    market_context_items = (
                        build_asset_market_context_items(
                            name=name,
                            asset_change_24h_percent=(
                                change_24h
                            ),
                            snapshot=market_overview,
                        )
                    )

                    if symbol == "BTC":
                        market_context_items = tuple(
                            item
                            for item in market_context_items
                            if (
                                item.key
                                != "asset_relative_strength"
                            )
                        )

                    items.extend(
                        market_context_items
                    )

        range_focuses = {
            RadarAIAssetFocusResolver.OPERATIONAL_RANGE,
            RadarAIAssetFocusResolver.RANGE_POSITION,
            RadarAIAssetFocusResolver.RANGE_SPACE,
            RadarAIAssetFocusResolver.RANGE_QUALITY,
            RadarAIAssetFocusResolver.RANGE_INVALIDATION,
            RadarAIAssetFocusResolver.RANGE_CONTEXT,
        }

        deep_focuses = {
            RadarAIAssetFocusResolver.OPERATIONAL_RANGE,
            RadarAIAssetFocusResolver.RANGE_QUALITY,
            RadarAIAssetFocusResolver.RANGE_INVALIDATION,
            RadarAIAssetFocusResolver.RANGE_CONTEXT,
        }

        if focus in range_focuses:
            range_assessment = (
                self._operational_range_provider.fetch(
                    asset_id=asset_id,
                    current_price=price,
                )
            )

            recurrence_assessment = None
            quality_assessment = None
            invalidation_assessment = None
            consolidated_context = None

            if (
                range_assessment is not None
                and focus in deep_focuses
            ):
                fetch_recurrence = getattr(
                    self._operational_range_provider,
                    "fetch_recurrence",
                    None,
                )

                if callable(
                    fetch_recurrence
                ):
                    recurrence_assessment = (
                        fetch_recurrence(
                            asset_id=asset_id,
                            current_price=price,
                        )
                    )

            if (
                range_assessment is not None
                and recurrence_assessment
                is not None
                and focus in deep_focuses
            ):
                historical_average_volume = (
                    None
                )

                fetch_historical_volume = (
                    getattr(
                        self
                        ._operational_range_provider,
                        (
                            "fetch_historical_"
                            "average_volume"
                        ),
                        None,
                    )
                )

                if callable(
                    fetch_historical_volume
                ):
                    historical_average_volume = (
                        fetch_historical_volume(
                            asset_id=asset_id,
                        )
                    )

                quality_assessment = (
                    calculate_asset_operational_range_quality(
                        recurrence=(
                            recurrence_assessment
                        ),
                        current_volume=volume,
                        market_cap=market_cap,
                        historical_average_volume=(
                            historical_average_volume
                        ),
                    )
                )

                invalidation_assessment = (
                    calculate_asset_operational_range_invalidation(
                        range_assessment=(
                            range_assessment
                        ),
                        quality=(
                            quality_assessment
                        ),
                    )
                )

                consolidated_context = (
                    calculate_asset_operational_range_context(
                        range_assessment=(
                            range_assessment
                        ),
                        quality=(
                            quality_assessment
                        ),
                        invalidation=(
                            invalidation_assessment
                        ),
                    )
                )

            items.extend(
                self._build_operational_range_items(
                    name=name,
                    assessment=(
                        range_assessment
                    ),
                    recurrence_assessment=(
                        recurrence_assessment
                    ),
                    quality_assessment=(
                        quality_assessment
                    ),
                    invalidation_assessment=(
                        invalidation_assessment
                    ),
                    consolidated_context=(
                        consolidated_context
                    ),
                )
            )

        if (
            focus in market_context_focuses
            and market_context_assessment
            is not None
        ):
            operational_scenario = (
                calculate_asset_operational_scenario(
                    score=score,
                    change_24h_percent=(
                        change_24h
                    ),
                    risk_score=(
                        risk_assessment.score
                    ),
                    range_quality_state=(
                        quality_assessment.state
                        if quality_assessment
                        is not None
                        else None
                    ),
                    range_invalidation_state=(
                        invalidation_assessment.state
                        if invalidation_assessment
                        is not None
                        else None
                    ),
                    market_context_state=(
                        market_context_assessment.state
                    ),
                    relative_strength_state=(
                        None
                        if symbol == "BTC"
                        else (
                            market_context_assessment
                            .relative_strength_state
                        )
                    ),
                )
            )

            items.extend(
                build_asset_operational_scenario_items(
                    name=name,
                    assessment=(
                        operational_scenario
                    ),
                )
            )

        return AssistantContext(
            intent=(
                AssistantIntent.ASSET_ANALYSIS
            ),
            source=(
                ASSET_ANALYSIS_SOURCE
            ),
            source_version=(
                ASSET_ANALYSIS_VERSION
            ),
            items=tuple(items),
        )

    @staticmethod
    def _build_operational_range_items(
        *,
        name: str,
        assessment,
        recurrence_assessment=None,
        quality_assessment=None,
        invalidation_assessment=None,
        consolidated_context=None,
    ) -> tuple[
        AssistantContextItem,
        ...,
    ]:
        return build_asset_operational_range_items(
            name=name,
            assessment=assessment,
            recurrence_assessment=(
                recurrence_assessment
            ),
            quality_assessment=(
                quality_assessment
            ),
            invalidation_assessment=(
                invalidation_assessment
            ),
            consolidated_context=(
                consolidated_context
            ),
        )

    @staticmethod
    def _build_recurrence_text(
        assessment,
    ) -> str:
        return (
            build_asset_operational_range_recurrence_text(
                assessment
            )
        )

    @staticmethod
    def _build_quality_text(
        *,
        name: str,
        assessment,
    ) -> str:
        return (
            build_asset_operational_range_quality_text(
                name=name,
                assessment=assessment,
            )
        )

    @staticmethod
    def _build_invalidation_text(
        *,
        name: str,
        assessment,
    ) -> str:
        return (
            build_asset_operational_range_invalidation_text(
                name=name,
                assessment=assessment,
            )
        )

    @staticmethod
    def _build_context_text(
        *,
        name: str,
        assessment,
    ) -> str:
        return (
            build_asset_operational_range_context_text(
                name=name,
                assessment=assessment,
            )
        )