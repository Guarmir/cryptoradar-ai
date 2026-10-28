
from unittest.mock import patch

import pytest

from app.early_movement.extreme_movement.extreme_movement_shadow_config import (
    ExtremeMovementShadowConfig,
)
from app.early_movement.extreme_movement.extreme_movement_discovery_bridge import (
    ExtremeMovementDiscoveryBridge,
)
from app.early_movement.scanner.scanner_runtime_config import (
    EarlyMovementScannerRuntimeConfig,
)
from app.early_movement.scanner.scanner_runtime_factory import (
    build_early_movement_scanner_runtime,
    is_extreme_discovery_enabled,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("0", False),
        ("off", False),
        ("", False),
    ],
)
def test_extreme_discovery_environment_values(
    monkeypatch,
    value,
    expected,
):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_DISCOVERY_ENABLED",
        value,
    )

    assert is_extreme_discovery_enabled() is expected


def test_extreme_discovery_disabled_by_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "EXTREME_MOVEMENT_DISCOVERY_ENABLED",
        raising=False,
    )

    assert is_extreme_discovery_enabled() is False


@pytest.mark.parametrize(
    "shadow_enabled,discovery_enabled,expected",
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ],
)
def test_extreme_discovery_requires_both_flags(
    monkeypatch,
    shadow_enabled,
    discovery_enabled,
    expected,
):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        str(shadow_enabled).lower(),
    )
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_DISCOVERY_ENABLED",
        str(discovery_enabled).lower(),
    )

    with patch.object(
        ExtremeMovementShadowConfig,
        "is_enabled",
        wraps=ExtremeMovementShadowConfig.is_enabled,
    ) as shadow_check:
        enabled = (
            ExtremeMovementShadowConfig.is_enabled()
            and is_extreme_discovery_enabled()
        )

    assert enabled is expected
    shadow_check.assert_called_once()


@pytest.mark.parametrize(
    "shadow_enabled,discovery_enabled,expected",
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ],
)
def test_runtime_connects_discovery_only_when_both_enabled(
    monkeypatch,
    shadow_enabled,
    discovery_enabled,
    expected,
):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        str(shadow_enabled).lower(),
    )
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_DISCOVERY_ENABLED",
        str(discovery_enabled).lower(),
    )

    # Sem banco, push ou consultas externas.
    config = EarlyMovementScannerRuntimeConfig(
        enabled=True,
        push_enabled=False,
        database_url=None,
    )

    with patch(
        "app.early_movement.scanner.scanner_runtime_factory."
        "ExtremeMovementDiscoveryBridge",
        wraps=ExtremeMovementDiscoveryBridge,
    ) as bridge_constructor:
        runtime = build_early_movement_scanner_runtime(
            config
        )

    assert runtime is not None

    if expected:
        bridge_constructor.assert_called_once()
    else:
        bridge_constructor.assert_not_called()
