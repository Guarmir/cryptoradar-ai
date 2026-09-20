import pytest

from app.access.access_entitlements_config import (
    AccessEntitlementsConfig,
)


def test_default_configuration():
    config = (
        AccessEntitlementsConfig
        .from_environment(
            {}
        )
    )

    assert config.free.plan == "free"
    assert config.free.monitored_asset_limit == 1
    assert not config.free.automatic_market_alerts
    assert not config.free.futures_enabled

    assert config.pro.plan == "pro"
    assert config.pro.monitored_asset_limit == 10
    assert config.pro.automatic_market_alerts
    assert config.pro.futures_enabled


def test_custom_configuration():
    config = (
        AccessEntitlementsConfig
        .from_environment(
            {
                "CRYPTORADAR_FREE_MONITORED_ASSET_LIMIT":
                    "2",
                "CRYPTORADAR_FREE_AUTOMATIC_MARKET_ALERTS":
                    "true",
                "CRYPTORADAR_FREE_FUTURES_ENABLED":
                    "false",
                "CRYPTORADAR_PRO_MONITORED_ASSET_LIMIT":
                    "20",
                "CRYPTORADAR_PRO_AUTOMATIC_MARKET_ALERTS":
                    "true",
                "CRYPTORADAR_PRO_FUTURES_ENABLED":
                    "true",
            }
        )
    )

    assert config.free.monitored_asset_limit == 2
    assert config.free.automatic_market_alerts
    assert not config.free.futures_enabled

    assert config.pro.monitored_asset_limit == 20
    assert config.pro.automatic_market_alerts
    assert config.pro.futures_enabled


def test_rejects_invalid_asset_limit():
    with pytest.raises(ValueError):
        (
            AccessEntitlementsConfig
            .from_environment(
                {
                    "CRYPTORADAR_FREE_MONITORED_ASSET_LIMIT":
                        "0",
                }
            )
        )


def test_rejects_non_integer_asset_limit():
    with pytest.raises(ValueError):
        (
            AccessEntitlementsConfig
            .from_environment(
                {
                    "CRYPTORADAR_PRO_MONITORED_ASSET_LIMIT":
                        "abc",
                }
            )
        )


def test_rejects_invalid_boolean():
    with pytest.raises(ValueError):
        (
            AccessEntitlementsConfig
            .from_environment(
                {
                    "CRYPTORADAR_FREE_FUTURES_ENABLED":
                        "talvez",
                }
            )
        )