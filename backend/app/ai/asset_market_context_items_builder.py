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
            title="Cenário geral do mercado",
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
        title="Cenário geral do mercado",
        content=(
            "As informações sobre o BTC e o mercado geral "
            f"estão temporariamente indisponíveis para {name}. "
            "A análise utiliza apenas os dados disponíveis "
            "do próprio ativo."
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
        f"As condições gerais do mercado para {name} "
        f"apresentam um cenário {label}. Essa avaliação "
        "considera a variação do BTC em 24h, a mudança "
        "na capitalização total e a proporção de ativos "
        "em alta e em queda. É uma análise de contexto, "
        "não uma recomendação de compra ou venda."
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
            "A variação do BTC em 24h não está "
            "disponível no momento."
        )
    else:
        change_text = (
            "A variação do BTC em 24h é "
            f"{btc_change:+.2f}%."
        )

    return (
        f"{change_text} "
        "A participação atual do BTC no valor total "
        "do mercado é de "
        f"{assessment.btc_dominance_percent:.2f}%. "
        "Esse valor mostra a situação atual, mas, "
        "sem dados históricos comparáveis, não indica "
        "se a participação está aumentando ou diminuindo."
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
        "A capitalização total do mercado variou "
        f"{assessment.market_cap_change_24h_percent:+.2f}% "
        "nas últimas 24h. Entre os ativos avaliados, "
        f"{assessment.advancing_asset_count} estão em alta, "
        f"{assessment.declining_asset_count} em queda "
        "e "
        f"{assessment.unchanged_asset_count} sem "
        "variação positiva ou negativa registrada. "
        f"A participação dos ativos em alta e queda está {label}."
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
            f"Não foi possível comparar o desempenho de {name} "
            "com o BTC porque a variação do BTC em 24h "
            "está indisponível."
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
        f"Nas últimas 24h, {name} apresentou diferença "
        f"de {relative_change:+.2f} ponto(s) percentual(is) "
        "em relação ao BTC, com desempenho relativo "
        f"{label}."
    )
