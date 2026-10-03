from app.services import (
    market_data_service,
)


def test_resolves_preferred_aliases() -> None:
    assert (
        market_data_service.resolve_coin_id(
            "btc"
        )
        == "bitcoin"
    )

    assert (
        market_data_service.resolve_coin_id(
            "ETH"
        )
        == "ethereum"
    )

    assert (
        market_data_service.resolve_coin_id(
            "uni"
        )
        == "uniswap"
    )


def test_empty_coin_returns_none() -> None:
    assert (
        market_data_service.resolve_coin_id(
            "   "
        )
        is None
    )


def test_safe_float() -> None:
    assert (
        market_data_service.safe_float(
            "12.5"
        )
        == 12.5
    )

    assert (
        market_data_service.safe_float(
            None
        )
        == 0.0
    )

    assert (
        market_data_service.safe_float(
            "invalid"
        )
        == 0.0
    )


def test_cache_round_trip() -> None:
    cache = {}

    market_data_service.set_cached(
        cache,
        "btc",
        {
            "price": 100,
        },
    )

    result = (
        market_data_service.get_cached(
            cache,
            "btc",
            60,
        )
    )

    assert result == {
        "price": 100,
    }

def test_get_market_data_logs_provider_http_error(
    monkeypatch,
    caplog,
) -> None:
    coin_id = "test-provider-error"

    market_data_service.market_cache.pop(
        coin_id,
        None,
    )

    class FakeResponse:
        status_code = 429

        def json(self):
            return {
                "status": {
                    "error_code": 429,
                    "error_message": "Rate limit",
                },
            }

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        return FakeResponse()

    monkeypatch.setattr(
        market_data_service.requests,
        "get",
        fake_get,
    )

    result = market_data_service.get_market_data(
        coin_id,
    )

    assert result is None

    assert "429" in caplog.text

    assert coin_id in caplog.text

def test_get_market_data_uses_stale_cache_on_provider_failure(
    monkeypatch,
) -> None:
    coin_id = "test-stale-market"

    stale_market = {
        "id": coin_id,
        "symbol": "tsm",
        "name": "Test Stale Market",
        "current_price": 123.45,
    }

    market_data_service.market_cache[
        coin_id
    ] = {
        "data": stale_market,
        "timestamp": 0,
    }

    class FakeResponse:
        status_code = 429

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        return FakeResponse()

    monkeypatch.setattr(
        market_data_service.requests,
        "get",
        fake_get,
    )

    result = market_data_service.get_market_data(
        coin_id,
    )

    assert result == stale_market

def test_get_market_data_uses_stale_cache_on_request_exception(
    monkeypatch,
) -> None:
    coin_id = "test-stale-exception"

    stale_market = {
        "id": coin_id,
        "symbol": "tse",
        "name": "Test Stale Exception",
        "current_price": 456.78,
    }

    market_data_service.market_cache[
        coin_id
    ] = {
        "data": stale_market,
        "timestamp": 0,
    }

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        raise TimeoutError(
            "Provider timeout"
        )

    monkeypatch.setattr(
        market_data_service.requests,
        "get",
        fake_get,
    )

    result = market_data_service.get_market_data(
        coin_id,
    )

    assert result == stale_market

def test_get_chart_data_uses_stale_cache_on_provider_failure(
    monkeypatch,
) -> None:
    coin_id = "test-stale-chart"
    days = 1
    cache_key = f"{coin_id}_{days}"

    stale_chart = {
        "prices": [
            [1000, 10.0],
            [2000, 11.0],
        ],
    }

    market_data_service.chart_cache[
        cache_key
    ] = {
        "data": stale_chart,
        "timestamp": 0,
    }

    class FakeResponse:
        status_code = 429

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        return FakeResponse()

    monkeypatch.setattr(
        market_data_service.requests,
        "get",
        fake_get,
    )

    result = market_data_service.get_chart_data(
        coin_id,
        days,
    )

    assert result == stale_chart

