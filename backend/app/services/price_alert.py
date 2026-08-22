import time
import requests

from app.services.score import resolve_coin, DEFAULT_HEADERS

COINGECKO_SIMPLE_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"


def monitor_price(coin_query: str, target_price: float, interval: int = 15):
    resolved = resolve_coin(coin_query)

    if not resolved or not resolved.get("id"):
        print("❌ Moeda não encontrada")
        return

    coin_id = resolved["id"]
    coin_name = resolved.get("name", coin_id)
    coin_symbol = str(resolved.get("symbol", coin_id)).upper()

    print(f"🔔 Alerta iniciado para {coin_name} ({coin_symbol}) | Alvo: ${target_price}")

    while True:
        try:
            response = requests.get(
                COINGECKO_SIMPLE_PRICE_URL,
                params={"ids": coin_id, "vs_currencies": "usd"},
                headers=DEFAULT_HEADERS,
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            if coin_id not in data or "usd" not in data[coin_id]:
                print("❌ Preço não disponível")
                time.sleep(interval)
                continue

            price = data[coin_id]["usd"]
            print(f"Preço atual: ${price}")

            if price >= target_price:
                print(f"🚨 ALERTA DISPARADO: {coin_name} ({coin_symbol}) atingiu ${price}")
                break

            time.sleep(interval)

        except Exception as e:
            print("Erro:", e)
            time.sleep(interval)