import pytest

from app.access.access_plan_resolver import (
    AccessPlanResolver,
)
from app.access.access_plan_store import (
    AccessPlanStore,
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


def test_missing_plan_resolves_to_free():
    resolver = AccessPlanResolver(
        store=_FakeAccessPlanStore(),
    )

    assert (
        resolver.resolve_plan(
            "device-1",
        )
        == "free"
    )


def test_explicit_free_plan_resolves_to_free():
    resolver = AccessPlanResolver(
        store=_FakeAccessPlanStore(
            {
                "device-1": "free",
            }
        ),
    )

    assert (
        resolver.resolve_plan(
            "device-1",
        )
        == "free"
    )


def test_explicit_pro_plan_resolves_to_pro():
    resolver = AccessPlanResolver(
        store=_FakeAccessPlanStore(
            {
                "device-1": "pro",
            }
        ),
    )

    assert (
        resolver.resolve_plan(
            "device-1",
        )
        == "pro"
    )


def test_installation_id_is_normalized():
    resolver = AccessPlanResolver(
        store=_FakeAccessPlanStore(
            {
                "device-1": "pro",
            }
        ),
    )

    assert (
        resolver.resolve_plan(
            "  device-1  ",
        )
        == "pro"
    )


def test_empty_installation_id_is_rejected():
    resolver = AccessPlanResolver(
        store=_FakeAccessPlanStore(),
    )

    with pytest.raises(ValueError):
        resolver.resolve_plan(
            "   ",
        )