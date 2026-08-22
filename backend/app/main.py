from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import threading
import time

from app.monitoring.monitoring_fastapi_lifecycle import (
    monitoring_lifespan,
)
from app.services.price_alert import monitor_price
from app.services.score import calculate_score

app = FastAPI(
    title="CryptoRadar AI",
    version="2.0.0",
    lifespan=monitoring_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COINGECKO_API = "https://api.coingecko.com/api/v3"

coin_list_cache = {
    "data": None,
    "timestamp": 0
}

market_cache = {}
chart_cache = {}

COIN_LIST_TTL = 60 * 60      # 1 hora
MARKET_TTL = 60              # 1 minuto
CHART_TTL = 60 * 5           # 5 minutos


def get_cached(cache_dict, key, ttl):
    item = cache_dict.get(key)
    if not item:
        return None

    if time.time() - item["timestamp"] > ttl:
        return None

    return item["data"]


def set_cached(cache_dict, key, data):
    cache_dict[key] = {
        "data": data,
        "timestamp": time.time()
    }


def get_coin_list():
    cached = coin_list_cache["data"]
    if cached and (time.time() - coin_list_cache["timestamp"] <= COIN_LIST_TTL):
        return cached

    url = f"{COINGECKO_API}/coins/list"

    try:
        response = requests.get(url, timeout=20)

        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Erro ao buscar lista de moedas.")

        data = response.json()
        coin_list_cache["data"] = data
        coin_list_cache["timestamp"] = time.time()
        return data

    except Exception:
        raise HTTPException(status_code=503, detail="Erro ao buscar lista de moedas.")
PREFERRED_COIN_IDS_BY_SYMBOL = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
}

def resolve_coin_id(user_input: str):
    query = user_input.strip().lower()

    if not query:
        return None

    preferred_coin_id = (
        PREFERRED_COIN_IDS_BY_SYMBOL.get(
            query
        )
    )

    if preferred_coin_id:
        return preferred_coin_id

    coins = get_coin_list()

    # 1. match exato por id
    for coin in coins:
        if coin["id"].lower() == query:
            return coin["id"]

    # 2. match exato por símbolo
    exact_symbol_matches = [
        coin
        for coin in coins
        if coin["symbol"].lower() == query
    ]

    if exact_symbol_matches:
        return exact_symbol_matches[0]["id"]

    # 3. match exato por nome
    for coin in coins:
        if coin["name"].lower() == query:
            return coin["id"]

    # 4. match parcial por id
    for coin in coins:
        if query in coin["id"].lower():
            return coin["id"]

    # 5. match parcial por nome
    for coin in coins:
        if query in coin["name"].lower():
            return coin["id"]

    return None


def get_market_data(coin_id: str):
    cached = get_cached(market_cache, coin_id, MARKET_TTL)
    if cached:
        return cached

    url = f"{COINGECKO_API}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": coin_id,
        "price_change_percentage": "24h"
    }

    try:
        response = requests.get(url, params=params, timeout=20)

        if response.status_code != 200:
            return None

        data = response.json()

        if not data:
            return None

        market = data[0]
        set_cached(market_cache, coin_id, market)
        return market

    except Exception:
        return None


def get_chart_data(coin_id: str, days: int):
    cache_key = f"{coin_id}_{days}"
    cached = get_cached(chart_cache, cache_key, CHART_TTL)
    if cached:
        return cached

    url = f"{COINGECKO_API}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "hourly" if days <= 7 else "daily"
    }

    try:
        response = requests.get(url, params=params, timeout=20)

        if response.status_code != 200:
            return {
                "prices": []
            }

        data = response.json()
        set_cached(chart_cache, cache_key, data)
        return data

    except Exception:
        return {
            "prices": []
        }


def safe_float(value):
    try:
        if value is None:
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def calculate_ai_score(change_24h, volume, market_cap):
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

    return max(0, min(100, round(score)))


def get_ai_signal(score):
    if score >= 70:
        return "bullish"
    if score >= 40:
        return "neutral"
    return "bearish"


def get_ai_confidence(score, market_cap, volume):
    confidence = score / 100

    if market_cap > 1_000_000_000 and volume > 50_000_000:
        confidence += 0.08

    confidence = max(0.45, min(0.95, confidence))
    return round(confidence, 2)


