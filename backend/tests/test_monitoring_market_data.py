import unittest

from app.monitoring.coingecko_monitoring_market_data_provider import (
    CoinGeckoMonitoringMarketDataProvider,
    MonitoringMarketDataError,
)
from app.monitoring.monitoring_engine import MonitoringEngine
from app.monitoring.monitoring_market_data_provider import (
    MonitoringMarketDataProvider,
)
from app.monitoring.monitoring_service import MonitoringService
from app.monitoring.monitoring_target import MonitoringTarget


class _FakeResponse:
    def __init__(
        self,
        status_code,
        payload,
    ):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _RecordingRequestGet:
    def __init__(
        self,
        responses,
    ):
        self._responses = list(
            responses,
        )
        self.calls = []

    def __call__(
        self,
        url,
        *,
        params,
        headers,
        timeout,
    ):
        self.calls.append(
            {
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )

        if not self._responses:
            raise AssertionError(
                "Nenhuma resposta fake restante."
            )

        return self._responses.pop(0)


class _FakeMarketDataProvider(
    MonitoringMarketDataProvider
):
    def __init__(
        self,
        data_by_symbol,
    ):
        self.data_by_symbol = data_by_symbol
        self.fetch_count = 0

    def fetch_market_data(
        self,
        target,
    ):
        self.fetch_count += 1

        value = self.data_by_symbol[
            target.symbol
        ]

        if isinstance(value, list):
            if not value:
                raise AssertionError(
                    "Sem dados fake restantes."
                )

            return value.pop(0)

        return value


class CoinGeckoMonitoringMarketDataProviderTest(
    unittest.TestCase
):
    def test_uses_target_coin_id_without_search(self):
        request_get = _RecordingRequestGet(
            [
                _FakeResponse(
                    200,
                    [
                        {
                            "id": "bitcoin",
                            "symbol": "btc",
                            "current_price": 95000,
                        }
                    ],
                ),
            ]
        )

        provider = (
            CoinGeckoMonitoringMarketDataProvider(
                request_get=request_get,
            )
        )

        market_data = provider.fetch_market_data(
            MonitoringTarget(
                symbol="BTC",
                coin_id="bitcoin",
            )
        )

        self.assertEqual(
            market_data["current_price"],
            95000,
        )

        self.assertEqual(
            len(request_get.calls),
            1,
        )

        self.assertEqual(
            request_get.calls[0]["url"],
            provider.MARKETS_URL,
        )

        self.assertEqual(
            request_get.calls[0]["params"]["ids"],
            "bitcoin",
        )

    def test_resolves_symbol_then_fetches_market(self):
        request_get = _RecordingRequestGet(
            [
                _FakeResponse(
                    200,
                    {
                        "coins": [
                            {
                                "id": "unrelated",
                                "symbol": "other",
                                "name": "Other",
                            },
                            {
                                "id": "pippin",
                                "symbol": "pippin",
                                "name": "Pippin",
                            },
                        ],
                    },
                ),
                _FakeResponse(
                    200,
                    [
                        {
                            "id": "pippin",
                            "symbol": "pippin",
                            "current_price": 0.4285,
                            "total_volume": 150_000_000,
                        }
                    ],
                ),
            ]
        )

        provider = (
            CoinGeckoMonitoringMarketDataProvider(
                request_get=request_get,
            )
        )

        market_data = provider.fetch_market_data(
            MonitoringTarget(
                symbol="PIPPIN",
            )
        )

        self.assertEqual(
            len(request_get.calls),
            2,
        )

        self.assertEqual(
            request_get.calls[0]["url"],
            provider.SEARCH_URL,
        )

        self.assertEqual(
            request_get.calls[1]["url"],
            provider.MARKETS_URL,
        )

        self.assertEqual(
            request_get.calls[1]["params"]["ids"],
            "pippin",
        )

        self.assertEqual(
            market_data["current_price"],
            0.4285,
        )

    def test_caches_resolved_coin_id(self):
        request_get = _RecordingRequestGet(
            [
                _FakeResponse(
                    200,
                    {
                        "coins": [
                            {
                                "id": "ethereum",
                                "symbol": "eth",
                                "name": "Ethereum",
                            },
                        ],
                    },
                ),
                _FakeResponse(
                    200,
                    [
                        {
                            "id": "ethereum",
                            "current_price": 3200,
                        }
                    ],
                ),
                _FakeResponse(
                    200,
                    [
                        {
                            "id": "ethereum",
                            "current_price": 3232,
                        }
                    ],
                ),
            ]
        )

        provider = (
            CoinGeckoMonitoringMarketDataProvider(
                request_get=request_get,
            )
        )

        target = MonitoringTarget(
            symbol="ETH",
        )

        first = provider.fetch_market_data(
            target,
        )

        second = provider.fetch_market_data(
            target,
        )

        self.assertEqual(
            first["current_price"],
            3200,
        )

        self.assertEqual(
            second["current_price"],
            3232,
        )

        self.assertEqual(
            len(request_get.calls),
            3,
        )

        search_calls = [
            call
            for call in request_get.calls
            if call["url"] == provider.SEARCH_URL
        ]

        self.assertEqual(
            len(search_calls),
            1,
        )

    def test_raises_when_asset_is_not_found(self):
        request_get = _RecordingRequestGet(
            [
                _FakeResponse(
                    200,
                    {
                        "coins": [],
                    },
                ),
            ]
        )

        provider = (
            CoinGeckoMonitoringMarketDataProvider(
                request_get=request_get,
            )
        )

        with self.assertRaises(
            MonitoringMarketDataError
        ):
            provider.fetch_market_data(
                MonitoringTarget(
                    symbol="NOTFOUND",
                )
            )

    def test_raises_on_rate_limit(self):
        request_get = _RecordingRequestGet(
            [
                _FakeResponse(
                    429,
                    {},
                ),
            ]
        )

        provider = (
            CoinGeckoMonitoringMarketDataProvider(
                request_get=request_get,
            )
        )

        with self.assertRaises(
            MonitoringMarketDataError
        ):
            provider.fetch_market_data(
                MonitoringTarget(
                    symbol="BTC",
                )
            )


class MonitoringServiceTest(
    unittest.TestCase
):
    def test_runs_real_monitoring_flow_with_provider(self):
        provider = _FakeMarketDataProvider(
            {
                "PIPPIN": [
                    {
                        "current_price": 0.42,
                        "total_volume": 100_000_000,
                    },
                    {
                        "current_price": 0.4284,
                        "total_volume": 150_000_000,
                    },
                ],
            }
        )

        service = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider,
        )

        service.register_target(
            MonitoringTarget(
                symbol="PIPPIN",
            )
        )

        first = service.run_cycle(
            "PIPPIN",
        )

        second = service.run_cycle(
            "pippin",
        )

        self.assertTrue(
            first.is_first_observation,
        )

        self.assertEqual(
            first.current_price,
            0.42,
        )

        self.assertFalse(
            second.is_first_observation,
        )

        self.assertEqual(
            second.observation_count,
            2,
        )

        self.assertAlmostEqual(
            second.price_change_percent,
            2.0,
            places=6,
        )

        self.assertEqual(
            provider.fetch_count,
            2,
        )

    def test_preserves_futures_target_context(self):
        provider = _FakeMarketDataProvider(
            {
                "PIPPIN": {
                    "current_price": 0.43,
                },
            }
        )

        service = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider,
        )

        service.register_target(
            MonitoringTarget(
                symbol="PIPPIN",
                trading_mode="futures",
                has_open_position=True,
                position_side="long",
                entry_price=0.4285,
                leverage=10,
            )
        )

        result = service.run_cycle(
            "PIPPIN",
        )

        self.assertTrue(
            result.target.is_futures,
        )

        self.assertTrue(
            result.target.is_long,
        )

        self.assertEqual(
            result.target.entry_price,
            0.4285,
        )

        self.assertEqual(
            result.target.leverage,
            10,
        )

    def test_rejects_unregistered_target_before_fetch(self):
        provider = _FakeMarketDataProvider(
            {}
        )

        service = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider,
        )

        with self.assertRaises(KeyError):
            service.run_cycle(
                "BTC",
            )

        self.assertEqual(
            provider.fetch_count,
            0,
        )

    def test_remove_target_stops_future_cycles(self):
        provider = _FakeMarketDataProvider(
            {
                "BTC": {
                    "current_price": 95000,
                },
            }
        )

        service = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider,
        )

        service.register_target(
            MonitoringTarget(
                symbol="BTC",
            )
        )

        removed = service.remove_target(
            "btc",
        )

        self.assertTrue(
            removed,
        )

        self.assertEqual(
            service.target_count,
            0,
        )

        with self.assertRaises(KeyError):
            service.run_cycle(
                "BTC",
            )


if __name__ == "__main__":
    unittest.main()