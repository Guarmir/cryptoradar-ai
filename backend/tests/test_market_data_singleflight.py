"""Regressao das consultas simultaneas ao mercado CoinGecko."""

from concurrent.futures import ThreadPoolExecutor
import threading
import time

from app.services import market_data_service as market


class FakeResponse:
    status_code = 200

    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_consultas_simultaneas_do_mesmo_ativo_usam_uma_requisicao(monkeypatch):
    monkeypatch.setattr(market, "market_cache", {})
    monkeypatch.setattr(
        market.coingecko_request_coordinator,
        "execute",
        lambda request: request(),
    )
    calls = []
    gate = threading.Barrier(5)

    def fake_get(*args, **kwargs):
        calls.append(kwargs["params"]["ids"])
        time.sleep(0.05)
        return FakeResponse([{"id": "uniswap", "current_price": 5.0}])

    monkeypatch.setattr(market.requests, "get", fake_get)

    def query():
        gate.wait()
        return market.get_market_data("uniswap")

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: query(), range(5)))

    assert calls == ["uniswap"]
    assert all(result["current_price"] == 5.0 for result in results)


def test_consultas_simultaneas_da_lista_reutilizam_cache(monkeypatch):
    monkeypatch.setattr(
        market,
        "coin_list_cache",
        {"data": None, "timestamp": 0},
    )
    monkeypatch.setattr(
        market.coingecko_request_coordinator,
        "execute",
        lambda request: request(),
    )
    calls = []
    gate = threading.Barrier(5)

    def fake_get(*args, **kwargs):
        calls.append(args[0])
        time.sleep(0.05)
        return FakeResponse(
            [{"id": "uniswap", "symbol": "uni", "name": "Uniswap"}]
        )

    monkeypatch.setattr(market.requests, "get", fake_get)

    def query():
        gate.wait()
        return market.get_coin_list()

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: query(), range(5)))

    assert len(calls) == 1
    assert all(result[0]["id"] == "uniswap" for result in results)
