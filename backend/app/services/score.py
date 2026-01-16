import requests
import time

CACHE = {}
CACHE_TTL = 300  # 5 minutos


def calculate_score(coin: str):
    coin = coin.lower()
    now = time.time()

    # 1️⃣ RETORNAR CACHE VÁLIDO
    if coin in CACHE:
        cached = CACHE[coin]
        if now - cached["timestamp"] < CACHE_TTL:
            return cached["data"]

    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": coin
        }

        response = requests.get(url, params=params, timeout=10)

        # 🚫 RATE LIMIT
        if response.status_code == 429:
            if coin in CACHE:
                return {
                    **CACHE[coin]["data"],
                    "cached": True,
                    "warning": "Dados temporariamente limitados. Usando cache."
                }
            return None

        response.raise_for_status()
        data = response.json()
        if not data:
            return None

        c = data[0]

        price = c.get("current_price")
        if not price:
            return None

        change_24h = c.get("price_change_percentage_24h") or 0
        volume = c.get("total_volume") or 0
        market_cap = c.get("market_cap") or 0
        high_24h = c.get("high_24h")
        low_24h = c.get("low_24h")

        score = 0

        # Variação
        if change_24h >= 5:
            score += 30
        elif change_24h > 0:
            score += 20
        else:
            score += 5

        # Volume
        if volume > 10_000_000_000:
            score += 20
        elif volume > 1_000_000_000:
            score += 10

        # Market cap
        if market_cap > 100_000_000_000:
            score += 20
        elif market_cap > 10_000_000_000:
            score += 10

        # Tendência
        if high_24h and low_24h and high_24h > low_24h:
            pos = (price - low_24h) / (high_24h - low_24h)
            if pos > 0.7:
                score += 20
            elif pos > 0.4:
                score += 10

        # Volatilidade
        if high_24h and low_24h:
            vol = (high_24h - low_24h) / price
            if vol < 0.05:
                score += 10
            elif vol < 0.10:
                score += 5

        score = min(score, 100)

        signal = (
            "🟢 Forte oportunidade" if score >= 70 else
            "🟡 Neutro / observar" if score >= 40 else
            "🔴 Fraco / risco alto"
        )

        result = {
            "coin": coin,
            "price_usd": price,
            "change_24h": round(change_24h, 2),
            "volume_24h": volume,
            "market_cap": market_cap,
            "score": score,
            "signal": signal,
            "cached": False
        }

        # 💾 SALVAR CACHE
        CACHE[coin] = {
            "data": {**result, "cached": True},
            "timestamp": now
        }

        return result

    except Exception as e:
        print("Erro no score:", e)
        if coin in CACHE:
            return CACHE[coin]["data"]
        return None
