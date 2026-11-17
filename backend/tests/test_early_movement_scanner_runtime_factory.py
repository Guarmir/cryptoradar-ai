from unittest.mock import MagicMock

import pytest

import app.early_movement.scanner.scanner_runtime_factory as factory
from app.early_movement.scanner.scanner_runtime_config import (
    EarlyMovementScannerRuntimeConfig,
)
from app.early_movement.scanner.scanner_runtime_factory import (
    build_early_movement_scanner_runtime,
)


def test_runtime_factory_returns_none_when_disabled() -> None:
    config = EarlyMovementScannerRuntimeConfig(enabled=False)
    runtime = build_early_movement_scanner_runtime(config)
    assert runtime is None


def test_runtime_factory_builds_runtime_without_push() -> None:
    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        interval_seconds=120,
        push_enabled=False,
    )
    runtime = build_early_movement_scanner_runtime(config)
    assert runtime is not None
    assert runtime.scheduler.interval_seconds == 120.0
    assert runtime.is_running is False


@pytest.mark.parametrize(
    ("shadow", "discovery", "tracking", "expected_tracking"),
    [
        (True, True, False, False),
        (True, True, True, True),
        (False, True, True, False),
        (True, False, True, False),
    ],
)
def test_experimental_tracking_requires_all_three_flags(
    monkeypatch: pytest.MonkeyPatch,
    shadow: bool,
    discovery: bool,
    tracking: bool,
    expected_tracking: bool,
) -> None:
    monkeypatch.delenv(
        "EXTREME_MOVEMENT_DIRECTIONAL_HISTORY_ENABLED", raising=False
    )
    monkeypatch.setattr(
        factory.ExtremeMovementShadowConfig,
        "is_enabled",
        staticmethod(lambda: shadow),
    )
    monkeypatch.setattr(factory, "is_extreme_discovery_enabled", lambda: discovery)
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_EXPERIMENTAL_TRACKING_ENABLED",
        "true" if tracking else "false",
    )

    fake_store = MagicMock(name="tracking_store")
    store_constructor = MagicMock(return_value=fake_store)
    coordinator_constructor = MagicMock(return_value=MagicMock(name="coordinator"))
    discovery_runner_constructor = MagicMock(return_value=MagicMock(name="runner"))

    monkeypatch.setattr(
        factory,
        "PostgreSQLExtremeMovementExperimentalTrackingStore",
        store_constructor,
    )
    monkeypatch.setattr(
        factory,
        "ExtremeMovementExperimentalTrackingCoordinator",
        coordinator_constructor,
    )
    monkeypatch.setattr(
        factory,
        "ExtremeMovementDiscoveryRunner",
        discovery_runner_constructor,
    )

    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        database_url="postgresql://example.invalid/test",
        push_enabled=False,
    )
    runtime = build_early_movement_scanner_runtime(config)

    assert runtime is not None
    assert runtime.is_running is False
    assert store_constructor.called is expected_tracking
    assert coordinator_constructor.called is expected_tracking

    if shadow and discovery:
        discovery_runner_constructor.assert_called_once()
        supplied_coordinator = discovery_runner_constructor.call_args.kwargs[
            "experimental_tracking_coordinator"
        ]
        if expected_tracking:
            assert supplied_coordinator is coordinator_constructor.return_value
            store_constructor.assert_called_once_with(
                database_url=config.database_url,
                scope_key=factory.EXTREME_MOVEMENT_SCOPE_KEY,
            )
            coordinator_constructor.assert_called_once_with(store=fake_store)
        else:
            assert supplied_coordinator is None
    else:
        discovery_runner_constructor.assert_not_called()


def test_experimental_tracking_requires_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "EXTREME_MOVEMENT_DIRECTIONAL_HISTORY_ENABLED", raising=False
    )
    monkeypatch.setattr(
        factory.ExtremeMovementShadowConfig,
        "is_enabled",
        staticmethod(lambda: True),
    )
    monkeypatch.setattr(factory, "is_extreme_discovery_enabled", lambda: True)
    monkeypatch.setenv("EXTREME_MOVEMENT_EXPERIMENTAL_TRACKING_ENABLED", "true")

    store_constructor = MagicMock()
    monkeypatch.setattr(
        factory,
        "PostgreSQLExtremeMovementExperimentalTrackingStore",
        store_constructor,
    )

    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        database_url=None,
        push_enabled=False,
    )

    with pytest.raises(ValueError, match="Tracking experimental exige DATABASE_URL"):
        build_early_movement_scanner_runtime(config)

    store_constructor.assert_not_called()


