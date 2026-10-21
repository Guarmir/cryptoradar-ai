
import pytest

from app.early_movement.scanner.scanner_runtime_factory import (
    is_scanner_rotation_enabled,
)


@pytest.mark.parametrize(
    "value",
    [
        "true",
        "TRUE",
        "1",
        "yes",
        "on",
        " true ",
    ],
)
def test_rotation_enabled_values(
    monkeypatch,
    value,
):
    monkeypatch.setenv(
        "EARLY_MOVEMENT_SCANNER_ROTATION_ENABLED",
        value,
    )

    assert is_scanner_rotation_enabled() is True


@pytest.mark.parametrize(
    "value",
    [
        "false",
        "FALSE",
        "0",
        "no",
        "off",
        "",
    ],
)
def test_rotation_disabled_values(
    monkeypatch,
    value,
):
    monkeypatch.setenv(
        "EARLY_MOVEMENT_SCANNER_ROTATION_ENABLED",
        value,
    )

    assert is_scanner_rotation_enabled() is False


def test_rotation_disabled_by_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "EARLY_MOVEMENT_SCANNER_ROTATION_ENABLED",
        raising=False,
    )

    assert is_scanner_rotation_enabled() is False
