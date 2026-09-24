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
    "conflicted": "cenário conflitante",
}

_STRENGTH_LABELS = {
    "strong": "forte",
    "moderate": "moderada",
    "weak": "fraca",
}

_FACTOR_LABELS = {
    "score_supports_upside": (
        "score favorece o lado positivo"
    ),
    "score_supports_downside": (
        "score favorece o lado negativo"
    ),
    "price_change_supports_upside": (
        "variação de 24h favorece o lado positivo"
    ),
    "price_change_supports_downside": (
        "variação de 24h favorece o lado negativo"
    ),
    "market_context_favorable": (
        "contexto externo de mercado favorável"
    ),
    "outperforming_btc": (
        "desempenho superior ao BTC"
    ),
    "range_quality_strong": (
        "faixa operacional com qualidade forte"
    ),
    "range_invalidation_low": (
        "baixo risco estrutural de invalidação da faixa"
    ),
    "observed_risk_low": (
        "Risk Score observado em nível baixo"
    ),
}

_WARNING_LABELS = {
    "market_context_unfavorable": (
        "contexto externo de mercado desfavorável"
    ),
    "underperforming_btc": (
        "desempenho inferior ao BTC"
    ),
    "range_quality_weak": (
        "faixa operacional com confirmação fraca"
    ),
    "range_invalidation_high": (
        "risco estrutural elevado de invalidação da faixa"
    ),
    "range_invalidated": (
        "faixa operacional observada invalidada"
    ),
    "observed_risk_high": (
        "Risk Score observado em nível alto"
    ),
    "observed_risk_elevated": (
        "Risk Score observado em nível elevado"
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
            f"O cenário operacional consolidado "
            f"de {name} apresenta {state_label}, "
            f"com confirmação {strength_label}. "
            f"A pontuação direcional V1 é "
            f"{assessment.directional_score:+d}. "
            "Essa leitura é observacional e não "
            "representa recomendação de compra "
            "ou venda."
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