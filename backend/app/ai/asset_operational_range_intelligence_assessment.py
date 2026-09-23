from dataclasses import dataclass
import math
from typing import Optional

from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
)
from app.ai.asset_operational_range_recurrence_assessment import (
    AssetOperationalRangeRecurrenceAssessment,
)


@dataclass(frozen=True)
class AssetOperationalRangeQualityAssessment:
    state: str
    recurrence_state: str
    volume_confirmation_state: str
    liquidity_state: str
    volume_ratio: Optional[float]
    turnover_ratio: Optional[float]
    factors: tuple[str, ...]


@dataclass(frozen=True)
class AssetOperationalRangeInvalidationAssessment:
    state: str
    is_invalidated: bool
    factors: tuple[str, ...]


@dataclass(frozen=True)
class AssetOperationalRangeConsolidatedContextAssessment:
    state: str
    position_zone: str
    factors: tuple[str, ...]


def calculate_asset_operational_range_quality(
    *,
    recurrence: AssetOperationalRangeRecurrenceAssessment,
    current_volume: float,
    market_cap: float,
    historical_average_volume: Optional[float],
) -> AssetOperationalRangeQualityAssessment:
    current_volume_value = _positive_float(
        current_volume
    )

    market_cap_value = _positive_float(
        market_cap
    )

    historical_volume_value = _positive_float(
        historical_average_volume
    )

    volume_ratio = None

    if (
        current_volume_value is not None
        and historical_volume_value is not None
    ):
        volume_ratio = (
            current_volume_value
            / historical_volume_value
        )

    if volume_ratio is None:
        volume_confirmation_state = (
            "unavailable"
        )

    elif volume_ratio >= 1.10:
        volume_confirmation_state = (
            "confirmed"
        )

    elif volume_ratio >= 0.75:
        volume_confirmation_state = (
            "acceptable"
        )

    else:
        volume_confirmation_state = "weak"

    turnover_ratio = None

    if (
        current_volume_value is not None
        and market_cap_value is not None
    ):
        turnover_ratio = (
            current_volume_value
            / market_cap_value
        )

    if turnover_ratio is None:
        liquidity_state = "unavailable"

    elif turnover_ratio >= 0.10:
        liquidity_state = "strong"

    elif turnover_ratio >= 0.03:
        liquidity_state = "acceptable"

    else:
        liquidity_state = "weak"

    has_market_support = (
        volume_confirmation_state
        in {
            "confirmed",
            "acceptable",
        }
        and liquidity_state
        in {
            "strong",
            "acceptable",
        }
    )

    if (
        recurrence
        .suggests_organized_oscillation
        and has_market_support
    ):
        state = "strong"

    elif (
        recurrence
        .suggests_recurring_range
        and has_market_support
    ):
        state = "acceptable"

    elif (
        recurrence
        .suggests_recurring_range
        or recurrence
        .suggests_organized_oscillation
    ):
        state = "under_observation"

    else:
        state = "weak"

    factors = [
        (
            "Recorrência observada: "
            f"{recurrence.state}."
        ),
    ]

    if volume_ratio is None:
        factors.append(
            "Confirmação por volume "
            "histórico indisponível."
        )

    else:
        factors.append(
            "Volume atual equivale a "
            f"{volume_ratio:.2f}x a média "
            "histórica observada."
        )

    if turnover_ratio is None:
        factors.append(
            "Indicador de liquidez por "
            "giro indisponível."
        )

    else:
        factors.append(
            "Relação volume/market cap: "
            f"{turnover_ratio:.2%}."
        )

    return (
        AssetOperationalRangeQualityAssessment(
            state=state,
            recurrence_state=(
                recurrence.state
            ),
            volume_confirmation_state=(
                volume_confirmation_state
            ),
            liquidity_state=(
                liquidity_state
            ),
            volume_ratio=volume_ratio,
            turnover_ratio=turnover_ratio,
            factors=tuple(factors),
        )
    )


def calculate_asset_operational_range_invalidation(
    *,
    range_assessment: AssetOperationalRangeAssessment,
    quality: AssetOperationalRangeQualityAssessment,
) -> AssetOperationalRangeInvalidationAssessment:
    position = (
        range_assessment.position_percent
    )

    if (
        position < 0
        or position > 100
    ):
        return (
            AssetOperationalRangeInvalidationAssessment(
                state="invalidated",
                is_invalidated=True,
                factors=(
                    (
                        "O preço atual está fora "
                        "dos limites observados "
                        "da faixa."
                    ),
                    (
                        "Posição relativa: "
                        f"{position:.2f}%."
                    ),
                ),
            )
        )

    if quality.state == "strong":
        state = "low"

    elif quality.state == "acceptable":
        state = "moderate"

    else:
        state = "high"

    factors = [
        (
            "Qualidade operacional da faixa: "
            f"{quality.state}."
        ),
        (
            "O preço permanece dentro dos "
            "limites observados."
        ),
    ]

    if (
        position <= 10
        or position >= 90
    ):
        factors.append(
            "O preço está próximo de um "
            "dos extremos da faixa."
        )

    return (
        AssetOperationalRangeInvalidationAssessment(
            state=state,
            is_invalidated=False,
            factors=tuple(factors),
        )
    )


def calculate_asset_operational_range_context(
    *,
    range_assessment: AssetOperationalRangeAssessment,
    quality: AssetOperationalRangeQualityAssessment,
    invalidation: AssetOperationalRangeInvalidationAssessment,
) -> AssetOperationalRangeConsolidatedContextAssessment:
    position = (
        range_assessment.position_percent
    )

    if position < 0:
        position_zone = "below_range"

    elif position <= 25:
        position_zone = "lower"

    elif position < 75:
        position_zone = "middle"

    elif position <= 100:
        position_zone = "upper"

    else:
        position_zone = "above_range"

    if invalidation.is_invalidated:
        state = "invalidated"

    elif (
        quality.state == "strong"
        and invalidation.state == "low"
    ):
        state = "organized"

    elif (
        quality.state == "acceptable"
        and invalidation.state
        in {
            "low",
            "moderate",
        }
    ):
        state = "usable"

    else:
        state = "under_observation"

    factors = (
        (
            "Qualidade da faixa: "
            f"{quality.state}."
        ),
        (
            "Risco de invalidação "
            "estrutural observado: "
            f"{invalidation.state}."
        ),
        (
            "Posição relativa do preço: "
            f"{position:.2f}%."
        ),
        (
            "Espaço até o limite inferior: "
            f"{range_assessment.distance_to_lower_percent:.2f}%."
        ),
        (
            "Espaço até o limite superior: "
            f"{range_assessment.distance_to_upper_percent:.2f}%."
        ),
    )

    return (
        AssetOperationalRangeConsolidatedContextAssessment(
            state=state,
            position_zone=position_zone,
            factors=factors,
        )
    )


def _positive_float(
    value,
) -> Optional[float]:
    if value is None:
        return None

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return None

    if (
        not math.isfinite(number)
        or number <= 0
    ):
        return None

    return number