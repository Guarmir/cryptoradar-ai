from app.access.access_entitlements import (
    AccessEntitlements,
)
from app.access.access_plan_resolver import (
    AccessPlanResolver,
)


class AccessEntitlementsResolver:
    def __init__(
        self,
        *,
        plan_resolver: AccessPlanResolver,
        free_entitlements: AccessEntitlements,
        pro_entitlements: AccessEntitlements,
    ):
        if not free_entitlements.is_free:
            raise ValueError(
                "Os direitos FREE devem pertencer "
                "ao plano free."
            )

        if not pro_entitlements.is_pro:
            raise ValueError(
                "Os direitos PRO devem pertencer "
                "ao plano pro."
            )

        self._plan_resolver = (
            plan_resolver
        )

        self._free_entitlements = (
            free_entitlements
        )

        self._pro_entitlements = (
            pro_entitlements
        )

    def resolve(
        self,
        installation_id: str,
    ) -> AccessEntitlements:
        plan = (
            self._plan_resolver.resolve_plan(
                installation_id,
            )
        )

        if plan == "free":
            return self._free_entitlements

        if plan == "pro":
            return self._pro_entitlements

        raise ValueError(
            "Plano de acesso nao suportado."
        )