import requests

def calculate_score(coin: str):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": coin
    }

    response = requests.get(url, params=params)
    data = response.json()

    if not data:
        return None

    c = data[0]

    price = c["current_price"]
    change_24h = c["price_change_percentage_24h"]
    volume = c["total_volume"]
    market_cap = c["market_cap"]
    high_24h = c["high_24h"]
    low_24h = c["low_24h"]

    score = 0

    # 🔹 1. Variação 24h (máx 30)
    if change_24h >= 5:
        score += 30
    elif change_24h > 0:
        score += 20
    else:
        score += 5

    # 🔹 2. Volume (máx 20)
    if volume > 10_000_000_000:
        score += 20
    elif volume > 1_000_000_000:
        score += 10

    # 🔹 3. Market Cap (máx 20)
    if market_cap > 100_000_000_000:
        score += 20
    elif market_cap > 10_000_000_000:
        score += 10

    # 🔹 4. Tendência de preço (máx 20)
    if high_24h and low_24h:
        range_24h = high_24h - low_24h
        if range_24h > 0:
            position = (price - low_24h) / range_24h
            if position > 0.7:
                score += 20
            elif position > 0.4:
                score += 10

    # 🔹 5. Volatilidade (máx 10)
    if high_24h and low_24h:
        volatility = (high_24h - low_24h) / price
        if volatility < 0.05:
            score += 10
        elif volatility < 0.10:
            score += 5

    # 🔹 Garantia 0–100
    score = min(score, 100)

    # 🔹 Sinal final
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
