from app.early_movement.scanner.scanner_runtime_config import (
    EarlyMovementScannerRuntimeConfig,
)
from app.early_movement.scanner.scanner_runtime_factory import (
    build_early_movement_scanner_runtime,
)


def test_runtime_factory_returns_none_when_disabled() -> None:
    config = EarlyMovementScannerRuntimeConfig(
        enabled=False,
    )

    runtime = (
        build_early_movement_scanner_runtime(
            config
        )
    )

    assert runtime is None


def test_runtime_factory_builds_runtime_without_push() -> None:
    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        interval_seconds=120,
        push_enabled=False,
    )

    runtime = (
        build_early_movement_scanner_runtime(
            config
        )
    )

    assert runtime is not None

    assert (
        runtime.scheduler.interval_seconds
        == 120.0
    )

    assert runtime.is_running is False