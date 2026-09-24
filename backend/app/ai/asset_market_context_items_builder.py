from app.ai.asset_market_context_assessment import (
    AssetMarketContextAssessment,
    calculate_asset_market_context,
)
from app.ai.assistant_context import (
    AssistantContextItem,
)
from app.ai.market_overview_snapshot import (
    MarketOverviewSnapshot,
)


def build_asset_market_context_items(
    *,
    name: str,
    asset_change_24h_percent: float,
    snapshot: MarketOverviewSnapshot,
) -> tuple[
    AssistantContextItem,
    ...,
]:
    assessment = calculate_asset_market_context(
        asset_change_24h_percent=(
            asset_change_24h_percent
        ),
        snapshot=snapshot,
    )

    return (
        AssistantContextItem(
            key="asset_market_context",
            title="Contexto externo do mercado",
            content=_build_context_text(
                name=name,
                assessment=assessment,
            ),
        ),
        AssistantContextItem(
            key="asset_market_btc",
            title="Contexto do BTC",
            content=_build_btc_text(
                assessment=assessment,
            ),
        ),
        AssistantContextItem(
            key="asset_market_breadth",
            title="Amplitude do mercado",
            content=_build_breadth_text(
                assessment=assessment,
            ),
        ),
        AssistantContextItem(
            key="asset_relative_strength",
            title="Força relativa ao BTC",
            content=_build_relative_strength_text(
                name=name,
                assessment=assessment,
            ),
        ),
    )


def build_asset_market_context_unavailable_item(
    *,
    name: str,
) -> AssistantContextItem:
    return AssistantContextItem(
        key="asset_market_context",
        title="Contexto externo do mercado",
        content=(
            "O contexto BTC/mercado geral está "
            f"indisponível no momento para {name}. "
            "A análise permanece baseada nos dados "
            "próprios do ativo."
        ),
    )


def _build_context_text(
    *,
    name: str,
    assessment: AssetMarketContextAssessment,
) -> str:
    labels = {
        "favorable": "favorável",
        "mixed": "misto",
        "unfavorable": "desfavorável",
    }

    label = labels.get(
        assessment.state,
        assessment.state,
    )

    return (
        f"O contexto externo observado para {name} "
        f"está {label}. A leitura combina o "
        "comportamento do BTC em 24h, a variação "
        "da capitalização total e a amplitude da "
        "amostra de mercado. Essa leitura é "
        "contextual e não representa recomendação "
        "de compra ou venda."
    )


def _build_btc_text(
    *,
    assessment: AssetMarketContextAssessment,
) -> str:
    btc_change = (
        assessment.btc_change_24h_percent
    )

    if btc_change is None:
        change_text = (
            "A variação do BTC em 24h está "
            "indisponível na amostra observada."
        )
    else:
        change_text = (
            "A variação do BTC em 24h é "
            f"{btc_change:+.2f}%."
        )

    return (
        f"{change_text} "
        "A dominância atual do BTC é "
        f"{assessment.btc_dominance_percent:.2f}%. "
        "A dominância é usada como fotografia "
        "atual; sem série histórica, não é "
        "interpretada como subida ou queda."
    )


def _build_breadth_text(
    *,
    assessment: AssetMarketContextAssessment,
) -> str:
    labels = {
        "positive": "majoritariamente positiva",
        "balanced": "equilibrada",
        "negative": "majoritariamente negativa",
    }

    label = labels.get(
        assessment.breadth_state,
        assessment.breadth_state,
    )

    return (
        "A capitalização total varia "
        f"{assessment.market_cap_change_24h_percent:+.2f}% "
        "em 24h. Na amostra observada, "
        f"{assessment.advancing_asset_count} ativos "
        "estão em alta, "
        f"{assessment.declining_asset_count} em queda "
        "e "
        f"{assessment.unchanged_asset_count} sem "
        "direção positiva ou negativa registrada. "
        f"A amplitude está {label}."
    )


def _build_relative_strength_text(
    *,
    name: str,
    assessment: AssetMarketContextAssessment,
) -> str:
    relative_change = (
        assessment.relative_change_vs_btc_pp
    )

    if relative_change is None:
        return (
            f"A força relativa de {name} frente ao BTC "
            "não pode ser calculada porque a variação "
            "do BTC em 24h está indisponível."
        )

    labels = {
        "outperforming": "superior",
        "aligned": "alinhado",
        "underperforming": "inferior",
    }

    label = labels.get(
        assessment.relative_strength_state,
        assessment.relative_strength_state,
    )

    return (
        f"{name} está {relative_change:+.2f} ponto(s) "
        "percentual(is) em relação ao BTC na janela "
        f"de 24h, com desempenho relativo {label} "
        "pelas regras V1 do backend."
    )