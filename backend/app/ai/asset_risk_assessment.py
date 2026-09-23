from dataclasses import dataclass


@dataclass(frozen=True)
class AssetRiskAssessment:
    score: int
    level: str
    market_cap_component: int
    liquidity_component: int
    volatility_component: int
    factors: tuple[str, ...]


def calculate_asset_risk_assessment(
    *,
    change_24h: float,
    volume: float,
    market_cap: float,
) -> AssetRiskAssessment:
    market_cap_risk = (
        _market_cap_risk(
            market_cap
        )
    )

    liquidity_risk = (
        _liquidity_risk(
            volume=volume,
            market_cap=market_cap,
        )
    )

    volatility_risk = (
        _volatility_risk(
            change_24h
        )
    )

    score = round(
        (
            market_cap_risk * 0.40
            + liquidity_risk * 0.35
            + volatility_risk * 0.25
        )
    )

    score = max(
        0,
        min(100, score),
    )

    level = _risk_level(
        score
    )

    volume_market_cap_ratio = (
        volume / market_cap
        if market_cap > 0
        else 0.0
    )

    factors = (
        _market_cap_factor(
            market_cap
        ),
        _liquidity_factor(
            volume_market_cap_ratio
        ),
        _volatility_factor(
            change_24h
        ),
    )

    return AssetRiskAssessment(
        score=score,
        level=level,
        market_cap_component=(
            market_cap_risk
        ),
        liquidity_component=(
            liquidity_risk
        ),
        volatility_component=(
            volatility_risk
        ),
        factors=factors,
    )


def _market_cap_risk(
    market_cap: float,
) -> int:
    if market_cap >= 50_000_000_000:
        return 10

    if market_cap >= 10_000_000_000:
        return 20

    if market_cap >= 2_000_000_000:
        return 35

    if market_cap >= 500_000_000:
        return 50

    if market_cap >= 100_000_000:
        return 70

    return 90


def _liquidity_risk(
    *,
    volume: float,
    market_cap: float,
) -> int:
    if (
        volume <= 0
        or market_cap <= 0
    ):
        return 90

    ratio = (
        volume / market_cap
    )

    if ratio >= 0.20:
        return 15

    if ratio >= 0.10:
        return 25

    if ratio >= 0.05:
        return 40

    if ratio >= 0.02:
        return 60

    if ratio >= 0.01:
        return 75

    return 90


def _volatility_risk(
    change_24h: float,
) -> int:
    absolute_change = abs(
        change_24h
    )

    if absolute_change < 2:
        return 15

    if absolute_change < 5:
        return 30

    if absolute_change < 10:
        return 50

    if absolute_change < 20:
        return 70

    return 90


def _risk_level(
    score: int,
) -> str:
    if score < 25:
        return "baixo"

    if score < 50:
        return "moderado"

    if score < 75:
        return "alto"

    return "muito alto"


def _market_cap_factor(
    market_cap: float,
) -> str:
    if market_cap >= 50_000_000_000:
        return (
            "Capitalização muito elevada "
            "reduz o componente de risco."
        )

    if market_cap >= 10_000_000_000:
        return (
            "Capitalização elevada reduz "
            "o componente de risco."
        )

    if market_cap >= 2_000_000_000:
        return (
            "Capitalização intermediária "
            "mantém risco moderado."
        )

    if market_cap >= 500_000_000:
        return (
            "Capitalização relativamente "
            "baixa aumenta o risco."
        )

    return (
        "Capitalização baixa aumenta "
        "significativamente o risco."
    )


def _liquidity_factor(
    ratio: float,
) -> str:
    percentage = (
        ratio * 100
    )

    if ratio >= 0.10:
        return (
            "Relação volume/capitalização "
            f"de {percentage:.2f}% indica "
            "boa atividade relativa."
        )

    if ratio >= 0.05:
        return (
            "Relação volume/capitalização "
            f"de {percentage:.2f}% indica "
            "atividade relativa moderada."
        )

    return (
        "Relação volume/capitalização "
        f"de {percentage:.2f}% indica "
        "atividade relativa limitada."
    )


def _volatility_factor(
    change_24h: float,
) -> str:
    absolute_change = abs(
        change_24h
    )

    if absolute_change < 2:
        return (
            "Movimento de 24h está "
            "relativamente contido."
        )

    if absolute_change < 5:
        return (
            "Movimento de 24h apresenta "
            "volatilidade moderada."
        )

    if absolute_change < 10:
        return (
            "Movimento de 24h apresenta "
            "volatilidade relevante."
        )

    return (
        "Movimento de 24h apresenta "
        "volatilidade elevada."
    )