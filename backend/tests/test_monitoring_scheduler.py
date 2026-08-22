import threading
import time
import unittest

from app.monitoring.monitoring_cycle_runner import (
    MonitoringCycleRunner,
)
from app.monitoring.monitoring_engine import MonitoringEngine
from app.monitoring.monitoring_execution_result import (
    MonitoringBatchResult,
)
from app.monitoring.monitoring_market_data_provider import (
    MonitoringMarketDataProvider,
)
from app.monitoring.monitoring_scheduler import (
    MonitoringScheduler,
)
from app.monitoring.monitoring_service import MonitoringService
from app.monitoring.monitoring_target import MonitoringTarget


class _FakeMarketDataProvider(
    MonitoringMarketDataProvider
):
    def __init__(
        self,
        data_by_symbol,
    ):
        self.data_by_symbol = data_by_symbol

        self.fetches = []

    def fetch_market_data(
        self,
        target,
    ):
        self.fetches.append(
            target.symbol,
        )

        value = self.data_by_symbol[
            target.symbol
        ]

        if isinstance(value, Exception):
            raise value

        if isinstance(value, list):
            if not value:
                raise AssertionError(
                    "Sem dados fake restantes."
                )

            current = value.pop(0)

            if isinstance(
                current,
                Exception,
            ):
                raise current

            return current

        return value


class _BlockingMarketDataProvider(
    MonitoringMarketDataProvider
):
    def __init__(self):
        self.started = threading.Event()

        self.release = threading.Event()

    def fetch_market_data(
        self,
        target,
    ):
        self.started.set()

        released = self.release.wait(
            timeout=2,
        )

        if not released:
            raise RuntimeError(
                "Teste não liberou o provider."
            )

        return {
            "current_price": 95000,
        }


class _RecordingRunner:
    def __init__(self):
        self.call_count = 0

        self.called = threading.Event()

    def run_once(self):
        self.call_count += 1

        self.called.set()

        return MonitoringBatchResult(
            executions=(),
        )


def _build_service(
    provider,
):
    return MonitoringService(
        engine=MonitoringEngine(),
        market_data_provider=provider,
    )


class MonitoringCycleRunnerTest(
    unittest.TestCase
):
    def test_runs_cycle_for_all_registered_targets(
        self,
    ):
        provider = _FakeMarketDataProvider(
            {
                "BTC": {
                    "current_price": 95000,
                },
                "ETH": {
                    "current_price": 3200,
                },
                "PIPPIN": {
                    "current_price": 0.42,
                },
            }
        )

        service = _build_service(
            provider,
        )

        for symbol in (
            "BTC",
            "ETH",
            "PIPPIN",
        ):
            service.register_target(
                MonitoringTarget(
                    symbol=symbol,
                )
            )

        runner = MonitoringCycleRunner(
            service=service,
        )

        batch = runner.run_once()

        self.assertFalse(
            batch.skipped_due_to_overlap,
        )

        self.assertEqual(
            batch.execution_count,
            3,
        )

        self.assertEqual(
            batch.success_count,
            3,
        )

        self.assertEqual(
            batch.failure_count,
            0,
        )

        self.assertTrue(
            batch.all_succeeded,
        )

        self.assertEqual(
            provider.fetches,
            [
                "BTC",
                "ETH",
                "PIPPIN",
            ],
        )

    def test_failure_of_one_asset_does_not_stop_others(
        self,
    ):
        provider = _FakeMarketDataProvider(
            {
                "BTC": {
                    "current_price": 95000,
                },
                "ETH": RuntimeError(
                    "Falha temporária ETH"
                ),
                "PIPPIN": {
                    "current_price": 0.42,
                },
            }
        )

        service = _build_service(
            provider,
        )

        for symbol in (
            "BTC",
            "ETH",
            "PIPPIN",
        ):
            service.register_target(
                MonitoringTarget(
                    symbol=symbol,
                )
            )

        runner = MonitoringCycleRunner(
            service=service,
        )

        batch = runner.run_once()

        self.assertEqual(
            batch.execution_count,
            3,
        )

        self.assertEqual(
            batch.success_count,
            2,
        )

        self.assertEqual(
            batch.failure_count,
            1,
        )

        self.assertTrue(
            batch.has_failures,
        )

        self.assertFalse(
            batch.all_succeeded,
        )

        failed = [
            execution
            for execution in batch.executions
            if execution.failed
        ]

        self.assertEqual(
            len(failed),
            1,
        )

        self.assertEqual(
            failed[0].symbol,
            "ETH",
        )

        self.assertIn(
            "Falha temporária ETH",
            failed[0].error_message,
        )

        self.assertEqual(
            service.state_for(
                "BTC"
            ).observation_count,
            1,
        )

        self.assertEqual(
            service.state_for(
                "PIPPIN"
            ).observation_count,
            1,
        )

    def test_empty_monitoring_set_is_valid(
        self,
    ):
        provider = _FakeMarketDataProvider(
            {}
        )

        runner = MonitoringCycleRunner(
            service=_build_service(
                provider,
            ),
        )

        batch = runner.run_once()

        self.assertEqual(
            batch.execution_count,
            0,
        )

        self.assertTrue(
            batch.all_succeeded,
        )

    def test_prevents_overlapping_cycles(
        self,
    ):
        provider = (
            _BlockingMarketDataProvider()
        )

        service = _build_service(
            provider,
        )

        service.register_target(
            MonitoringTarget(
                symbol="BTC",
            )
        )

        runner = MonitoringCycleRunner(
            service=service,
        )

        first_result = []

        def execute_first():
            first_result.append(
                runner.run_once()
            )

        thread = threading.Thread(
            target=execute_first,
        )

        thread.start()

        self.assertTrue(
            provider.started.wait(
                timeout=1,
            )
        )

        self.assertTrue(
            runner.is_running,
        )

        overlapping = runner.run_once()

        self.assertTrue(
            overlapping.skipped_due_to_overlap,
        )

        self.assertEqual(
            overlapping.execution_count,
            0,
        )

        provider.release.set()

        thread.join(
            timeout=2,
        )

        self.assertFalse(
            thread.is_alive(),
        )

        self.assertEqual(
            len(first_result),
            1,
        )

        self.assertEqual(
            first_result[0].success_count,
            1,
        )


