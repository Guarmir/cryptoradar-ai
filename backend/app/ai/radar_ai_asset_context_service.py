from typing import Optional

from app.ai.asset_operational_range_intelligence_assessment import (
    calculate_asset_operational_range_context,
    calculate_asset_operational_range_invalidation,
    calculate_asset_operational_range_quality,
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
        if assessment is None:
            return (
                AssistantContextItem(
                    key=(
                        "asset_operational_range"
                    ),
                    title="Faixa operacional",
                    content=(
                        "Não há histórico "
                        "suficiente para calcular "
                        "a faixa operacional "
                        f"recente de {name}."
                    ),
                ),
            )

        amplitude_status = (
            "está dentro"
            if (
                assessment
                .is_operational_amplitude
            )
            else "está fora"
        )

        range_content = (
            f"A faixa recente observada "
            f"de {name} vai de "
            f"US$ "
            f"{assessment.lower_limit:,.8f} "
            f"até US$ "
            f"{assessment.upper_limit:,.8f}. "
            f"A amplitude é de "
            f"{assessment.amplitude_percent:.2f}% "
            f"e {amplitude_status} da "
            f"faixa-alvo operacional "
            f"de 4% a 6%."
        )

        if recurrence_assessment is not None:
            range_content = (
                f"{range_content} "
                f"{RadarAIAssetContextService._build_recurrence_text(recurrence_assessment)}"
            )

        items = [
            AssistantContextItem(
                key=(
                    "asset_operational_range"
                ),
                title="Faixa operacional",
                content=range_content,
            ),
            AssistantContextItem(
                key=(
                    "asset_operational_range_position"
                ),
                title="Posição na faixa",
                content=(
                    f"A posição relativa do preço "
                    f"de {name} é "
                    f"{assessment.position_percent:.2f}% "
                    f"da amplitude observada "
                    f"(0% = limite inferior; "
                    f"100% = limite superior)."
                ),
            ),
            AssistantContextItem(
                key=(
                    "asset_operational_range_space"
                ),
                title="Espaço na faixa",
                content=(
                    f"Distância do preço atual "
                    f"ao limite inferior: "
                    f"{assessment.distance_to_lower_percent:.2f}%. "
                    f"Distância ao limite superior: "
                    f"{assessment.distance_to_upper_percent:.2f}%."
                ),
            ),
        ]

        if quality_assessment is not None:
            items.append(
                AssistantContextItem(
                    key=(
                        "asset_operational_range_quality"
                    ),
                    title=(
                        "Qualidade da faixa"
                    ),
                    content=(
                        RadarAIAssetContextService
                        ._build_quality_text(
                            name=name,
                            assessment=(
                                quality_assessment
                            ),
                        )
                    ),
                )
            )

        if invalidation_assessment is not None:
            items.append(
                AssistantContextItem(
                    key=(
                        "asset_operational_range_invalidation"
                    ),
                    title=(
                        "Risco de invalidação "
                        "da faixa"
                    ),
                    content=(
                        RadarAIAssetContextService
                        ._build_invalidation_text(
                            name=name,
                            assessment=(
                                invalidation_assessment
                            ),
                        )
                    ),
                )
            )

        if consolidated_context is not None:
            items.append(
                AssistantContextItem(
                    key=(
                        "asset_operational_range_context"
                    ),
                    title=(
                        "Contexto operacional "
                        "consolidado"
                    ),
                    content=(
                        RadarAIAssetContextService
                        ._build_context_text(
                            name=name,
                            assessment=(
                                consolidated_context
                            ),
                        )
                    ),
                )
            )

        return tuple(items)

    @staticmethod
    def _build_recurrence_text(
        assessment,
    ) -> str:
        details = (
            f"Foram identificados "
            f"{assessment.lower_limit_touches} "
            f"toques no limite inferior e "
            f"{assessment.upper_limit_touches} "
            f"toques no limite superior, "
            f"com "
            f"{assessment.completed_oscillations} "
            f"oscilações completas estimadas."
        )

        if (
            assessment
            .suggests_organized_oscillation
        ):
            return (
                f"{details} "
                f"A recorrência é forte e "
                f"equilibrada, sugerindo "
                f"oscilação organizada "
                f"dentro da faixa observada."
            )

        if (
            assessment
            .suggests_recurring_range
        ):
            return (
                f"{details} "
                f"A faixa apresenta "
                f"recorrência mínima "
                f"confirmada, mas o histórico "
                f"ainda não é forte o "
                f"suficiente para classificá-la "
                f"como oscilação organizada."
            )

        return (
            f"{details} "
            f"A recorrência observada ainda "
            f"é insuficiente para confirmar "
            f"comportamento repetitivo "
            f"entre os dois limites."
        )

    @staticmethod
    def _build_quality_text(
        *,
        name: str,
        assessment,
    ) -> str:
        labels = {
            "strong": "forte",
            "acceptable": "aceitável",
            "under_observation": (
                "em observação"
            ),
            "weak": "fraca",
        }

        label = labels.get(
            assessment.state,
            assessment.state,
        )

        return (
            f"A qualidade operacional "
            f"da faixa de {name} é "
            f"{label}. "
            f"Confirmação por volume: "
            f"{assessment.volume_confirmation_state}. "
            f"Liquidez observada: "
            f"{assessment.liquidity_state}."
        )

    @staticmethod
    def _build_invalidation_text(
        *,
        name: str,
        assessment,
    ) -> str:
        labels = {
            "low": "baixo",
            "moderate": "moderado",
            "high": "alto",
            "invalidated": "invalidada",
        }

        label = labels.get(
            assessment.state,
            assessment.state,
        )

        if assessment.is_invalidated:
            return (
                f"A faixa observada de {name} "
                f"está invalidada porque o "
                f"preço atual saiu dos limites "
                f"utilizados no cálculo."
            )

        return (
            f"O risco estrutural observado "
            f"de invalidação da faixa de "
            f"{name} é {label}. "
            f"Esse indicador descreve a "
            f"estrutura da faixa e não o "
            f"risco total do ativo."
        )

    @staticmethod
    def _build_context_text(
        *,
        name: str,
        assessment,
    ) -> str:
        labels = {
            "organized": (
                "organizado"
            ),
            "usable": (
                "utilizável, mas sem "
                "confirmação forte"
            ),
            "under_observation": (
                "em observação"
            ),
            "invalidated": (
                "invalidado"
            ),
        }

        zones = {
            "below_range": (
                "abaixo da faixa"
            ),
            "lower": (
                "região inferior"
            ),
            "middle": (
                "região central"
            ),
            "upper": (
                "região superior"
            ),
            "above_range": (
                "acima da faixa"
            ),
        }

        state_label = labels.get(
            assessment.state,
            assessment.state,
        )

        zone_label = zones.get(
            assessment.position_zone,
            assessment.position_zone,
        )

        return (
            f"O contexto operacional "
            f"consolidado de {name} está "
            f"{state_label}. "
            f"O preço está na "
            f"{zone_label}. "
            f"Essa leitura é observacional "
            f"e não representa recomendação "
            f"de compra ou venda."
        )