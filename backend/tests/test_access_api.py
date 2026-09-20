import pytest
from fastapi import HTTPException

from app.access.access_api import (
    get_access_entitlements,
)
from app.access.access_api_config import (
    AccessApiConfig,
)
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
                AccessEntitlements(
                    plan="free",
                    monitored_asset_limit=1,
                    automatic_market_alerts=False,
                    futures_enabled=False,
                )
            ),
            pro_entitlements=(
                AccessEntitlements(
                    plan="pro",
                    monitored_asset_limit=10,
                    automatic_market_alerts=True,
                    futures_enabled=True,
                )
            ),
        )
    )

    return AccessService(
        entitlements_resolver=(
            entitlements_resolver
        ),
        policy=AccessPolicy(),
    )


def _enabled_config():
    return AccessApiConfig(
        enabled=True,
        database_url="postgresql://test",
        scope_key="access-test",
    )


def test_access_api_is_disabled_by_default():
    with pytest.raises(
        HTTPException
    ) as error:
        get_access_entitlements(
            "device-1",
            config=AccessApiConfig(
                enabled=False,
            ),
            service=_build_service(),
        )

    assert error.value.status_code == 503


def test_missing_plan_returns_free():
    response = get_access_entitlements(
        "device-1",
        config=_enabled_config(),
        service=_build_service(),
    )

    assert response.plan == "free"
    assert response.monitored_asset_limit == 1
    assert not response.automatic_market_alerts
    assert not response.futures_enabled


def test_explicit_pro_returns_pro():
    response = get_access_entitlements(
        "device-1",
        config=_enabled_config(),
        service=_build_service(
            {
                "device-1": "pro",
            }
        ),
    )

    assert response.plan == "pro"
    assert response.monitored_asset_limit == 10
    assert response.automatic_market_alerts
    assert response.futures_enabled


def test_empty_installation_id_returns_422():
    with pytest.raises(
        HTTPException
    ) as error:
        get_access_entitlements(
            "   ",
            config=_enabled_config(),
            service=_build_service(),
        )

    assert error.value.status_code == 422


def test_config_is_disabled_by_default():
    config = (
        AccessApiConfig
        .from_environment(
            {}
        )
    )

    assert not config.enabled


def test_enabled_config_reads_environment():
    config = (
        AccessApiConfig
        .from_environment(
            {
                "CRYPTORADAR_ACCESS_ENABLED":
                    "true",
                "CRYPTORADAR_DATABASE_URL":
                    "postgresql://test",
                "CRYPTORADAR_ACCESS_SCOPE":
                    "production",
            }
        )
    )

    assert config.enabled
    assert config.database_url == "postgresql://test"
    assert config.scope_key == "production"