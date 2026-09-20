import pytest

from app.ai.coingecko_market_overview_provider import (
    CoinGeckoMarketOverviewProvider,
    MarketOverviewDataError,
)


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code=200,
        payload=None,
    ):
        self.status_code = status_code
        self._payload = payload

    def json(
        self,
    ):
        return self._payload


def _global_payload():
    return {
        "data": {
            "total_market_cap": {
                "usd": 2_500_000_000_000,
            },
            "total_volume": {
                "usd": 120_000_000_000,
            },
            "market_cap_change_percentage_24h_usd":
                2.5,
            "market_cap_percentage": {
                "btc": 55.0,
                "eth": 12.0,
            },
        }
    }


def _markets_payload():
    return [
        {
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 100_000,
            "price_change_percentage_24h": 3.0,
            "market_cap": 2_000_000_000_000,
            "total_volume": 50_000_000_000,
        },
        {
            "symbol": "eth",
            "name": "Ethereum",
            "current_price": 4_000,
            "price_change_percentage_24h": -1.0,
            "market_cap": 480_000_000_000,
            "total_volume": 20_000_000_000,
        },
    ]


def _request_get(
    url,
    **kwargs,
):
    if url.endswith(
        "/global"
    ):
        return _FakeResponse(
            payload=_global_payload(),
        )

    return _FakeResponse(
        payload=_markets_payload(),
    )


def test_fetches_market_overview():
    provider = (
        CoinGeckoMarketOverviewProvider(
            request_get=_request_get,
        )
    )

    snapshot = provider.fetch()

    assert (
        snapshot.total_market_cap_usd
        == 2_500_000_000_000
    )

    assert (
        snapshot.total_volume_24h_usd
        == 120_000_000_000
    )

    assert (
        snapshot.market_cap_change_24h_percent
        == 2.5
    )

    assert (
        snapshot.btc_dominance_percent
        == 55.0
    )

    assert (
        snapshot.eth_dominance_percent
        == 12.0
    )


def test_fetches_major_assets():
    provider = (
        CoinGeckoMarketOverviewProvider(
            request_get=_request_get,
        )
    )

    snapshot = provider.fetch()

    assert len(
        snapshot.assets
    ) == 2

    assert (
        snapshot.assets[0].symbol
        == "BTC"
    )

    assert (
        snapshot.assets[1].symbol
        == "ETH"
    )


def test_counts_advancing_assets():
    provider = (
        CoinGeckoMarketOverviewProvider(
            request_get=_request_get,
        )
    )

    snapshot = provider.fetch()

    assert (
        snapshot.advancing_asset_count
        == 1
    )


def test_counts_declining_assets():
    provider = (
        CoinGeckoMarketOverviewProvider(
            request_get=_request_get,
        )
    )

    snapshot = provider.fetch()

    assert (
        snapshot.declining_asset_count
        == 1
    )


def test_rejects_invalid_timeout():
    with pytest.raises(
        ValueError
    ):
        CoinGeckoMarketOverviewProvider(
            timeout=0,
        )


def test_rejects_invalid_asset_limit():
    with pytest.raises(
        ValueError
    ):
        CoinGeckoMarketOverviewProvider(
            asset_limit=0,
        )


def test_rejects_rate_limit():
    def request_get(
        url,
        **kwargs,
    ):
        return _FakeResponse(
            status_code=429,
        )

    provider = (
        CoinGeckoMarketOverviewProvider(
            request_get=request_get,
        )
    )

    with pytest.raises(
        MarketOverviewDataError
    ):
        provider.fetch()


def test_rejects_incomplete_global_data():
    def request_get(
        url,
        **kwargs,
    ):
        if url.endswith(
            "/global"
        ):
            return _FakeResponse(
                payload={
                    "data": {},
                }
            )

        return _FakeResponse(
            payload=_markets_payload(),
        )

    provider = (
        CoinGeckoMarketOverviewProvider(
            request_get=request_get,
        )
    )

    with pytest.raises(
        MarketOverviewDataError
    ):
        provider.fetch()