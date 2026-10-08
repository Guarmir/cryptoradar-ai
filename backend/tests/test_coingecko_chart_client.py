from app.services.coingecko_chart_client import (
    CoinGeckoChartClient,
    CoinGeckoChartRequestError,
)


def test_client_fetches_chart():
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "prices": [[1, 10.0]],
            }

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout

        return FakeResponse()

    client = CoinGeckoChartClient(
        api_base_url="https://example.test",
        request_get=fake_get,
    )

    result = client.fetch(
        "bitcoin",
        7,
    )

    assert result == {
        "prices": [[1, 10.0]],
    }

    assert captured["url"] == (
        "https://example.test"
        "/coins/bitcoin/market_chart"
    )

    assert captured["params"] == {
        "vs_currency": "usd",
        "days": 7,
        "interval": "hourly",
    }

    assert captured["timeout"] == 20


def test_client_uses_daily_interval_for_long_period():
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"prices": []}

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        captured["params"] = params

        return FakeResponse()

    client = CoinGeckoChartClient(
        api_base_url="https://example.test",
        request_get=fake_get,
    )

    client.fetch(
        "bitcoin",
        30,
    )

    assert captured["params"]["interval"] == "daily"


def test_client_exposes_http_failure():
    class FakeResponse:
        status_code = 429

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        return FakeResponse()

    client = CoinGeckoChartClient(
        api_base_url="https://example.test",
        request_get=fake_get,
    )

    try:
        client.fetch(
            "bitcoin",
            7,
        )
    except CoinGeckoChartRequestError as exc:
        assert exc.coin_id == "bitcoin"
        assert exc.days == 7
        assert exc.status_code == 429
    else:
        raise AssertionError(
            "Era esperado erro HTTP."
        )

def test_client_exposes_non_rate_limit_http_failure():
    class FakeResponse:
        status_code = 500

    def fake_get(
        url,
        params=None,
        timeout=None,
    ):
        return FakeResponse()

    client = CoinGeckoChartClient(
        api_base_url="https://example.test",
        request_get=fake_get,
    )

    try:
        client.fetch(
            "ethereum",
            7,
        )
    except CoinGeckoChartRequestError as exc:
        assert exc.coin_id == "ethereum"
        assert exc.days == 7
        assert exc.status_code == 500
    else:
        raise AssertionError(
            "Era esperado erro HTTP."
        )