import time
import requests

def monitor_price(coin: str, target_price: float, interval: int = 15):
    print(f"🔔 Alerta iniciado para {coin.upper()} | Alvo: ${target_price}")

    while True:
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": coin, "vs_currencies": "usd"}
            response = requests.get(url, params=params)
            data = response.json()

            if coin not in data:
                print("❌ Moeda não encontrada")
                time.sleep(interval)
                continue

            price = data[coin]["usd"]
            print(f"Preço atual: ${price}")

            if price >= target_price:
                print(f"🚨 ALERTA DISPARADO: {coin.upper()} atingiu ${price}")
                break

            time.sleep(interval)

        except Exception as e:
            print("Erro:", e)
            time.sleep(interval)
