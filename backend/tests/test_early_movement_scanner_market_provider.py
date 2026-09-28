import pytest

from app.early_movement.scanner import (
    CoinGeckoEarlyMovementScannerMarketProvider,
    EarlyMovementScannerDataError,
)


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload,
    ) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(
        self,
    ):
        return self._payload


def test_fetch_preserves_canonical_coin_id() -> None:
    captured = {}

    def fake_get(
        url,
        *,
        params,
        headers,
        timeout,
    ):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        captured["timeout"] = timeout

        return FakeResponse(
            status_code=200,
            payload=[
                {
                    "id": "bitcoin",
                    "symbol": "btc",
                    "name": "Bitcoin",
                    "current_price": 65000,
                    "market_cap": 1_200_000_000_000,
                    "total_volume": 30_000_000_000,
                    "price_change_percentage_24h": 2.5,
                    "market_cap_rank": 1,
                },
                {
                    "id": "uniswap",
                    "symbol": "uni",
                    "name": "Uniswap",
                    "current_price": 12.5,
                    "market_cap": 7_500_000_000,
                    "total_volume": 650_000_000,
                    "price_change_percentage_24h": 4.2,
                    "market_cap_rank": 25,
                },
            ],
        )

    provider = (
        CoinGeckoEarlyMovementScannerMarketProvider(
            asset_limit=100,
            request_get=fake_get,
        )
    )

    result = provider.fetch()

    assert len(result) == 2

    assert result[0].coin_id == "bitcoin"
    assert result[0].symbol == "BTC"
    assert result[0].market_cap_rank == 1

    assert result[1].coin_id == "uniswap"
    assert result[1].symbol == "UNI"
    assert result[1].total_volume == 650_000_000

    assert (
        captured["params"]["per_page"]
        == 100
    )

    assert (
        captured["params"]["order"]
        == "market_cap_desc"
    )


def test_fetch_skips_invalid_market_assets() -> None:
    def fake_get(
        url,
        *,
        params,
        headers,
        timeout,
    ):
        return FakeResponse(
            status_code=200,
            payload=[
                {
                    "id": "",
                    "symbol": "bad",
                    "name": "Invalid",
                    "current_price": 10,
                },
                {
                    "id": "no-price",
                    "symbol": "np",
                    "name": "No Price",
                    "current_price": None,
                },
                {
                    "id": "ethereum",
                    "symbol": "eth",
                    "name": "Ethereum",
                    "current_price": 3500,
                    "market_cap": 420_000_000_000,
                    "total_volume": 18_000_000_000,
                    "price_change_percentage_24h": -1.5,
                    "market_cap_rank": 2,
                },
            ],
        )

    provider = (
        CoinGeckoEarlyMovementScannerMarketProvider(
            request_get=fake_get,
        )
    )

    result = provider.fetch()

    assert len(result) == 1
    assert result[0].coin_id == "ethereum"


def test_fetch_rejects_rate_limit_response() -> None:
    def fake_get(
        url,
        *,
        params,
        headers,
        timeout,
    ):
        return FakeResponse(
            status_code=429,
            payload={},
        )

    provider = (
        CoinGeckoEarlyMovementScannerMarketProvider(
            request_get=fake_get,
        )
    )

    with pytest.raises(
        EarlyMovementScannerDataError,
        match="Limite temporário",
    ):
        provider.fetch()


def test_asset_limit_cannot_exceed_coingecko_page_limit() -> None:
    with pytest.raises(
        ValueError,
        match="entre 1 e 250",
    ):
        CoinGeckoEarlyMovementScannerMarketProvider(
            asset_limit=251,
        )