import pytest

from app.early_movement.scanner.scanner_runtime_config import (
    EarlyMovementScannerRuntimeConfig,
)


def test_runtime_config_defaults_disabled() -> None:
    config = (
        EarlyMovementScannerRuntimeConfig
        .from_environment({})
    )

    assert config.enabled is False
    assert config.interval_seconds == 300.0

    assert config.push_enabled is False
    assert (
        config.push_cooldown_seconds
        == 3600.0
    )

    assert config.database_url is None
    assert config.push_scope_key is None


def test_runtime_config_reads_environment() -> None:
    config = (
        EarlyMovementScannerRuntimeConfig
        .from_environment(
            {
                (
                    "CRYPTORADAR_EARLY_MOVEMENT_"
                    "SCANNER_ENABLED"
                ): "true",
                (
                    "CRYPTORADAR_EARLY_MOVEMENT_"
                    "SCANNER_INTERVAL_SECONDS"
                ): "120",
                (
                    "CRYPTORADAR_EARLY_MOVEMENT_"
                    "SCANNER_PUSH_ENABLED"
                ): "true",
                (
                    "CRYPTORADAR_EARLY_MOVEMENT_"
                    "SCANNER_PUSH_COOLDOWN_SECONDS"
                ): "600",
                "CRYPTORADAR_DATABASE_URL": (
                    "postgresql://test"
                ),
                "CRYPTORADAR_PUSH_SCOPE": (
                    "test-scope"
                ),
            }
        )
    )

    assert config.enabled is True
    assert config.interval_seconds == 120.0

    assert config.push_enabled is True
    assert (
        config.push_cooldown_seconds
        == 600.0
    )

    assert (
        config.database_url
        == "postgresql://test"
    )

    assert (
        config.push_scope_key
        == "test-scope"
    )


def test_runtime_config_rejects_invalid_enabled() -> None:
    with pytest.raises(
        ValueError,
    ):
        (
            EarlyMovementScannerRuntimeConfig
            .from_environment(
                {
                    (
                        "CRYPTORADAR_EARLY_MOVEMENT_"
                        "SCANNER_ENABLED"
                    ): "talvez",
                }
            )
        )


def test_runtime_config_rejects_invalid_interval() -> None:
    with pytest.raises(
        ValueError,
    ):
        (
            EarlyMovementScannerRuntimeConfig
            .from_environment(
                {
                    (
                        "CRYPTORADAR_EARLY_MOVEMENT_"
                        "SCANNER_INTERVAL_SECONDS"
                    ): "0",
                }
            )
        )


def test_runtime_config_requires_database_for_push() -> None:
    with pytest.raises(
        ValueError,
    ):
        (
            EarlyMovementScannerRuntimeConfig
            .from_environment(
                {
                    (
                        "CRYPTORADAR_EARLY_MOVEMENT_"
                        "SCANNER_PUSH_ENABLED"
                    ): "true",
                    "CRYPTORADAR_PUSH_SCOPE": (
                        "test-scope"
                    ),
                }
            )
        )


def test_runtime_config_requires_scope_for_push() -> None:
    with pytest.raises(
        ValueError,
    ):
        (
            EarlyMovementScannerRuntimeConfig
            .from_environment(
                {
                    (
                        "CRYPTORADAR_EARLY_MOVEMENT_"
                        "SCANNER_PUSH_ENABLED"
                    ): "true",
                    "CRYPTORADAR_DATABASE_URL": (
                        "postgresql://test"
                    ),
                }
            )
        )