def generate_ai_analysis(score, change_24h, volume, market_cap):
    if score >= 70:
        summary = "O ativo apresenta cenário positivo no curto prazo, com força relativa acima da média."
        reasons = [
            "Score elevado em relação ao conjunto de fatores analisados",
            "Movimento recente favorável",
            "Boa atividade de mercado"
        ]
        risks = [
            "Possível correção após movimento de alta",
            "Volatilidade típica do mercado cripto"
        ]
        invalidation = "Perda de força compradora acompanhada de queda relevante no preço."

    elif score >= 40:
        summary = "O ativo está em zona de atenção, com sinais mistos e sem confirmação forte de direção."
        reasons = [
            "Score intermediário",
            "Mercado ainda indefinido",
            "Dados atuais não indicam força dominante"
        ]
        risks = [
            "Falta de confirmação de tendência",
            "Possível reversão rápida em caso de aumento de volatilidade"
        ]
        invalidation = "Movimento forte contra o cenário atual, com queda de score e redução de volume."

    else:
        summary = "O ativo apresenta fraqueza no curto prazo e exige cautela antes de qualquer decisão."
        reasons = [
            "Score baixo",
            "Pressão de mercado desfavorável",
            "Baixa confirmação de força compradora"
        ]
        risks = [
            "Continuação da queda",
            "Baixo interesse comprador no momento"
        ]
        invalidation = "Recuperação consistente de preço, volume e score acima da zona de atenção."

    return summary, reasons, risks, invalidation


@app.get("/analysis/{symbol}")
def get_analysis(symbol: str):
    coin_id = resolve_coin_id(symbol)

    if not coin_id:
        raise HTTPException(status_code=404, detail="Ativo não encontrado.")

    market = get_market_data(coin_id)

    if not market:
        raise HTTPException(status_code=503, detail="Dados de mercado indisponíveis.")

    price = safe_float(market.get("current_price"))
    market_cap = safe_float(market.get("market_cap"))
    volume = safe_float(market.get("total_volume"))
    change_24h = safe_float(market.get("price_change_percentage_24h"))

    score = calculate_ai_score(change_24h, volume, market_cap)
    signal = get_ai_signal(score)
    confidence = get_ai_confidence(score, market_cap, volume)

    summary, reasons, risks, invalidation = generate_ai_analysis(
        score,
        change_24h,
        volume,
        market_cap,
    )

    return {
        "symbol": market.get("symbol", symbol).upper(),
        "name": market.get("name", coin_id),
        "coin_id": coin_id,
        "price": price,
        "market_cap": market_cap,
        "volume": volume,
        "change_24h": change_24h,
        "score": score,
        "signal": signal,
        "confidence": confidence,
        "summary": summary,
        "reasons": reasons,
        "risks": risks,
        "invalidation": invalidation,
        "image": market.get("image"),
        "last_updated": market.get("last_updated"),
    }


def build_empty_asset_response(original_input: str, days: int = 1):
    return {
        "coin": original_input.upper(),
        "coin_id": None,
        "name": original_input.capitalize(),
        "score": None,
        "signal": "🔴",
        "price": None,
        "market_cap": None,
        "volume": None,
        "change_24h": None,
        "image": None,
        "last_updated": None,
        "days": days,
        "points": []
    }


@app.get("/")
def home():
    return {
        "status": "CryptoRadar AI online",
        "version": "2.0.0"
    }


@app.get("/price/{coin}")
def get_price(coin: str):
    coin_id = resolve_coin_id(coin)

    if not coin_id:
        return {
            "error": "Moeda não encontrada",
            "coin": coin.upper(),
            "coin_id": None,
            "price_usd": None
        }

    market = get_market_data(coin_id)

    if not market:
        return {
            "error": "Preço indisponível no momento",
            "coin": coin.upper(),
            "coin_id": coin_id,
            "price_usd": None
        }

    return {
        "coin": market.get("symbol", coin).upper(),
        "coin_id": market.get("id"),
        "name": market.get("name"),
        "price_usd": market.get("current_price")
    }


