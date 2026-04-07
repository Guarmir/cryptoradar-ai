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

chart_cache = {}
CHART_TTL = 60 * 5  # 5 minutos


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


def get_chart_data(coin: str, days: int):
    cache_key = f"{coin}_{days}"
    cached = get_cached(chart_cache, cache_key, CHART_TTL)
    if cached:
        return cached

    url = f"{COINGECKO_API}/coins/{coin}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "hourly" if days <= 7 else "daily"
    }

    response = requests.get(url, params=params, timeout=20)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Histórico não encontrado.")

    data = response.json()
    set_cached(chart_cache, cache_key, data)
    return data


@app.get("/")
def home():
    return {"status": "CryptoRadar AI online"}


@app.get("/price/{coin}")
def get_price(coin: str):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin, "vs_currencies": "usd"}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    if coin not in data:
        return {"error": "Moeda não encontrada"}

    return {
        "coin": coin,
        "price_usd": data[coin]["usd"]
    }


@app.get("/alert/{coin}/{price}")
def start_alert(coin: str, price: float):
    thread = threading.Thread(
        target=monitor_price,
        args=(coin, price),
        daemon=True
    )
    thread.start()

    return {
        "status": "Alerta iniciado",
        "coin": coin,
        "target_price": price
    }


@app.get("/score/{coin}")
def get_score(coin: str):
    result = calculate_score(coin)

    if result is None:
        return {
            "error": "Dados indisponíveis no momento. Tente novamente em instantes."
        }

    return result


@app.get("/chart/{coin}")
def get_chart(coin: str, days: int = 1):
    if days not in [1, 7]:
        raise HTTPException(status_code=400, detail="Use days=1 ou days=7.")

    chart_data = get_chart_data(coin, days)
    prices = chart_data.get("prices", [])

    if not prices:
        raise HTTPException(status_code=404, detail="Histórico não encontrado.")

    points = []
    for item in prices:
        if len(item) >= 2:
            points.append({
                "timestamp": item[0],
                "price": item[1]
            })

    return {
        "coin": coin.upper(),
        "days": days,
        "points": points
    }
