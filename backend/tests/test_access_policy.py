import pytest

from app.access.access_entitlements import (
    AccessEntitlements,
)
from app.access.access_policy import (
    AccessPolicy,
)


def _free_entitlements():
    return AccessEntitlements(
        plan="free",
        monitored_asset_limit=1,
        automatic_market_alerts=False,
        futures_enabled=False,
    )


def _pro_entitlements():
    return AccessEntitlements(
        plan="pro",
        monitored_asset_limit=10,
        automatic_market_alerts=True,
        futures_enabled=True,
    )


def test_free_plan_is_identified():
    entitlements = _free_entitlements()

    assert entitlements.is_free
    assert not entitlements.is_pro


def test_pro_plan_is_identified():
    entitlements = _pro_entitlements()

    assert entitlements.is_pro
    assert not entitlements.is_free


def test_rejects_invalid_asset_limit():
    with pytest.raises(ValueError):
        AccessEntitlements(
            plan="free",
            monitored_asset_limit=0,
            automatic_market_alerts=False,
            futures_enabled=False,
        )


def test_allows_asset_below_limit():
    policy = AccessPolicy()

    assert policy.can_monitor_another_asset(
        entitlements=_pro_entitlements(),
        current_monitored_assets=9,
    )


def test_blocks_asset_at_limit():
    policy = AccessPolicy()

    assert not policy.can_monitor_another_asset(
        entitlements=_pro_entitlements(),
        current_monitored_assets=10,
    )


def test_rejects_negative_current_asset_count():
    policy = AccessPolicy()

    with pytest.raises(ValueError):
        policy.can_monitor_another_asset(
            entitlements=_free_entitlements(),
            current_monitored_assets=-1,
        )


def test_free_plan_capabilities():
    policy = AccessPolicy()

    entitlements = _free_entitlements()

    assert not policy.can_use_automatic_market_alerts(
        entitlements=entitlements,
    )

    assert not policy.can_use_futures(
        entitlements=entitlements,
    )


def test_pro_plan_capabilities():
    policy = AccessPolicy()

    entitlements = _pro_entitlements()

    assert policy.can_use_automatic_market_alerts(
        entitlements=entitlements,
    )

    assert policy.can_use_futures(
        entitlements=entitlements,
    )