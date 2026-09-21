def calculate_ai_score(
    change_24h,
    volume,
    market_cap,
):
    score = 50

    if change_24h > 5:
        score += 15

    elif change_24h > 2:
        score += 10

    elif change_24h < -5:
        score -= 15

    elif change_24h < -2:
        score -= 8

    if volume > 1_000_000_000:
        score += 10

    elif volume > 100_000_000:
        score += 5

    elif volume < 10_000_000:
        score -= 10

    if market_cap > 10_000_000_000:
        score += 5

    elif market_cap < 50_000_000:
        score -= 8

    return max(
        0,
        min(
            100,
            round(score),
        ),
    )


def get_ai_signal(score):
    if score >= 70:
        return "bullish"

    if score >= 40:
        return "neutral"

    return "bearish"


def get_ai_confidence(
    score,
    market_cap,
    volume,
):
    confidence = score / 100

    if (
        market_cap > 1_000_000_000
        and volume > 50_000_000
    ):
        confidence += 0.08

    confidence = max(
        0.45,
        min(
            0.95,
            confidence,
        ),
    )

    return round(
        confidence,
        2,
    )


def generate_ai_analysis(
    score,
    change_24h,
    volume,
    market_cap,
):
    if score >= 70:
        summary = (
            "O ativo apresenta cenário "
            "positivo no curto prazo, "
            "com força relativa acima "
            "da média."
        )

        reasons = [
            (
                "Score elevado em relação "
                "ao conjunto de fatores "
                "analisados"
            ),
            "Movimento recente favorável",
            "Boa atividade de mercado",
        ]

        risks = [
            (
                "Possível correção após "
                "movimento de alta"
            ),
            (
                "Volatilidade típica do "
                "mercado cripto"
            ),
        ]

        invalidation = (
            "Perda de força compradora "
            "acompanhada de queda "
            "relevante no preço."
        )

    elif score >= 40:
        summary = (
            "O ativo está em zona de "
            "atenção, com sinais mistos "
            "e sem confirmação forte "
            "de direção."
        )

        reasons = [
            "Score intermediário",
            "Mercado ainda indefinido",
            (
                "Dados atuais não indicam "
                "força dominante"
            ),
        ]

        risks = [
            (
                "Falta de confirmação "
                "de tendência"
            ),
            (
                "Possível reversão rápida "
                "em caso de aumento de "
                "volatilidade"
            ),
        ]

        invalidation = (
            "Movimento forte contra o "
            "cenário atual, com queda "
            "de score e redução de volume."
        )

    else:
        summary = (
            "O ativo apresenta fraqueza "
            "no curto prazo e exige "
            "cautela antes de qualquer "
            "decisão."
        )

        reasons = [
            "Score baixo",
            (
                "Pressão de mercado "
                "desfavorável"
            ),
            (
                "Baixa confirmação de "
                "força compradora"
            ),
        ]

        risks = [
            "Continuação da queda",
            (
                "Baixo interesse comprador "
                "no momento"
            ),
        ]

        invalidation = (
            "Recuperação consistente de "
            "preço, volume e score acima "
            "da zona de atenção."
        )

    return (
        summary,
        reasons,
        risks,
        invalidation,
    )


def calculate_score_from_market(
    market: dict,
):
    price_change_24h = (
        market.get(
            "price_change_percentage_24h"
        )
        or 0
    )

    market_cap = (
        market.get("market_cap")
        or 0
    )

    total_volume = (
        market.get("total_volume")
        or 0
    )

    current_price = (
        market.get("current_price")
        or 0
    )

    score = 50

    if price_change_24h > 8:
        score += 20

    elif price_change_24h > 3:
        score += 12

    elif price_change_24h > 0:
        score += 6

    elif price_change_24h < -8:
        score -= 20

    elif price_change_24h < -3:
        score -= 12

    elif price_change_24h < 0:
        score -= 6

    if market_cap >= 10_000_000_000:
        score += 12

    elif market_cap >= 1_000_000_000:
        score += 8

    elif market_cap >= 100_000_000:
        score += 4

    else:
        score -= 3

    if total_volume >= 1_000_000_000:
        score += 10

    elif total_volume >= 100_000_000:
        score += 6

    elif total_volume >= 10_000_000:
        score += 3

    else:
        score -= 4

    if current_price > 0:
        score += 1

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    if score >= 70:
        signal = "🟢"

    elif score >= 40:
        signal = "🟡"

    else:
        signal = "🔴"

    return (
        score,
        signal,
    )


def build_empty_asset_response(
    original_input: str,
    days: int = 1,
):
    return {
        "coin": original_input.upper(),
        "coin_id": None,
        "name": (
            original_input.capitalize()
        ),
        "score": None,
        "signal": "🔴",
        "price": None,
        "market_cap": None,
        "volume": None,
        "change_24h": None,
        "image": None,
        "last_updated": None,
        "days": days,
        "points": [],
    }