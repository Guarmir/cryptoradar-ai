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