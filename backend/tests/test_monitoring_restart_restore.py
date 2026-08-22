import unittest

from app.monitoring.in_memory_monitoring_state_store import (
    InMemoryMonitoringStateStore,
)
from app.monitoring.monitoring_engine import MonitoringEngine
from app.monitoring.monitoring_market_data_provider import (
    MonitoringMarketDataProvider,
)
from app.monitoring.monitoring_service import MonitoringService
from app.monitoring.monitoring_target import MonitoringTarget


class _SequenceMarketDataProvider(
    MonitoringMarketDataProvider
):
    def __init__(
        self,
        data_by_symbol,
    ):
        self._data_by_symbol = data_by_symbol

    def fetch_market_data(
        self,
        target,
    ):
        values = self._data_by_symbol[
            target.symbol
        ]

        if not values:
            raise AssertionError(
                "Sem observações fake restantes."
            )

        return values.pop(0)


class MonitoringRestartRestoreTest(
    unittest.TestCase
):
    def test_restores_and_continues_observation_count(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        provider_a = _SequenceMarketDataProvider(
            {
                "PIPPIN": [
                    {
                        "current_price": 0.42,
                    },
                    {
                        "current_price": 0.4284,
                    },
                ],
            }
        )

        server_a = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider_a,
            state_store=store,
        )

        server_a.register_target(
            MonitoringTarget(
                symbol="PIPPIN",
                coin_id="pippin",
                trading_mode="futures",
                has_open_position=True,
                position_side="long",
                entry_price=0.4285,
                leverage=10,
            )
        )

        first = server_a.run_cycle(
            "PIPPIN",
        )

        second = server_a.run_cycle(
            "PIPPIN",
        )

        self.assertEqual(
            first.observation_count,
            1,
        )

        self.assertEqual(
            second.observation_count,
            2,
        )

        persisted = store.load_state(
            "PIPPIN",
        )

        self.assertIsNotNone(
            persisted,
        )

        self.assertEqual(
            persisted.observation_count,
            2,
        )

        self.assertEqual(
            persisted.previous_price,
            0.42,
        )

        self.assertEqual(
            persisted.current_price,
            0.4284,
        )

        provider_b = _SequenceMarketDataProvider(
            {
                "PIPPIN": [
                    {
                        "current_price": 0.43,
                    },
                ],
            }
        )

        server_b = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider_b,
            state_store=store,
        )

        restored_states = (
            server_b.restore_from_store()
        )

        self.assertEqual(
            len(restored_states),
            1,
        )

        self.assertEqual(
            server_b.target_count,
            1,
        )

        restored = server_b.state_for(
            "pippin",
        )

        self.assertIsNotNone(
            restored,
        )

        self.assertEqual(
            restored.observation_count,
            2,
        )

        self.assertTrue(
            restored.target.is_long,
        )

        self.assertEqual(
            restored.target.entry_price,
            0.4285,
        )

        self.assertEqual(
            restored.target.leverage,
            10,
        )

        third = server_b.run_cycle(
            "PIPPIN",
        )

        self.assertEqual(
            third.observation_count,
            3,
        )

        self.assertEqual(
            third.previous_price,
            0.4284,
        )

        self.assertEqual(
            third.current_price,
            0.43,
        )

        persisted_after_restart = (
            store.load_state(
                "PIPPIN",
            )
        )

        self.assertEqual(
            persisted_after_restart.observation_count,
            3,
        )

        self.assertEqual(
            persisted_after_restart.current_price,
            0.43,
        )

    def test_registration_is_persisted_before_first_cycle(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        provider = _SequenceMarketDataProvider(
            {
                "BTC": [],
            }
        )

        service = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider,
            state_store=store,
        )

        service.register_target(
            MonitoringTarget(
                symbol="BTC",
                coin_id="bitcoin",
            )
        )

        persisted = store.load_state(
            "BTC",
        )

        self.assertIsNotNone(
            persisted,
        )

        self.assertEqual(
            persisted.target.symbol,
            "BTC",
        )

        self.assertEqual(
            persisted.target.coin_id,
            "bitcoin",
        )

        self.assertEqual(
            persisted.observation_count,
            0,
        )

    def test_remove_deletes_persisted_state(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        provider = _SequenceMarketDataProvider(
            {
                "ETH": [],
            }
        )

        service = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider,
            state_store=store,
        )

        service.register_target(
            MonitoringTarget(
                symbol="ETH",
            )
        )

        self.assertIsNotNone(
            store.load_state(
                "ETH",
            )
        )

        removed = service.remove_target(
            "eth",
        )

        self.assertTrue(
            removed,
        )

        self.assertIsNone(
            store.load_state(
                "ETH",
            )
        )

    def test_clear_removes_memory_and_persistence(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        provider = _SequenceMarketDataProvider(
            {
                "BTC": [],
                "ETH": [],
            }
        )

        service = MonitoringService(
            engine=MonitoringEngine(),
            market_data_provider=provider,
            state_store=store,
        )

        service.register_target(
            MonitoringTarget(
                symbol="BTC",
            )
        )

        service.register_target(
            MonitoringTarget(
                symbol="ETH",
            )
        )

        self.assertEqual(
            len(
                store.load_all()
            ),
            2,
        )

        service.clear()

        self.assertEqual(
            service.target_count,
            0,
        )

        self.assertEqual(
            store.load_all(),
            (),
        )

    def test_service_without_store_keeps_previous_behavior(
        self,
    ):
        provider = _SequenceMarketDataProvider(
            {
                "BTC": [
                    {
                        "current_price": 95000,
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
                symbol="BTC",
            )
        )

        restored = service.restore_from_store()

        self.assertEqual(
            restored,
            (),
        )

        result = service.run_cycle(
            "BTC",
        )

        self.assertEqual(
            result.observation_count,
            1,
        )

        self.assertEqual(
            result.current_price,
            95000,
        )


if __name__ == "__main__":
    unittest.main()