@pytest.mark.parametrize(
    ("shadow", "discovery", "directional_enabled", "expected_store"),
    [
        (True, True, True, True),
        (True, True, False, False),
        (False, True, True, False),
        (True, False, True, False),
    ],
)
def test_directional_history_respects_shadow_and_discovery_flags(
    monkeypatch: pytest.MonkeyPatch,
    shadow: bool,
    discovery: bool,
    directional_enabled: bool,
    expected_store: bool,
) -> None:
    monkeypatch.setattr(
        factory.ExtremeMovementShadowConfig,
        "is_enabled",
        staticmethod(lambda: shadow),
    )
    monkeypatch.setattr(factory, "is_extreme_discovery_enabled", lambda: discovery)
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_DIRECTIONAL_HISTORY_ENABLED",
        "true" if directional_enabled else "false",
    )
    monkeypatch.setenv("EXTREME_MOVEMENT_EXPERIMENTAL_TRACKING_ENABLED", "false")

    fake_directional_store = MagicMock(name="directional_history_store")
    directional_constructor = MagicMock(return_value=fake_directional_store)
    bridge_constructor = MagicMock(return_value=MagicMock(name="bridge"))

    monkeypatch.setattr(
        factory,
        "PostgreSQLExtremeMovementDirectionalHistoryStore",
        directional_constructor,
    )
    monkeypatch.setattr(
        factory,
        "ExtremeMovementDiscoveryBridge",
        bridge_constructor,
    )

    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        database_url="postgresql://example.invalid/test",
        push_enabled=False,
    )
    runtime = build_early_movement_scanner_runtime(config)

    assert runtime is not None
    assert runtime.is_running is False
    assert directional_constructor.called is expected_store

    if shadow and discovery:
        bridge_constructor.assert_called_once()
        supplied_store = bridge_constructor.call_args.kwargs[
            "directional_history_store"
        ]
        if expected_store:
            assert supplied_store is fake_directional_store
            directional_constructor.assert_called_once_with(
                database_url=config.database_url,
                scope_key=factory.EXTREME_MOVEMENT_SCOPE_KEY,
            )
        else:
            assert supplied_store is None
    else:
        bridge_constructor.assert_not_called()


def test_directional_history_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("EXTREME_MOVEMENT_DIRECTIONAL_HISTORY_ENABLED", raising=False)
    monkeypatch.setenv("EXTREME_MOVEMENT_EXPERIMENTAL_TRACKING_ENABLED", "false")
    monkeypatch.setattr(
        factory.ExtremeMovementShadowConfig,
        "is_enabled",
        staticmethod(lambda: True),
    )
    monkeypatch.setattr(factory, "is_extreme_discovery_enabled", lambda: True)

    directional_constructor = MagicMock()
    bridge_constructor = MagicMock(return_value=MagicMock(name="bridge"))
    monkeypatch.setattr(
        factory,
        "PostgreSQLExtremeMovementDirectionalHistoryStore",
        directional_constructor,
    )
    monkeypatch.setattr(factory, "ExtremeMovementDiscoveryBridge", bridge_constructor)

    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        database_url="postgresql://example.invalid/test",
        push_enabled=False,
    )
    runtime = build_early_movement_scanner_runtime(config)

    assert runtime is not None
    directional_constructor.assert_not_called()
    assert bridge_constructor.call_args.kwargs["directional_history_store"] is None


def test_directional_history_requires_database_url_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory.ExtremeMovementShadowConfig,
        "is_enabled",
        staticmethod(lambda: True),
    )
    monkeypatch.setattr(factory, "is_extreme_discovery_enabled", lambda: True)
    monkeypatch.setenv("EXTREME_MOVEMENT_DIRECTIONAL_HISTORY_ENABLED", "true")
    monkeypatch.setenv("EXTREME_MOVEMENT_EXPERIMENTAL_TRACKING_ENABLED", "false")

    directional_constructor = MagicMock()
    monkeypatch.setattr(
        factory,
        "PostgreSQLExtremeMovementDirectionalHistoryStore",
        directional_constructor,
    )

    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        database_url=None,
        push_enabled=False,
    )

    with pytest.raises(
        ValueError,
        match="Historico direcional experimental exige DATABASE_URL",
    ):
        build_early_movement_scanner_runtime(config)

    directional_constructor.assert_not_called()