class MonitoringSchedulerTest(
    unittest.TestCase
):
    def test_rejects_invalid_interval(
        self,
    ):
        runner = _RecordingRunner()

        with self.assertRaises(
            ValueError
        ):
            MonitoringScheduler(
                runner=runner,
                interval_seconds=0,
            )

    def test_start_runs_immediately(
        self,
    ):
        runner = _RecordingRunner()

        scheduler = MonitoringScheduler(
            runner=runner,
            interval_seconds=60,
        )

        started = scheduler.start()

        self.assertTrue(
            started,
        )

        self.assertTrue(
            runner.called.wait(
                timeout=1,
            )
        )

        self.assertGreaterEqual(
            runner.call_count,
            1,
        )

        self.assertIsNotNone(
            scheduler.last_batch_result,
        )

        scheduler.stop()

    def test_second_start_does_not_create_duplicate_scheduler(
        self,
    ):
        runner = _RecordingRunner()

        scheduler = MonitoringScheduler(
            runner=runner,
            interval_seconds=60,
        )

        first_start = scheduler.start()

        self.assertTrue(
            runner.called.wait(
                timeout=1,
            )
        )

        second_start = scheduler.start()

        self.assertTrue(
            first_start,
        )

        self.assertFalse(
            second_start,
        )

        scheduler.stop()

    def test_stop_finishes_background_scheduler(
        self,
    ):
        runner = _RecordingRunner()

        scheduler = MonitoringScheduler(
            runner=runner,
            interval_seconds=60,
        )

        scheduler.start()

        self.assertTrue(
            runner.called.wait(
                timeout=1,
            )
        )

        stopped = scheduler.stop()

        self.assertTrue(
            stopped,
        )

        deadline = (
            time.monotonic() + 1
        )

        while (
            scheduler.is_running
            and time.monotonic()
            < deadline
        ):
            time.sleep(
                0.01,
            )

        self.assertFalse(
            scheduler.is_running,
        )

    def test_manual_run_once_updates_last_result(
        self,
    ):
        runner = _RecordingRunner()

        scheduler = MonitoringScheduler(
            runner=runner,
            interval_seconds=60,
        )

        result = scheduler.run_once()

        self.assertIs(
            scheduler.last_batch_result,
            result,
        )

        self.assertEqual(
            runner.call_count,
            1,
        )

        self.assertIsNone(
            scheduler.last_scheduler_error,
        )


if __name__ == "__main__":
    unittest.main()