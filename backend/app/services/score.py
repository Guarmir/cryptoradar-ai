import requests

def calculate_score(coin: str):
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": coin
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data:
            return None

        c = data[0]

        price = c.get("current_price")
        change_24h = c.get("price_change_percentage_24h") or 0
        volume = c.get("total_volume") or 0
        market_cap = c.get("market_cap") or 0
        high_24h = c.get("high_24h")
        low_24h = c.get("low_24h")

        if price is None or price == 0:
            return None

        score = 0

        # 1️⃣ Variação 24h (máx 30)
        if change_24h >= 5:
            score += 30
        elif change_24h > 0:
            score += 20
        else:
            score += 5

        # 2️⃣ Volume (máx 20)
        if volume > 10_000_000_000:
            score += 20
        elif volume > 1_000_000_000:
            score += 10

        # 3️⃣ Market Cap (máx 20)
        if market_cap > 100_000_000_000:
            score += 20
        elif market_cap > 10_000_000_000:
            score += 10

        # 4️⃣ Tendência (máx 20)
        if high_24h and low_24h and high_24h > low_24h:
            position = (price - low_24h) / (high_24h - low_24h)
            if position > 0.7:
                score += 20
            elif position > 0.4:
                score += 10

        # 5️⃣ Volatilidade (máx 10)
        if high_24h and low_24h and price > 0:
            volatility = (high_24h - low_24h) / price
            if volatility < 0.05:
                score += 10
            elif volatility < 0.10:
                score += 5

        score = min(score, 100)

        if score >= 70:
            signal = "🟢 Forte oportunidade"
        elif score >= 40:
            signal = "🟡 Neutro / observar"
        else:
            signal = "🔴 Fraco / risco alto"

        return {
            "coin": coin,
            "price_usd": price,
            "change_24h": round(change_24h, 2),
            "volume_24h": volume,
            "market_cap": market_cap,
            "score": score,
            "signal": signal
        }

    except Exception as e:
        # Log simples para produção
        print("Erro no score:", e)
        return None
