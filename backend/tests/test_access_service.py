import pytest

from app.access.access_entitlements import (
    AccessEntitlements,
)
from app.access.access_entitlements_resolver import (
    AccessEntitlementsResolver,
)
from app.access.access_plan_resolver import (
    AccessPlanResolver,
)
from app.access.access_plan_store import (
    AccessPlanStore,
)
from app.access.access_policy import (
    AccessPolicy,
)
from app.access.access_service import (
    AccessService,
)


class _FakeAccessPlanStore(
    AccessPlanStore
):
    def __init__(
        self,
        plans=None,
    ):
        self.plans = dict(
            plans or {}
        )

    def load_plan(
        self,
        installation_id: str,
    ):
        return self.plans.get(
            installation_id,
        )

    def save_plan(
        self,
        *,
        installation_id: str,
        plan,
    ) -> None:
        self.plans[
            installation_id
        ] = plan


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


def _build_service(
    plans=None,
):
    store = _FakeAccessPlanStore(
        plans,
    )

    plan_resolver = AccessPlanResolver(
        store=store,
    )

    entitlements_resolver = (
        AccessEntitlementsResolver(
            plan_resolver=plan_resolver,
            free_entitlements=(
                _free_entitlements()
            ),
            pro_entitlements=(
                _pro_entitlements()
            ),
        )
    )

    return AccessService(
        entitlements_resolver=(
            entitlements_resolver
        ),
        policy=AccessPolicy(),
    )


def test_missing_plan_uses_free_entitlements():
    service = _build_service()

    entitlements = (
        service.entitlements_for(
            "device-1",
        )
    )

    assert entitlements.is_free
    assert not entitlements.is_pro


def test_pro_plan_uses_pro_entitlements():
    service = _build_service(
        {
            "device-1": "pro",
        }
    )

    entitlements = (
        service.entitlements_for(
            "device-1",
        )
    )

    assert entitlements.is_pro
    assert not entitlements.is_free


def test_free_plan_blocks_automatic_market_alerts():
    service = _build_service()

    assert not (
        service
        .can_use_automatic_market_alerts(
            "device-1",
        )
    )


def test_pro_plan_allows_automatic_market_alerts():
    service = _build_service(
        {
            "device-1": "pro",
        }
    )

    assert (
        service
        .can_use_automatic_market_alerts(
            "device-1",
        )
    )


def test_free_plan_blocks_futures():
    service = _build_service()

    assert not service.can_use_futures(
        "device-1",
    )


def test_pro_plan_allows_futures():
    service = _build_service(
        {
            "device-1": "pro",
        }
    )

    assert service.can_use_futures(
        "device-1",
    )


def test_free_asset_limit_is_enforced():
    service = _build_service()

    assert service.can_monitor_another_asset(
        installation_id="device-1",
        current_monitored_assets=0,
    )

    assert not service.can_monitor_another_asset(
        installation_id="device-1",
        current_monitored_assets=1,
    )


def test_resolver_rejects_wrong_free_entitlements():
    store = _FakeAccessPlanStore()

    plan_resolver = AccessPlanResolver(
        store=store,
    )

    with pytest.raises(ValueError):
        AccessEntitlementsResolver(
            plan_resolver=plan_resolver,
            free_entitlements=(
                _pro_entitlements()
            ),
            pro_entitlements=(
                _pro_entitlements()
            ),
        )


def test_resolver_rejects_wrong_pro_entitlements():
    store = _FakeAccessPlanStore()

    plan_resolver = AccessPlanResolver(
        store=store,
    )

    with pytest.raises(ValueError):
        AccessEntitlementsResolver(
            plan_resolver=plan_resolver,
            free_entitlements=(
                _free_entitlements()
            ),
            pro_entitlements=(
                _free_entitlements()
            ),
        )