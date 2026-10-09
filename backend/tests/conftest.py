import pytest

from app.services import market_data_service
from app.services import coingecko_request_runtime
from app.services.coingecko_request_coordinator import (
    CoinGeckoRequestCoordinator,
)


@pytest.fixture(autouse=True)
def isolate_coingecko_coordinator(monkeypatch):
    coordinator = CoinGeckoRequestCoordinator(
        min_interval_seconds=0,
        cooldown_seconds=60,
    )

    monkeypatch.setattr(
        coingecko_request_runtime,
        "coingecko_request_coordinator",
        coordinator,
    )

    monkeypatch.setattr(
        market_data_service,
        "coingecko_request_coordinator",
        coordinator,
    )

    monkeypatch.setattr(
        "app.monitoring.coingecko_monitoring_market_data_provider."
        "coingecko_request_coordinator",
        coordinator,
    )

    monkeypatch.setattr(
        "app.early_movement.scanner.coingecko_scanner_market_provider."
        "coingecko_request_coordinator",
        coordinator,
    )