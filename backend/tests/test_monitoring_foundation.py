import unittest
from datetime import datetime, timezone

from app.monitoring.monitoring_observation import MonitoringObservation
from app.monitoring.monitoring_state import MonitoringState
from app.monitoring.monitoring_target import MonitoringTarget


class MonitoringTargetTest(unittest.TestCase):
    def test_normalizes_symbol(self):
        target = MonitoringTarget(
            symbol=" pippin ",
        )

        self.assertEqual(
            target.symbol,
            "PIPPIN",
        )

    def test_creates_spot_without_open_position(self):
        target = MonitoringTarget(
            symbol="BTC",
            trading_mode="spot",
        )

        self.assertTrue(target.is_spot)
        self.assertFalse(target.is_futures)
        self.assertFalse(target.has_open_position)

    def test_creates_futures_long_position(self):
        target = MonitoringTarget(
            symbol="PIPPIN",
            trading_mode="futures",
            has_open_position=True,
            position_side="long",
            entry_price=0.4285,
            leverage=10,
        )

        self.assertTrue(target.is_futures)
        self.assertTrue(target.is_long)
        self.assertFalse(target.is_short)
        self.assertEqual(
            target.entry_price,
            0.4285,
        )
        self.assertEqual(
            target.leverage,
            10,
        )

    def test_rejects_futures_position_without_side(self):
        with self.assertRaises(ValueError):
            MonitoringTarget(
                symbol="BTC",
                trading_mode="futures",
                has_open_position=True,
                entry_price=95000,
                leverage=5,
            )

    def test_rejects_position_without_entry_price(self):
        with self.assertRaises(ValueError):
            MonitoringTarget(
                symbol="BTC",
                trading_mode="futures",
                has_open_position=True,
                position_side="long",
                leverage=5,
            )

    def test_rejects_spot_with_leverage(self):
        with self.assertRaises(ValueError):
            MonitoringTarget(
                symbol="BTC",
                trading_mode="spot",
                has_open_position=True,
                entry_price=95000,
                leverage=2,
            )


class MonitoringObservationTest(unittest.TestCase):
    def test_normalizes_symbol(self):
        observation = MonitoringObservation(
            symbol=" eth ",
            price=3200,
        )

        self.assertEqual(
            observation.symbol,
            "ETH",
        )

    def test_rejects_invalid_price(self):
        with self.assertRaises(ValueError):
            MonitoringObservation(
                symbol="BTC",
                price=0,
            )

    def test_assigns_utc_timestamp_when_missing(self):
        observation = MonitoringObservation(
            symbol="BTC",
            price=95000,
        )

        self.assertIsNotNone(
            observation.observed_at,
        )

        self.assertIsNotNone(
            observation.observed_at.tzinfo,
        )

    def test_preserves_provided_timestamp(self):
        timestamp = datetime(
            2026,
            8,
            20,
            8,
            30,
            tzinfo=timezone.utc,
        )

        observation = MonitoringObservation(
            symbol="BTC",
            price=95000,
            observed_at=timestamp,
        )

        self.assertEqual(
            observation.observed_at,
            timestamp,
        )


class MonitoringStateTest(unittest.TestCase):
    def test_starts_without_observations(self):
        state = MonitoringState(
            target=MonitoringTarget(
                symbol="PIPPIN",
            ),
        )

        self.assertFalse(
            state.has_observation,
        )

        self.assertEqual(
            state.observation_count,
            0,
        )

        self.assertIsNone(
            state.current_price,
        )

    def test_adds_first_observation(self):
        state = MonitoringState(
            target=MonitoringTarget(
                symbol="PIPPIN",
            ),
        )

        updated = state.observe(
            MonitoringObservation(
                symbol="PIPPIN",
                price=0.42,
            ),
        )

        self.assertEqual(
            updated.observation_count,
            1,
        )

        self.assertEqual(
            updated.current_price,
            0.42,
        )

        self.assertIsNone(
            updated.previous_price,
        )

    def test_keeps_previous_observation(self):
        state = MonitoringState(
            target=MonitoringTarget(
                symbol="PIPPIN",
            ),
        )

        state = state.observe(
            MonitoringObservation(
                symbol="PIPPIN",
                price=0.42,
            ),
        )

        state = state.observe(
            MonitoringObservation(
                symbol="PIPPIN",
                price=0.4284,
            ),
        )

        self.assertEqual(
            state.observation_count,
            2,
        )

        self.assertEqual(
            state.previous_price,
            0.42,
        )

        self.assertEqual(
            state.current_price,
            0.4284,
        )

        self.assertAlmostEqual(
            state.price_change_since_previous_percent,
            2.0,
            places=6,
        )

    def test_detects_negative_price_change(self):
        state = MonitoringState(
            target=MonitoringTarget(
                symbol="ETH",
            ),
        )

        state = state.observe(
            MonitoringObservation(
                symbol="ETH",
                price=3200,
            ),
        )

        state = state.observe(
            MonitoringObservation(
                symbol="ETH",
                price=3040,
            ),
        )

        self.assertAlmostEqual(
            state.price_change_since_previous_percent,
            -5.0,
            places=6,
        )

    def test_rejects_observation_from_another_asset(self):
        state = MonitoringState(
            target=MonitoringTarget(
                symbol="BTC",
            ),
        )

        with self.assertRaises(ValueError):
            state.observe(
                MonitoringObservation(
                    symbol="ETH",
                    price=3200,
                ),
            )


if __name__ == "__main__":
    unittest.main()