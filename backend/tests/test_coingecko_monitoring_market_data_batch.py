from app.monitoring.coingecko_monitoring_market_data_provider import (
    CoinGeckoMonitoringMarketDataProvider,
)
from app.monitoring.monitoring_target import (
    MonitoringTarget,
)


def _target(
    *,
    symbol: str,
    coin_id: str,
) -> MonitoringTarget:
    return MonitoringTarget(
        symbol=symbol,
        coin_id=coin_id,
    )


def test_fetch_market_data_batch_uses_one_market_request() -> None:
    requests_received = []

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
        headers=None,
        timeout=None,
    ):
        requests_received.append(
            {
                "url": url,
                "params": params,
            }
        )

        return FakeResponse()

    provider = (
        CoinGeckoMonitoringMarketDataProvider(
            request_get=fake_get,
        )
    )

    result = provider.fetch_market_data_batch(
        [
            _target(
                symbol="BTC",
                coin_id="bitcoin",
            ),
            _target(
                symbol="ETH",
                coin_id="ethereum",
            ),
            _target(
                symbol="SOL",
                coin_id="solana",
            ),
        ]
    )

    assert len(requests_received) == 1

    assert requests_received[0][
        "url"
    ] == provider.MARKETS_URL

    assert requests_received[0][
        "params"
    ]["ids"] == (
        "bitcoin,ethereum,solana"
    )

    assert result["BTC"][
        "current_price"
    ] == 100

    assert result["ETH"][
        "current_price"
    ] == 200

    assert result["SOL"][
        "current_price"
    ] == 300