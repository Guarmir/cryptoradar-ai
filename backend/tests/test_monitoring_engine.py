import unittest
from datetime import timezone

from app.monitoring.monitoring_engine import MonitoringEngine
from app.monitoring.monitoring_observation import MonitoringObservation
from app.monitoring.monitoring_observation_builder import (
    build_monitoring_observation,
)
from app.monitoring.monitoring_target import MonitoringTarget


class MonitoringObservationBuilderTest(unittest.TestCase):
    def test_builds_from_coingecko_market_data(self):
        target = MonitoringTarget(
            symbol="PIPPIN",
        )

        observation = build_monitoring_observation(
            target,
            {
                "current_price": 0.4285,
                "total_volume": 150_000_000,
                "market_cap": 420_000_000,
                "price_change_percentage_24h": 12.5,
                "last_updated": "2026-08-20T08:30:00Z",
            },
        )

        self.assertEqual(
            observation.symbol,
            "PIPPIN",
        )

        self.assertEqual(
            observation.price,
            0.4285,
        )

        self.assertEqual(
            observation.volume,
            150_000_000,
        )

        self.assertEqual(
            observation.market_cap,
            420_000_000,
        )

        self.assertEqual(
            observation.change_24h,
            12.5,
        )

        self.assertEqual(
            observation.observed_at.tzinfo,
            timezone.utc,
        )

    def test_builds_from_existing_backend_response_shape(self):
        target = MonitoringTarget(
            symbol="ETH",
        )

        observation = build_monitoring_observation(
            target,
            {
                "price": 3200,
                "volume": 800_000_000,
                "market_cap": 380_000_000_000,
                "change_24h": -2.5,
            },
        )

        self.assertEqual(
            observation.price,
            3200,
        )

        self.assertEqual(
            observation.volume,
            800_000_000,
        )

        self.assertEqual(
            observation.change_24h,
            -2.5,
        )

    def test_rejects_missing_price(self):
        target = MonitoringTarget(
            symbol="BTC",
        )

        with self.assertRaises(ValueError):
            build_monitoring_observation(
                target,
                {
                    "total_volume": 1_000_000,
                },
            )

    def test_ignores_invalid_optional_values(self):
        target = MonitoringTarget(
            symbol="BTC",
        )

        observation = build_monitoring_observation(
            target,
            {
                "current_price": 95000,
                "total_volume": "inválido",
                "market_cap": -1,
                "price_change_percentage_24h": "inválido",
            },
        )

        self.assertIsNone(
            observation.volume,
        )

        self.assertIsNone(
            observation.market_cap,
        )

        self.assertIsNone(
            observation.change_24h,
        )


