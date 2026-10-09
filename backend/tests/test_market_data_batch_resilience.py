from app.services import market_data_service

def test_batch_uses_stale_cache_when_provider_is_rate_limited(
    monkeypatch,
) -> None:
    market_data_service.market_cache.clear()

    stale_bitcoin = {
        "id": "bitcoin",
        "symbol": "btc",
        "current_price": 100,
    }

    market_data_service.market_cache[
        "bitcoin"
    ] = {
        "data": stale_bitcoin,
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

    result = (
        market_data_service.get_market_data_batch(
            [
                "bitcoin",
            ],
        )
    )

    assert result == {
        "bitcoin": stale_bitcoin,
    }

def test_batch_uses_stale_cache_on_request_exception(
    monkeypatch,
) -> None:
    market_data_service.market_cache.clear()

    stale_ethereum = {
        "id": "ethereum",
        "symbol": "eth",
        "current_price": 200,
    }

    market_data_service.market_cache[
        "ethereum"
    ] = {
        "data": stale_ethereum,
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

    result = (
        market_data_service.get_market_data_batch(
            [
                "ethereum",
            ],
        )
    )

    assert result == {
        "ethereum": stale_ethereum,
    }

def test_batch_populates_cache_for_all_returned_assets(
    monkeypatch,
) -> None:
    market_data_service.market_cache.clear()

    class FakeResponse:
        status_code = 200

        def json(self):
            return [
                {
                    "id": "bitcoin",
                    "current_price": 100,
                },
                {
                    "id": "ethereum",
                    "current_price": 200,
                },
                {
                    "id": "solana",
                    "current_price": 300,
                },
            ]

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

    market_data_service.get_market_data_batch(
        [
            "bitcoin",
            "ethereum",
            "solana",
        ]
    )

    assert market_data_service.get_cached(
        market_data_service.market_cache,
        "bitcoin",
        market_data_service.MARKET_TTL,
    )["current_price"] == 100

    assert market_data_service.get_cached(
        market_data_service.market_cache,
        "ethereum",
        market_data_service.MARKET_TTL,
    )["current_price"] == 200

    assert market_data_service.get_cached(
        market_data_service.market_cache,
        "solana",
        market_data_service.MARKET_TTL,
    )["current_price"] == 300

def test_chart_logs_provider_http_error(
    monkeypatch,
    caplog,
) -> None:
    coin_id = "test-chart-rate-limit"
    days = 1
    cache_key = f"{coin_id}_{days}"

    market_data_service.chart_cache.pop(
        cache_key,
        None,
    )

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

    assert result == {
        "prices": [],
    }

    assert "429" in caplog.text
    assert coin_id in caplog.text