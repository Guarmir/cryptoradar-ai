from app.services.market_data_service import (
    MARKET_TTL,
    get_cached,
    get_market_data_batch,
    market_cache,
)


DEFAULT_PREFETCH_COIN_IDS = (
    "bitcoin",
    "ethereum",
    "solana",
    "ripple",
    "cardano",
    "dogecoin",
)


def ensure_default_market_data(
    coin_id: str,
) -> None:
    if coin_id not in DEFAULT_PREFETCH_COIN_IDS:
        return

    cached = get_cached(
        market_cache,
        coin_id,
        MARKET_TTL,
    )

    if cached:
        return

    get_market_data_batch(
        list(
            DEFAULT_PREFETCH_COIN_IDS
        )
    )


def prefetch_default_market_data() -> None:
    get_market_data_batch(
        list(
            DEFAULT_PREFETCH_COIN_IDS
        )
    )