class MonitoringEngineTest(unittest.TestCase):
    def test_registers_target(self):
        engine = MonitoringEngine()

        state = engine.register_target(
            MonitoringTarget(
                symbol=" pippin ",
            ),
        )

        self.assertEqual(
            engine.target_count,
            1,
        )

        self.assertTrue(
            engine.contains("PIPPIN"),
        )

        self.assertEqual(
            state.target.symbol,
            "PIPPIN",
        )

    def test_first_market_cycle_creates_observation(self):
        engine = MonitoringEngine()

        engine.register_target(
            MonitoringTarget(
                symbol="PIPPIN",
            ),
        )

        result = engine.observe_market_data(
            "pippin",
            {
                "current_price": 0.42,
                "total_volume": 100_000_000,
            },
        )

        self.assertTrue(
            result.is_first_observation,
        )

        self.assertEqual(
            result.observation_count,
            1,
        )

        self.assertEqual(
            result.current_price,
            0.42,
        )

        self.assertIsNone(
            result.previous_price,
        )

        self.assertIsNone(
            result.price_change_percent,
        )

    def test_second_cycle_calculates_positive_change(self):
        engine = MonitoringEngine()

        engine.register_target(
            MonitoringTarget(
                symbol="PIPPIN",
            ),
        )

        engine.observe_market_data(
            "PIPPIN",
            {
                "current_price": 0.42,
            },
        )

        result = engine.observe_market_data(
            "PIPPIN",
            {
                "current_price": 0.4284,
            },
        )

        self.assertFalse(
            result.is_first_observation,
        )

        self.assertEqual(
            result.observation_count,
            2,
        )

        self.assertEqual(
            result.previous_price,
            0.42,
        )

        self.assertEqual(
            result.current_price,
            0.4284,
        )

        self.assertAlmostEqual(
            result.price_change_percent,
            2.0,
            places=6,
        )

    def test_second_cycle_calculates_negative_change(self):
        engine = MonitoringEngine()

        engine.register_target(
            MonitoringTarget(
                symbol="ETH",
            ),
        )

        engine.observe_market_data(
            "ETH",
            {
                "current_price": 3200,
            },
        )

        result = engine.observe_market_data(
            "ETH",
            {
                "current_price": 3040,
            },
        )

        self.assertAlmostEqual(
            result.price_change_percent,
            -5.0,
            places=6,
        )

    def test_keeps_independent_state_for_multiple_assets(self):
        engine = MonitoringEngine()

        engine.register_target(
            MonitoringTarget(
                symbol="BTC",
            ),
        )

        engine.register_target(
            MonitoringTarget(
                symbol="ETH",
            ),
        )

        engine.observe_market_data(
            "BTC",
            {
                "current_price": 95000,
            },
        )

        engine.observe_market_data(
            "ETH",
            {
                "current_price": 3200,
            },
        )

        self.assertEqual(
            engine.target_count,
            2,
        )

        self.assertEqual(
            engine.state_for("BTC").current_price,
            95000,
        )

        self.assertEqual(
            engine.state_for("ETH").current_price,
            3200,
        )

    def test_updating_target_preserves_observation_history(self):
        engine = MonitoringEngine()

        engine.register_target(
            MonitoringTarget(
                symbol="PIPPIN",
                trading_mode="futures",
            ),
        )

        engine.observe_market_data(
            "PIPPIN",
            {
                "current_price": 0.42,
            },
        )

        updated_state = engine.register_target(
            MonitoringTarget(
                symbol="PIPPIN",
                trading_mode="futures",
                has_open_position=True,
                position_side="long",
                entry_price=0.4285,
                leverage=10,
            ),
        )

        self.assertEqual(
            updated_state.observation_count,
            1,
        )

        self.assertEqual(
            updated_state.current_price,
            0.42,
        )

        self.assertTrue(
            updated_state.target.is_long,
        )

        self.assertEqual(
            updated_state.target.leverage,
            10,
        )

    def test_observe_accepts_direct_observation(self):
        engine = MonitoringEngine()

        engine.register_target(
            MonitoringTarget(
                symbol="BTC",
            ),
        )

        result = engine.observe(
            MonitoringObservation(
                symbol="BTC",
                price=95000,
            ),
        )

        self.assertEqual(
            result.current_price,
            95000,
        )

        self.assertEqual(
            result.observation_count,
            1,
        )

    def test_rejects_unregistered_asset(self):
        engine = MonitoringEngine()

        with self.assertRaises(KeyError):
            engine.observe_market_data(
                "BTC",
                {
                    "current_price": 95000,
                },
            )

    def test_removes_target(self):
        engine = MonitoringEngine()

        engine.register_target(
            MonitoringTarget(
                symbol="BTC",
            ),
        )

        removed = engine.remove_target(
            "btc",
        )

        self.assertTrue(
            removed,
        )

        self.assertFalse(
            engine.contains("BTC"),
        )

        self.assertEqual(
            engine.target_count,
            0,
        )

    def test_clear_removes_all_targets(self):
        engine = MonitoringEngine()

        engine.register_target(
            MonitoringTarget(
                symbol="BTC",
            ),
        )

        engine.register_target(
            MonitoringTarget(
                symbol="ETH",
            ),
        )

        engine.clear()

        self.assertEqual(
            engine.target_count,
            0,
        )

        self.assertEqual(
            engine.registered_symbols,
            (),
        )


if __name__ == "__main__":
    unittest.main()