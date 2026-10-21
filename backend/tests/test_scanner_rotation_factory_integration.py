
from app.early_movement.scanner import (
    scanner_runtime_factory,
)
from app.early_movement.scanner.scanner_runtime_config import (
    EarlyMovementScannerRuntimeConfig,
)


def test_factory_connects_rotation_when_enabled(
    monkeypatch,
):
    monkeypatch.setenv(
        "EARLY_MOVEMENT_SCANNER_ROTATION_ENABLED",
        "true",
    )

    created = []

    original_bridge = (
        scanner_runtime_factory
        .EarlyMovementScannerRotationBridge
    )

    class RecordingBridge(original_bridge):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            created.append(self)

    monkeypatch.setattr(
        scanner_runtime_factory,
        "EarlyMovementScannerRotationBridge",
        RecordingBridge,
    )

    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        interval_seconds=120,
        push_enabled=False,
    )

    runtime = (
        scanner_runtime_factory
        .build_early_movement_scanner_runtime(
            config,
        )
    )

    assert runtime is not None
    assert len(created) == 1


def test_factory_does_not_create_rotation_when_disabled(
    monkeypatch,
):
    monkeypatch.setenv(
        "EARLY_MOVEMENT_SCANNER_ROTATION_ENABLED",
        "false",
    )

    def unexpected_bridge(**kwargs):
        raise AssertionError(
            "Rotação não deveria ser criada."
        )

    monkeypatch.setattr(
        scanner_runtime_factory,
        "EarlyMovementScannerRotationBridge",
        unexpected_bridge,
    )

    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        interval_seconds=120,
        push_enabled=False,
    )

    runtime = (
        scanner_runtime_factory
        .build_early_movement_scanner_runtime(
            config,
        )
    )

    assert runtime is not None
