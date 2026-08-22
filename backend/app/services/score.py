import time
import requests

CACHE = {}
CACHE_TTL = 300  # 5 minutos

COINGECKO_SEARCH_URL = "https://api.coingecko.com/api/v3/search"
COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "CryptoRadar/1.0",
}

PREFERRED_COIN_IDS_BY_SYMBOL = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
}

def _get_cached(coin_key: str):
    now = time.time()
    cached = CACHE.get(coin_key)

    if not cached:
        return None

    if now - cached["timestamp"] < CACHE_TTL:
        return cached["data"]

    return None


def _set_cache(coin_key: str, data: dict):
    CACHE[coin_key] = {
        "data": data,
        "timestamp": time.time(),
    }


def resolve_coin(query: str):
    query = query.strip().lower()
    if not query:
        return None

    preferred_coin_id = (
    PREFERRED_COIN_IDS_BY_SYMBOL.get(
        query
    )
)

    if preferred_coin_id:
        return {
          "id": preferred_coin_id,
          "symbol": query,
          "name": None,
    }

    response = requests.get(
        COINGECKO_SEARCH_URL,
        params={"query": query},
        headers=DEFAULT_HEADERS,
        timeout=10,
    )

    if response.status_code == 429:
        return None

    response.raise_for_status()
    payload = response.json()

    coins = payload.get("coins", [])
    if not coins:
        return None

    exact_id = None
    exact_symbol = None
    exact_name = None

    for coin in coins:
        coin_id = str(coin.get("id", "")).lower()
        symbol = str(coin.get("symbol", "")).lower()
        name = str(coin.get("name", "")).lower()

        if coin_id == query:
            exact_id = coin
            break

        if symbol == query and exact_symbol is None:
            exact_symbol = coin

        if name == query and exact_name is None:
            exact_name = coin

    selected = exact_id or exact_symbol or exact_name or coins[0]

    return {
        "id": selected.get("id"),
        "symbol": selected.get("symbol"),
        "name": selected.get("name"),
    }


def calculate_score(coin_query: str):
    coin_query = coin_query.strip().lower()
    if not coin_query:
        return None

    cached = _get_cached(coin_query)
    if cached:
        return {**cached, "cached": True}

    try:
        resolved = resolve_coin(coin_query)
        if not resolved or not resolved.get("id"):
            return None

        coin_id = resolved["id"]

        market_response = requests.get(
            COINGECKO_MARKETS_URL,
            params={
                "vs_currency": "usd",
                "ids": coin_id,
            },
            headers=DEFAULT_HEADERS,
            timeout=10,
        )

        if market_response.status_code == 429:
            fallback = _get_cached(coin_query)
            if fallback:
                return {
                    **fallback,
                    "cached": True,
                    "warning": "Rate limit temporário. Retornando dados em cache.",
                }
            return None

        market_response.raise_for_status()
        data = market_response.json()

        if not data:
            return None

        c = data[0]

        price = c.get("current_price")
        if price is None or price <= 0:
            return None

        change_24h = c.get("price_change_percentage_24h") or 0
        volume = c.get("total_volume") or 0
        market_cap = c.get("market_cap") or 0
        high_24h = c.get("high_24h")
        low_24h = c.get("low_24h")

        score = 0

        # Movimento de preço em 24h
        if change_24h >= 8:
            score += 30
        elif change_24h >= 3:
            score += 22
        elif change_24h > 0:
            score += 15
        elif change_24h > -5:
            score += 8
        else:
            score += 3

        # Volume
        if volume > 10_000_000_000:
            score += 20
        elif volume > 1_000_000_000:
            score += 14
        elif volume > 100_000_000:
            score += 8

        # Market cap
        if market_cap > 100_000_000_000:
            score += 20
        elif market_cap > 10_000_000_000:
            score += 14
        elif market_cap > 1_000_000_000:
            score += 8

        # Posição no range do dia
        if high_24h and low_24h and high_24h > low_24h:
            pos = (price - low_24h) / (high_24h - low_24h)
            if pos > 0.7:
                score += 15
            elif pos > 0.4:
                score += 8

        # Volatilidade diária
        if high_24h and low_24h and price > 0:
            vol = (high_24h - low_24h) / price
            if vol < 0.05:
                score += 10
            elif vol < 0.10:
                score += 5

        score = min(max(score, 0), 100)

        signal = (
            "🟢 Mercado forte"
            if score >= 70
            else "🟡 Mercado moderado"
            if score >= 40
            else "🔴 Mercado fraco"
        )

        result = {
            "coin_query": coin_query,
            "coin_id": coin_id,
            "coin_name": c.get("name"),
            "coin_symbol": str(c.get("symbol", "")).upper(),
            "price_usd": round(float(price), 6),
            "change_24h": round(float(change_24h), 2),
            "volume_24h": volume,
            "market_cap": market_cap,
            "high_24h": high_24h,
            "low_24h": low_24h,
            "score": score,
            "signal": signal,
            "cached": False,
        }

        _set_cache(coin_query, result)

        return result

    except Exception as e:
        print("Erro no score:", e)

        fallback = _get_cached(coin_query)
        if fallback:
            return {
                **fallback,
                "cached": True,
                "warning": "Falha temporária. Retornando dados em cache.",
            }

        return None