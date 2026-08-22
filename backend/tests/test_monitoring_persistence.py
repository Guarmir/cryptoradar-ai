import json
import unittest
from datetime import datetime, timezone

from app.monitoring.in_memory_monitoring_state_store import (
    InMemoryMonitoringStateStore,
)
from app.monitoring.monitoring_observation import (
    MonitoringObservation,
)
from app.monitoring.monitoring_state import (
    MonitoringState,
)
from app.monitoring.monitoring_state_serializer import (
    monitoring_state_from_dict,
    monitoring_state_to_dict,
)
from app.monitoring.monitoring_target import (
    MonitoringTarget,
)


def _build_futures_state():
    target = MonitoringTarget(
        symbol="PIPPIN",
        coin_id="pippin",
        trading_mode="futures",
        has_open_position=True,
        position_side="long",
        entry_price=0.4285,
        leverage=10,
    )

    first = MonitoringObservation(
        symbol="PIPPIN",
        price=0.42,
        volume=100_000_000,
        market_cap=400_000_000,
        change_24h=2.5,
        observed_at=datetime(
            2026,
            8,
            20,
            8,
            0,
            tzinfo=timezone.utc,
        ),
    )

    second = MonitoringObservation(
        symbol="PIPPIN",
        price=0.4284,
        volume=150_000_000,
        market_cap=420_000_000,
        change_24h=4.8,
        observed_at=datetime(
            2026,
            8,
            20,
            8,
            1,
            tzinfo=timezone.utc,
        ),
    )

    state = MonitoringState(
        target=target,
    )

    state = state.observe(
        first,
    )

    return state.observe(
        second,
    )


class MonitoringStateSerializerTest(
    unittest.TestCase
):
    def test_serializes_complete_state_to_json_safe_data(
        self,
    ):
        state = _build_futures_state()

        serialized = monitoring_state_to_dict(
            state,
        )

        encoded = json.dumps(
            serialized,
        )

        self.assertIsInstance(
            encoded,
            str,
        )

        self.assertEqual(
            serialized["schema_version"],
            1,
        )

        self.assertEqual(
            serialized["target"]["symbol"],
            "PIPPIN",
        )

        self.assertEqual(
            serialized["target"]["trading_mode"],
            "futures",
        )

        self.assertEqual(
            serialized["target"]["position_side"],
            "long",
        )

        self.assertEqual(
            serialized["observation_count"],
            2,
        )

    def test_restores_complete_state(
        self,
    ):
        original = _build_futures_state()

        restored = monitoring_state_from_dict(
            monitoring_state_to_dict(
                original,
            )
        )

        self.assertEqual(
            restored.target.symbol,
            "PIPPIN",
        )

        self.assertEqual(
            restored.target.coin_id,
            "pippin",
        )

        self.assertTrue(
            restored.target.is_futures,
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

        self.assertEqual(
            restored.observation_count,
            2,
        )

        self.assertEqual(
            restored.previous_price,
            0.42,
        )

        self.assertEqual(
            restored.current_price,
            0.4284,
        )

        self.assertAlmostEqual(
            restored.price_change_since_previous_percent,
            2.0,
            places=6,
        )

        self.assertEqual(
            restored.current_observation.observed_at,
            original.current_observation.observed_at,
        )

    def test_rejects_unknown_schema_version(
        self,
    ):
        data = monitoring_state_to_dict(
            _build_futures_state(),
        )

        data["schema_version"] = 999

        with self.assertRaises(
            ValueError
        ):
            monitoring_state_from_dict(
                data,
            )

    def test_rejects_invalid_target_data(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            monitoring_state_from_dict(
                {
                    "schema_version": 1,
                    "target": None,
                    "observation_count": 0,
                }
            )

    def test_rejects_invalid_observation_count(
        self,
    ):
        data = monitoring_state_to_dict(
            _build_futures_state(),
        )

        data["observation_count"] = "2"

        with self.assertRaises(
            ValueError
        ):
            monitoring_state_from_dict(
                data,
            )


class InMemoryMonitoringStateStoreTest(
    unittest.TestCase
):
    def test_starts_empty(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        self.assertEqual(
            store.load_all(),
            (),
        )

        self.assertIsNone(
            store.load_state(
                "BTC",
            )
        )

    def test_saves_and_restores_state(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        original = _build_futures_state()

        store.save_state(
            original,
        )

        restored = store.load_state(
            "pippin",
        )

        self.assertIsNotNone(
            restored,
        )

        self.assertEqual(
            restored.target.symbol,
            "PIPPIN",
        )

        self.assertEqual(
            restored.observation_count,
            2,
        )

        self.assertEqual(
            restored.current_price,
            0.4284,
        )

        self.assertTrue(
            restored.target.is_long,
        )

    def test_updates_existing_symbol_without_duplicate(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        state = MonitoringState(
            target=MonitoringTarget(
                symbol="BTC",
            )
        )

        store.save_state(
            state,
        )

        state = state.observe(
            MonitoringObservation(
                symbol="BTC",
                price=95000,
            )
        )

        store.save_state(
            state,
        )

        all_states = store.load_all()

        self.assertEqual(
            len(all_states),
            1,
        )

        self.assertEqual(
            all_states[0].observation_count,
            1,
        )

        self.assertEqual(
            all_states[0].current_price,
            95000,
        )

    def test_load_all_restores_multiple_assets(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        store.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="BTC",
                )
            )
        )

        store.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="ETH",
                )
            )
        )

        states = store.load_all()

        symbols = {
            state.target.symbol
            for state in states
        }

        self.assertEqual(
            symbols,
            {
                "BTC",
                "ETH",
            },
        )

    def test_delete_state(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        store.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="BTC",
                )
            )
        )

        removed = store.delete_state(
            "btc",
        )

        self.assertTrue(
            removed,
        )

        self.assertIsNone(
            store.load_state(
                "BTC",
            )
        )

        self.assertFalse(
            store.delete_state(
                "BTC",
            )
        )

    def test_clear_removes_everything(
        self,
    ):
        store = InMemoryMonitoringStateStore()

        store.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="BTC",
                )
            )
        )

        store.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="ETH",
                )
            )
        )

        store.clear()

        self.assertEqual(
            store.load_all(),
            (),
        )


if __name__ == "__main__":
    unittest.main()