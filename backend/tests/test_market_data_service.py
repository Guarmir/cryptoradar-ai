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