def test_get_chart_data_uses_stale_cache_on_request_exception(
    monkeypatch,
) -> None:
    coin_id = "test-stale-chart-exception"
    days = 1
    cache_key = f"{coin_id}_{days}"

    stale_chart = {
        "prices": [
            [1000, 20.0],
            [2000, 21.0],
        ],
    }

    market_data_service.chart_cache[
        cache_key
    ] = {
        "data": stale_chart,
        "timestamp": 0,
    }

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        raise TimeoutError(
            "Provider timeout"
        )

    monkeypatch.setattr(
        market_data_service.requests,
        "get",
        fake_get,
    )

    result = market_data_service.get_chart_data(
        coin_id,
        days,
    )

    assert result == stale_chart

def test_get_market_data_batch_fetches_multiple_assets_in_one_request(
    monkeypatch,
) -> None:
    coin_ids = [
        "bitcoin",
        "ethereum",
        "solana",
    ]

    for coin_id in coin_ids:
        market_data_service.market_cache.pop(
            coin_id,
            None,
        )

    received_requests = []

    class FakeResponse:
        status_code = 200

        def json(self):
            return [
                {
                    "id": "bitcoin",
                    "symbol": "btc",
                    "current_price": 100,
                },
                {
                    "id": "ethereum",
                    "symbol": "eth",
                    "current_price": 200,
                },
                {
                    "id": "solana",
                    "symbol": "sol",
                    "current_price": 300,
                },
            ]

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        received_requests.append(
            {
                "url": url,
                "params": params,
            }
        )

        return FakeResponse()

    monkeypatch.setattr(
        market_data_service.requests,
        "get",
        fake_get,
    )

    result = (
        market_data_service.get_market_data_batch(
            coin_ids,
        )
    )

    assert len(received_requests) == 1

    assert received_requests[0]["params"][
        "ids"
    ] == "bitcoin,ethereum,solana"

    assert result["bitcoin"][
        "current_price"
    ] == 100

    assert result["ethereum"][
        "current_price"
    ] == 200

    assert result["solana"][
        "current_price"
    ] == 300

def test_get_market_data_batch_fetches_only_uncached_assets(
    monkeypatch,
) -> None:
    market_data_service.market_cache.clear()

    bitcoin = {
        "id": "bitcoin",
        "symbol": "btc",
        "current_price": 100,
    }

    ethereum = {
        "id": "ethereum",
        "symbol": "eth",
        "current_price": 200,
    }

    market_data_service.set_cached(
        market_data_service.market_cache,
        "bitcoin",
        bitcoin,
    )

    market_data_service.set_cached(
        market_data_service.market_cache,
        "ethereum",
        ethereum,
    )

    received_requests = []

    class FakeResponse:
        status_code = 200

        def json(self):
            return [
                {
                    "id": "solana",
                    "symbol": "sol",
                    "current_price": 300,
                },
            ]

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        received_requests.append(
            params,
        )

        return FakeResponse()

    monkeypatch.setattr(
        market_data_service.requests,
        "get",
        fake_get,
    )

    result = (
        market_data_service.get_market_data_batch(
            [
                "bitcoin",
                "ethereum",
                "solana",
            ],
        )
    )

    assert len(received_requests) == 1

    assert received_requests[0][
        "ids"
    ] == "solana"

    assert set(result) == {
        "bitcoin",
        "ethereum",
        "solana",
    }

def test_get_market_data_batch_makes_no_request_when_all_assets_are_cached(
    monkeypatch,
) -> None:
    market_data_service.market_cache.clear()

    bitcoin = {
        "id": "bitcoin",
        "symbol": "btc",
        "current_price": 100,
    }

    ethereum = {
        "id": "ethereum",
        "symbol": "eth",
        "current_price": 200,
    }

    market_data_service.set_cached(
        market_data_service.market_cache,
        "bitcoin",
        bitcoin,
    )

    market_data_service.set_cached(
        market_data_service.market_cache,
        "ethereum",
        ethereum,
    )

    request_count = 0

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        nonlocal request_count
        request_count += 1

        raise AssertionError(
            "CoinGecko nao deveria ser chamada."
        )

    monkeypatch.setattr(
        market_data_service.requests,
        "get",
        fake_get,
    )

    result = (
        market_data_service.get_market_data_batch(
            [
                "bitcoin",
                "ethereum",
            ],
        )
    )

    assert request_count == 0

    assert set(result) == {
        "bitcoin",
        "ethereum",
    }