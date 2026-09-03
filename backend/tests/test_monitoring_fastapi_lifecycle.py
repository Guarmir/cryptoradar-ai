import unittest
from unittest.mock import patch

from fastapi import FastAPI

from app.monitoring.monitoring_fastapi_lifecycle import (
    monitoring_lifespan,
)
from app.monitoring.monitoring_runtime_config import (
    MonitoringRuntimeConfig,
)


class _FakeRuntime:
    def __init__(
        self,
        *,
        fail_on_start=False,
    ):
        self.start_count = 0
        self.stop_count = 0
        self.fail_on_start = fail_on_start

    def start(self):
        self.start_count += 1

        if self.fail_on_start:
            raise RuntimeError(
                "Falha simulada no startup."
            )

        return True

    def stop(self):
        self.stop_count += 1
        return True


class MonitoringFastAPILifecycleTest(
    unittest.IsolatedAsyncioTestCase
):
    async def test_disabled_monitoring_does_not_start_runtime(
        self,
    ):
        app = FastAPI()

        config = MonitoringRuntimeConfig(
            enabled=False,
        )

        with patch(
            "app.monitoring."
            "monitoring_fastapi_lifecycle."
            "MonitoringRuntimeConfig."
            "from_environment",
            return_value=config,
        ), patch(
            "app.monitoring."
            "monitoring_fastapi_lifecycle."
            "build_monitoring_runtime",
            return_value=None,
        ):
            async with monitoring_lifespan(
                app,
            ):
                self.assertIsNone(
                    app.state.monitoring_runtime,
                )

        self.assertIsNone(
            app.state.monitoring_runtime,
        )

    async def test_enabled_monitoring_starts_and_stops_runtime(
        self,
    ):
        app = FastAPI()

        config = MonitoringRuntimeConfig(
            enabled=True,
            database_url=(
                "postgresql://test"
            ),
            scope_key="test-scope",
            interval_seconds=60,
        )

        runtime = _FakeRuntime()

        with patch(
            "app.monitoring."
            "monitoring_fastapi_lifecycle."
            "MonitoringRuntimeConfig."
            "from_environment",
            return_value=config,
        ), patch(
            "app.monitoring."
            "monitoring_fastapi_lifecycle."
            "build_monitoring_runtime",
            return_value=runtime,
        ):
            async with monitoring_lifespan(
                app,
            ):
                self.assertIs(
                    app.state.monitoring_runtime,
                    runtime,
                )

                self.assertEqual(
                    runtime.start_count,
                    1,
                )

                self.assertEqual(
                    runtime.stop_count,
                    0,
                )

            self.assertEqual(
                runtime.stop_count,
                1,
            )

            self.assertIsNone(
                app.state.monitoring_runtime,
            )

    async def test_shutdown_occurs_even_if_application_body_fails(
        self,
    ):
        app = FastAPI()

        config = MonitoringRuntimeConfig(
            enabled=True,
            database_url=(
                "postgresql://test"
            ),
            scope_key="test-scope",
        )

        runtime = _FakeRuntime()

        with patch(
            "app.monitoring."
            "monitoring_fastapi_lifecycle."
            "MonitoringRuntimeConfig."
            "from_environment",
            return_value=config,
        ), patch(
            "app.monitoring."
            "monitoring_fastapi_lifecycle."
            "build_monitoring_runtime",
            return_value=runtime,
        ):
            with self.assertRaises(
                RuntimeError
            ):
                async with monitoring_lifespan(
                    app,
                ):
                    raise RuntimeError(
                        "Falha simulada da aplicação."
                    )

        self.assertEqual(
            runtime.start_count,
            1,
        )

        self.assertEqual(
            runtime.stop_count,
            1,
        )

    async def test_startup_failure_is_propagated(
        self,
    ):
        app = FastAPI()

        config = MonitoringRuntimeConfig(
            enabled=True,
            database_url=(
                "postgresql://test"
            ),
            scope_key="test-scope",
        )

        runtime = _FakeRuntime(
            fail_on_start=True,
        )

        with patch(
            "app.monitoring."
            "monitoring_fastapi_lifecycle."
            "MonitoringRuntimeConfig."
            "from_environment",
            return_value=config,
        ), patch(
            "app.monitoring."
            "monitoring_fastapi_lifecycle."
            "build_monitoring_runtime",
            return_value=runtime,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Falha simulada",
            ):
                async with monitoring_lifespan(
                    app,
                ):
                    pass

        self.assertEqual(
            runtime.start_count,
            1,
        )

        self.assertEqual(
            runtime.stop_count,
            0,
        )


class MainApplicationRegressionTest(
    unittest.TestCase
):
    def test_existing_routes_remain_registered(
        self,
    ):
        from app.main import app

        paths = {
            route.path
            for route in app.routes
        }

        expected_paths = {
            "/",
            "/analysis/{symbol}",
            "/price/{coin}",
            "/alert/{coin}/{price}",
            "/score/{coin}",
            "/chart/{coin}",
            "/asset/{coin}",
            "/push/devices/register",
        }

        self.assertTrue(
            expected_paths.issubset(
                paths,
            )
        )


if __name__ == "__main__":
    unittest.main()