import unittest

from app.monitoring.monitoring_runtime import (
    MonitoringRuntime,
)
from app.monitoring.monitoring_runtime_config import (
    MonitoringRuntimeConfig,
)
from app.monitoring.monitoring_runtime_factory import (
    build_monitoring_runtime,
)


class _FakeService:
    def __init__(
        self,
        restored_states=(),
    ):
        self.restored_states = (
            restored_states
        )

        self.restore_count = 0

        self.target_count = len(
            restored_states,
        )

        self.registered_symbols = tuple(
            f"ASSET-{index}"
            for index, _
            in enumerate(
                restored_states,
                start=1,
            )
        )

    def restore_from_store(
        self,
    ):
        self.restore_count += 1

        return self.restored_states


class _FakeScheduler:
    def __init__(self):
        self.start_count = 0
        self.stop_count = 0
        self.is_running = False

    def start(self):
        if self.is_running:
            return False

        self.start_count += 1
        self.is_running = True

        return True

    def stop(self):
        if not self.is_running:
            return False

        self.stop_count += 1
        self.is_running = False

        return True


class MonitoringRuntimeConfigTest(
    unittest.TestCase
):
    def test_monitoring_is_disabled_by_default(
        self,
    ):
        config = (
            MonitoringRuntimeConfig
            .from_environment(
                {}
            )
        )

        self.assertFalse(
            config.enabled,
        )

        self.assertEqual(
            config.interval_seconds,
            60,
        )

    def test_parses_enabled_configuration(
        self,
    ):
        config = (
            MonitoringRuntimeConfig
            .from_environment(
                {
                    "CRYPTORADAR_MONITORING_ENABLED":
                        "true",
                    "CRYPTORADAR_DATABASE_URL":
                        "postgresql://test",
                    "CRYPTORADAR_MONITORING_SCOPE":
                        "local-test",
                    "CRYPTORADAR_MONITORING_INTERVAL_SECONDS":
                        "30",
                }
            )
        )

        self.assertTrue(
            config.enabled,
        )

        self.assertEqual(
            config.database_url,
            "postgresql://test",
        )

        self.assertEqual(
            config.scope_key,
            "local-test",
        )

        self.assertEqual(
            config.interval_seconds,
            30,
        )

    def test_enabled_requires_database_url(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            (
                MonitoringRuntimeConfig
                .from_environment(
                    {
                        "CRYPTORADAR_MONITORING_ENABLED":
                            "true",
                        "CRYPTORADAR_MONITORING_SCOPE":
                            "local-test",
                    }
                )
            )

    def test_enabled_requires_scope(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            (
                MonitoringRuntimeConfig
                .from_environment(
                    {
                        "CRYPTORADAR_MONITORING_ENABLED":
                            "true",
                        "CRYPTORADAR_DATABASE_URL":
                            "postgresql://test",
                    }
                )
            )

    def test_rejects_invalid_interval(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            (
                MonitoringRuntimeConfig
                .from_environment(
                    {
                        "CRYPTORADAR_MONITORING_INTERVAL_SECONDS":
                            "0",
                    }
                )
            )

    def test_rejects_invalid_enabled_value(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            (
                MonitoringRuntimeConfig
                .from_environment(
                    {
                        "CRYPTORADAR_MONITORING_ENABLED":
                            "talvez",
                    }
                )
            )


class MonitoringRuntimeTest(
    unittest.TestCase
):
    def test_start_restores_before_scheduler(
        self,
    ):
        service = _FakeService(
            restored_states=(
                object(),
                object(),
            )
        )

        scheduler = _FakeScheduler()

        runtime = MonitoringRuntime(
            service=service,
            scheduler=scheduler,
        )

        started = runtime.start()

        self.assertTrue(
            started,
        )

        self.assertEqual(
            service.restore_count,
            1,
        )

        self.assertEqual(
            scheduler.start_count,
            1,
        )

        self.assertEqual(
            runtime.restored_state_count,
            2,
        )

        self.assertTrue(
            runtime.is_started,
        )

        self.assertTrue(
            runtime.is_running,
        )

    def test_second_start_is_ignored(
        self,
    ):
        service = _FakeService()

        scheduler = _FakeScheduler()

        runtime = MonitoringRuntime(
            service=service,
            scheduler=scheduler,
        )

        first = runtime.start()
        second = runtime.start()

        self.assertTrue(
            first,
        )

        self.assertFalse(
            second,
        )

        self.assertEqual(
            service.restore_count,
            1,
        )

        self.assertEqual(
            scheduler.start_count,
            1,
        )

    def test_stop_finishes_scheduler(
        self,
    ):
        service = _FakeService()
        scheduler = _FakeScheduler()

        runtime = MonitoringRuntime(
            service=service,
            scheduler=scheduler,
        )

        runtime.start()

        stopped = runtime.stop()

        self.assertTrue(
            stopped,
        )

        self.assertEqual(
            scheduler.stop_count,
            1,
        )

        self.assertFalse(
            runtime.is_started,
        )

        self.assertFalse(
            runtime.is_running,
        )

    def test_second_stop_is_ignored(
        self,
    ):
        service = _FakeService()
        scheduler = _FakeScheduler()

        runtime = MonitoringRuntime(
            service=service,
            scheduler=scheduler,
        )

        runtime.start()

        first = runtime.stop()
        second = runtime.stop()

        self.assertTrue(
            first,
        )

        self.assertFalse(
            second,
        )

        self.assertEqual(
            scheduler.stop_count,
            1,
        )


class MonitoringRuntimeFactoryTest(
    unittest.TestCase
):
    def test_disabled_configuration_returns_none(
        self,
    ):
        config = MonitoringRuntimeConfig(
            enabled=False,
        )

        runtime = build_monitoring_runtime(
            config,
        )

        self.assertIsNone(
            runtime,
        )

    def test_enabled_configuration_builds_runtime_without_connecting(
        self,
    ):
        config = MonitoringRuntimeConfig(
            enabled=True,
            database_url=(
                "postgresql://test"
            ),
            scope_key="local-test",
            interval_seconds=60,
        )

        runtime = build_monitoring_runtime(
            config,
        )

        self.assertIsInstance(
            runtime,
            MonitoringRuntime,
        )

        self.assertFalse(
            runtime.is_started,
        )

        self.assertFalse(
            runtime.is_running,
        )


if __name__ == "__main__":
    unittest.main()