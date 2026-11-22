from app.ai.asset_operational_scenario_assessment import (
    AssetOperationalScenarioAssessment,
)
from app.ai.assistant_context import (
    AssistantContextItem,
)


_STATE_LABELS = {
    "bullish": "viés de alta",
    "bearish": "viés de baixa",
    "neutral": "cenário neutro",
    "conflicted": "cenário com sinais divergentes",
}

_STRENGTH_LABELS = {
    "strong": "forte",
    "moderate": "moderada",
    "weak": "fraca",
}

_FACTOR_LABELS = {
    "score_supports_upside": (
        "pontuação favorece a alta"
    ),
    "score_supports_downside": (
        "pontuação favorece a baixa"
    ),
    "price_change_supports_upside": (
        "variação de 24h favorece a alta"
    ),
    "price_change_supports_downside": (
        "variação de 24h favorece a baixa"
    ),
    "market_context_favorable": (
        "condições gerais do mercado favoráveis"
    ),
    "outperforming_btc": (
        "desempenho superior ao BTC"
    ),
    "range_quality_strong": (
        "faixa de preço com confirmação forte"
    ),
    "range_invalidation_low": (
        "baixo risco de perda da faixa de preço observada"
    ),
    "observed_risk_low": (
        "risco estimado em nível baixo"
    ),
}

_WARNING_LABELS = {
    "market_context_unfavorable": (
        "condições gerais do mercado desfavoráveis"
    ),
    "underperforming_btc": (
        "desempenho inferior ao BTC"
    ),
    "range_quality_weak": (
        "faixa de preço com confirmação fraca"
    ),
    "range_invalidation_high": (
        "risco elevado de perda da faixa de preço observada"
    ),
    "range_invalidated": (
        "faixa de preço observada não se mantém válida"
    ),
    "observed_risk_high": (
        "risco estimado em nível alto"
    ),
    "observed_risk_elevated": (
        "risco estimado em nível elevado"
    ),
}


def build_asset_operational_scenario_items(
    *,
    name: str,
    assessment: AssetOperationalScenarioAssessment,
) -> tuple[
    AssistantContextItem,
    ...,
]:
    state_label = _STATE_LABELS.get(
        assessment.state,
        assessment.state,
    )

    strength_label = _STRENGTH_LABELS.get(
        assessment.strength,
        assessment.strength,
    )

    scenario_item = AssistantContextItem(
        key="asset_operational_scenario",
        title="Cenário operacional",
        content=(
            f"A análise de {name} indica {state_label}, "
            f"com confirmação {strength_label}. "
            "A pontuação de direção é "
            f"{assessment.directional_score:+d}. "
            "Esse resultado descreve as condições "
            "observadas e não representa recomendação "
            "de compra ou venda."
        ),
    )

    support_item = AssistantContextItem(
        key="asset_operational_scenario_support",
        title="Fatores de confirmação",
        content=_build_factor_text(
            assessment.supporting_factors,
            labels=_FACTOR_LABELS,
            empty_text=(
                "Não foram identificados fatores "
                "adicionais de confirmação para "
                f"o cenário de {name}."
            ),
        ),
    )

    warning_item = AssistantContextItem(
        key="asset_operational_scenario_warnings",
        title="Alertas do cenário",
        content=_build_factor_text(
            assessment.warning_factors,
            labels=_WARNING_LABELS,
            empty_text=(
                "Não foram identificados alertas "
                "adicionais relevantes no cenário "
                f"de {name}."
            ),
        ),
    )

    return (
        scenario_item,
        support_item,
        warning_item,
    )


def _build_factor_text(
    factors: tuple[str, ...],
    *,
    labels: dict[str, str],
    empty_text: str,
) -> str:
    if not factors:
        return empty_text

    readable_factors = tuple(
        labels.get(
            factor,
            factor,
        )
        for factor in factors
    )

    return "; ".join(
        readable_factors
    ) + "."
