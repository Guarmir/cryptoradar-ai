from fastapi import FastAPI
import requests
import threading

from app.services.price_alert import monitor_price
from app.services.score import calculate_score

app = FastAPI(title="CryptoRadar AI")


@app.get("/")
def home():
    return {"status": "CryptoRadar AI online"}


@app.get("/price/{coin}")
def get_price(coin: str):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin, "vs_currencies": "usd"}
    response = requests.get(url, params=params)
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
