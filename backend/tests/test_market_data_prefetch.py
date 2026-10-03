from app.services import (
    market_data_prefetch,
)


def test_prefetch_default_market_data_uses_single_batch(
    monkeypatch,
) -> None:
    received_coin_ids = []

    def fake_batch(
        coin_ids,
    ):
        received_coin_ids.append(
            tuple(coin_ids)
        )

        return {}

    monkeypatch.setattr(
        market_data_prefetch,
        "get_market_data_batch",
        fake_batch,
    )

    market_data_prefetch.prefetch_default_market_data()

    assert received_coin_ids == [
        (
            "bitcoin",
            "ethereum",
            "solana",
            "ripple",
            "cardano",
            "dogecoin",
        )
    ]

def test_ensure_default_market_data_skips_batch_when_asset_is_cached(
    monkeypatch,
) -> None:
    market_data_prefetch.market_cache.clear()

    market_data_prefetch.market_cache[
        "bitcoin"
    ] = {
        "data": {
            "id": "bitcoin",
            "current_price": 100,
        },
        "timestamp": __import__(
            "time"
        ).time(),
    }

    batch_calls = []

    def fake_batch(
        coin_ids,
    ):
        batch_calls.append(
            tuple(coin_ids)
        )

        return {}

    monkeypatch.setattr(
        market_data_prefetch,
        "get_market_data_batch",
        fake_batch,
    )

    market_data_prefetch.ensure_default_market_data(
        "bitcoin"
    )

    assert batch_calls == []

def test_ensure_default_market_data_prefetches_group_when_cache_is_cold(
    monkeypatch,
) -> None:
    market_data_prefetch.market_cache.clear()

    batch_calls = []

    def fake_batch(
        coin_ids,
    ):
        batch_calls.append(
            tuple(coin_ids)
        )

        return {}

    monkeypatch.setattr(
        market_data_prefetch,
        "get_market_data_batch",
        fake_batch,
    )

    market_data_prefetch.ensure_default_market_data(
        "bitcoin"
    )

    assert batch_calls == [
        (
            "bitcoin",
            "ethereum",
            "solana",
            "ripple",
            "cardano",
            "dogecoin",
        )
    ]