@app.get("/alert/{coin}/{price}")
def start_alert(coin: str, price: float):
    coin_id = resolve_coin_id(coin)

    if not coin_id:
        return {
            "error": "Moeda não encontrada"
        }

    thread = threading.Thread(
        target=monitor_price,
        args=(coin_id, price),
        daemon=True
    )
    thread.start()

    return {
        "status": "Alerta iniciado",
        "coin": coin.upper(),
        "coin_id": coin_id,
        "target_price": price
    }


@app.get("/score/{coin}")
def get_score(coin: str):
    coin_id = resolve_coin_id(coin)

    if not coin_id:
        return {
            "error": "Moeda não encontrada",
            **build_empty_asset_response(coin)
        }

    market = get_market_data(coin_id)

    if not market:
        return {
            "error": "Dados indisponíveis no momento. Tente novamente em instantes.",
            **build_empty_asset_response(coin)
        }

    score_result = calculate_score(coin_id)

    if isinstance(score_result, dict):
        score = score_result.get("score")
        signal = score_result.get("signal", "🔴")
    elif isinstance(score_result, (list, tuple)) and len(score_result) >= 2:
        score = score_result[0]
        signal = score_result[1]
    elif score_result is None:
        score = None
        signal = "🔴"
    else:
        score = None
        signal = "🔴"

    return {
        "coin": market.get("symbol", coin).upper(),
        "coin_id": market.get("id"),
        "name": market.get("name"),
        "score": score,
        "signal": signal,
        "price": market.get("current_price"),
        "market_cap": market.get("market_cap"),
        "volume": market.get("total_volume"),
        "change_24h": market.get("price_change_percentage_24h"),
        "image": market.get("image"),
        "last_updated": market.get("last_updated")
    }


@app.get("/chart/{coin}")
def get_chart(coin: str, days: int = 1):
    if days not in [1, 7]:
        raise HTTPException(status_code=400, detail="Use days=1 ou days=7.")

    coin_id = resolve_coin_id(coin)

    if not coin_id:
        return {
            "coin": coin.upper(),
            "coin_id": None,
            "days": days,
            "points": []
        }

    chart_data = get_chart_data(coin_id, days)
    prices = chart_data.get("prices", [])

    points = []
    for item in prices:
        if isinstance(item, list) and len(item) >= 2:
            points.append({
                "timestamp": item[0],
                "price": item[1]
            })

    return {
        "coin": coin.upper(),
        "coin_id": coin_id,
        "days": days,
        "points": points
    }


@app.get("/asset/{coin}")
def get_asset(coin: str, days: int = 1):
    if days not in [1, 7]:
        raise HTTPException(status_code=400, detail="Use days=1 ou days=7.")

    coin_id = resolve_coin_id(coin)

    if not coin_id:
        return {
            "error": "Moeda não encontrada",
            **build_empty_asset_response(coin, days)
        }

    market = get_market_data(coin_id)
    chart_data = get_chart_data(coin_id, days)

    if not market:
        return {
            "error": "Dados indisponíveis no momento. Tente novamente em instantes.",
            **build_empty_asset_response(coin, days)
        }

    score_result = calculate_score(coin_id)

    if isinstance(score_result, dict):
        score = score_result.get("score")
        signal = score_result.get("signal", "🔴")
    elif isinstance(score_result, (list, tuple)) and len(score_result) >= 2:
        score = score_result[0]
        signal = score_result[1]
    elif score_result is None:
        score = None
        signal = "🔴"
    else:
        score = None
        signal = "🔴"

    prices = chart_data.get("prices", [])
    points = []

    for item in prices:
        if isinstance(item, list) and len(item) >= 2:
            points.append({
                "timestamp": item[0],
                "price": item[1]
            })

    return {
        "coin": market.get("symbol", coin).upper(),
        "coin_id": market.get("id"),
        "name": market.get("name"),
        "score": score,
        "signal": signal,
        "price": market.get("current_price"),
        "market_cap": market.get("market_cap"),
        "volume": market.get("total_volume"),
        "change_24h": market.get("price_change_percentage_24h"),
        "image": market.get("image"),
        "last_updated": market.get("last_updated"),
        "days": days,
        "points": points
    }