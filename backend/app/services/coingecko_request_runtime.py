
from app.services.coingecko_request_coordinator import (
    CoinGeckoRequestCoordinator,
)


coingecko_request_coordinator = (
    CoinGeckoRequestCoordinator(
        min_interval_seconds=2.0,
        cooldown_seconds=60.0,
    )
)
