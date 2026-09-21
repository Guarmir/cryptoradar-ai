from app.ai.assistant_context import (
    AssistantContext,
    AssistantContextItem,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)


MARKET_OVERVIEW_SOURCE = (
    "cryptoradar_market_overview"
)

MARKET_OVERVIEW_VERSION = "v1"


def build_market_overview_context(
    snapshot: MarketOverviewSnapshot,
    *,
    mover_limit: int = 5,
) -> AssistantContext:
    if mover_limit < 1:
        raise ValueError(
            "mover_limit deve ser maior que zero."
        )

    items = (
        _build_global_market_item(
            snapshot,
        ),
        _build_market_breadth_item(
            snapshot,
        ),
        _build_major_assets_item(
            snapshot,
            mover_limit=mover_limit,
        ),
        _build_relevant_moves_item(
            snapshot,
            mover_limit=mover_limit,
        ),
    )

    return AssistantContext(
        intent=(
            AssistantIntent
            .MARKET_OVERVIEW
        ),
        source=(
            MARKET_OVERVIEW_SOURCE
        ),
        source_version=(
            MARKET_OVERVIEW_VERSION
        ),
        items=items,
    )


def _build_global_market_item(
    snapshot: MarketOverviewSnapshot,
) -> AssistantContextItem:
    eth_dominance = (
        (
            f"{snapshot.eth_dominance_percent:.2f}%"
        )
        if (
            snapshot.eth_dominance_percent
            is not None
        )
        else "indisponivel"
    )

    content = (
        "Capitalizacao total: "
        f"US$ {snapshot.total_market_cap_usd:,.0f}. "
        "Volume em 24h: "
        f"US$ {snapshot.total_volume_24h_usd:,.0f}. "
        "Variacao da capitalizacao em 24h: "
        f"{snapshot.market_cap_change_24h_percent:+.2f}%. "
        "Dominancia BTC: "
        f"{snapshot.btc_dominance_percent:.2f}%. "
        "Dominancia ETH: "
        f"{eth_dominance}."
    )

    return AssistantContextItem(
        key="global_market",
        title="Mercado global",
        content=content,
    )


def _build_market_breadth_item(
    snapshot: MarketOverviewSnapshot,
) -> AssistantContextItem:
    advancing = (
        snapshot.advancing_asset_count
    )

    declining = (
        snapshot.declining_asset_count
    )

    unchanged = (
        len(snapshot.assets)
        - advancing
        - declining
    )

    content = (
        "Na amostra observada, "
        f"{advancing} ativos estao em alta, "
        f"{declining} estao em queda e "
        f"{unchanged} estao sem variacao "
        "positiva ou negativa registrada."
    )

    return AssistantContextItem(
        key="market_breadth",
        title="Amplitude do mercado",
        content=content,
    )


def _build_major_assets_item(
    snapshot: MarketOverviewSnapshot,
    *,
    mover_limit: int,
) -> AssistantContextItem:
    selected = snapshot.assets[
        :mover_limit
    ]

    descriptions = [
        _format_asset(
            asset,
        )
        for asset in selected
    ]

    content = (
        "; ".join(
            descriptions,
        )
        if descriptions
        else "Nenhum ativo disponivel."
    )

    return AssistantContextItem(
        key="major_assets",
        title="Principais ativos observados",
        content=content,
    )


def _build_relevant_moves_item(
    snapshot: MarketOverviewSnapshot,
    *,
    mover_limit: int,
) -> AssistantContextItem:
    with_change = [
        asset
        for asset in snapshot.assets
        if (
            asset.change_24h_percent
            is not None
        )
    ]

    strongest = sorted(
        with_change,
        key=lambda asset: (
            asset.change_24h_percent
            or 0
        ),
        reverse=True,
    )[:mover_limit]

    weakest = sorted(
        with_change,
        key=lambda asset: (
            asset.change_24h_percent
            or 0
        ),
    )[:mover_limit]

    strongest_text = (
        ", ".join(
            _format_move(
                asset,
            )
            for asset in strongest
        )
        if strongest
        else "indisponivel"
    )

    weakest_text = (
        ", ".join(
            _format_move(
                asset,
            )
            for asset in weakest
        )
        if weakest
        else "indisponivel"
    )

    content = (
        "Maiores variacoes positivas: "
        f"{strongest_text}. "
        "Maiores variacoes negativas: "
        f"{weakest_text}."
    )

    return AssistantContextItem(
        key="relevant_moves",
        title="Movimentos relevantes",
        content=content,
    )


def _format_asset(
    asset: MarketOverviewAsset,
) -> str:
    change = asset.change_24h_percent

    change_text = (
        f"{change:+.2f}%"
        if change is not None
        else "variacao indisponivel"
    )

    return (
        f"{asset.symbol} "
        f"US$ {asset.price_usd:,.6f} "
        f"({change_text} em 24h)"
    )


def _format_move(
    asset: MarketOverviewAsset,
) -> str:
    change = (
        asset.change_24h_percent
        or 0
    )

    return (
        f"{asset.symbol} "
        f"{change:+.2f}%"
    )