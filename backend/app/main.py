from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import threading
import time

from app.services.price_alert import monitor_price
from app.services.score import calculate_score

app = FastAPI(title="CryptoRadar AI")

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

chart_cache = {}

COIN_LIST_TTL = 60 * 60   # 1 hora
CHART_TTL = 60 * 5        # 5 minutos


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
    response = requests.get(url, timeout=20)

    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="Erro ao buscar lista de moedas.")

    data = response.json()
    coin_list_cache["data"] = data
    coin_list_cache["timestamp"] = time.time()
    return data


def resolve_coin_id(user_input: str):
    query = user_input.strip().lower()
    coins = get_coin_list()

    # 1. match exato por id
    for coin in coins:
        if coin["id"].lower() == query:
            return coin["id"]

    # 2. match exato por símbolo
    exact_symbol_matches = [coin for coin in coins if coin["symbol"].lower() == query]
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
                "coin_id": coin_id,
                "days": days,
                "points": []
            }

        data = response.json()
        set_cached(chart_cache, cache_key, data)
        return data

    except Exception:
        return {
            "coin_id": coin_id,
            "days": days,
            "points": []
        }


@app.get("/")
def home():
    return {"status": "CryptoRadar AI online"}


@app.get("/price/{coin}")
def get_price(coin: str):
    coin_id = resolve_coin_id(coin)

    if not coin_id:
        return {"error": "Moeda não encontrada"}

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": "usd"}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    if coin_id not in data:
        return {"error": "Moeda não encontrada"}

    return {
        "coin": coin.upper(),
        "coin_id": coin_id,
        "price_usd": data[coin_id]["usd"]
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
            "error": "Moeda não encontrada"
        }

    result = calculate_score(coin_id)

    if result is None:
        return {
            "error": "Dados indisponíveis no momento. Tente novamente em instantes."
        }

    return result


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
        if len(item) >= 2:
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
