from dataclasses import dataclass
from typing import Optional

from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)


@dataclass(frozen=True)
class AssetMarketContextAssessment:
    state: str
    btc_state: str
    market_state: str
    breadth_state: str
    relative_strength_state: str

    btc_change_24h_percent: Optional[float]
    market_cap_change_24h_percent: float
    btc_dominance_percent: float

    advancing_asset_count: int
    declining_asset_count: int
    unchanged_asset_count: int

    relative_change_vs_btc_pp: Optional[float]

    factors: tuple[str, ...]


def calculate_asset_market_context(
    *,
    asset_change_24h_percent: float,
    snapshot: MarketOverviewSnapshot,
) -> AssetMarketContextAssessment:
    btc_asset = _find_btc_asset(
        snapshot
    )

    btc_change = (
        btc_asset.change_24h_percent
        if btc_asset is not None
        else None
    )

    btc_state = _direction_state(
        btc_change
    )

    market_state = _direction_state(
        snapshot.market_cap_change_24h_percent
    )

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

    breadth_state = _calculate_breadth_state(
        advancing=advancing,
        declining=declining,
    )

    relative_change = None
    relative_strength_state = "unavailable"

    if btc_change is not None:
        relative_change = (
            asset_change_24h_percent
            - btc_change
        )

        relative_strength_state = (
            _calculate_relative_strength_state(
                relative_change
            )
        )

    external_score = 0

    external_score += _state_score(
        btc_state
    )

    external_score += _state_score(
        market_state
    )

    external_score += _state_score(
        breadth_state
    )

    if external_score >= 2:
        state = "favorable"
    elif external_score <= -2:
        state = "unfavorable"
    else:
        state = "mixed"

    factors = [
        (
            "Variação da capitalização total "
            f"em 24h: "
            f"{snapshot.market_cap_change_24h_percent:+.2f}%."
        ),
        (
            "Amplitude observada: "
            f"{advancing} ativos em alta, "
            f"{declining} em queda e "
            f"{unchanged} sem direção positiva "
            "ou negativa registrada."
        ),
        (
            "Dominância atual do BTC: "
            f"{snapshot.btc_dominance_percent:.2f}%."
        ),
    ]

    if btc_change is None:
        factors.append(
            "Variação do BTC em 24h indisponível "
            "na amostra observada."
        )
    else:
        factors.append(
            "Variação do BTC em 24h: "
            f"{btc_change:+.2f}%."
        )

        factors.append(
            "Diferença do ativo em relação "
            "ao BTC em 24h: "
            f"{relative_change:+.2f} ponto(s) percentual(is)."
        )

    return AssetMarketContextAssessment(
        state=state,
        btc_state=btc_state,
        market_state=market_state,
        breadth_state=breadth_state,
        relative_strength_state=(
            relative_strength_state
        ),
        btc_change_24h_percent=btc_change,
        market_cap_change_24h_percent=(
            snapshot.market_cap_change_24h_percent
        ),
        btc_dominance_percent=(
            snapshot.btc_dominance_percent
        ),
        advancing_asset_count=advancing,
        declining_asset_count=declining,
        unchanged_asset_count=unchanged,
        relative_change_vs_btc_pp=(
            relative_change
        ),
        factors=tuple(factors),
    )


def _find_btc_asset(
    snapshot: MarketOverviewSnapshot,
) -> Optional[MarketOverviewAsset]:
    for asset in snapshot.assets:
        if asset.symbol.upper() == "BTC":
            return asset

    return None


def _direction_state(
    value: Optional[float],
) -> str:
    if value is None:
        return "unavailable"

    if value > 0.5:
        return "positive"

    if value < -0.5:
        return "negative"

    return "neutral"


def _calculate_breadth_state(
    *,
    advancing: int,
    declining: int,
) -> str:
    directional_total = (
        advancing
        + declining
    )

    if directional_total <= 0:
        return "balanced"

    advancing_ratio = (
        advancing
        / directional_total
    )

    if advancing_ratio >= 0.60:
        return "positive"

    if advancing_ratio <= 0.40:
        return "negative"

    return "balanced"


def _calculate_relative_strength_state(
    relative_change: float,
) -> str:
    if relative_change >= 1.0:
        return "outperforming"

    if relative_change <= -1.0:
        return "underperforming"

    return "aligned"


def _state_score(
    state: str,
) -> int:
    if state == "positive":
        return 1

    if state == "negative":
        return -1

    return 0