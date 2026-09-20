from app.access.access_entitlements import (
    AccessEntitlements,
)
from app.access.access_entitlements_resolver import (
    AccessEntitlementsResolver,
)
from app.access.access_policy import (
    AccessPolicy,
)


class AccessService:
    def __init__(
        self,
        *,
        entitlements_resolver: AccessEntitlementsResolver,
        policy: AccessPolicy,
    ):
        self._entitlements_resolver = (
            entitlements_resolver
        )

        self._policy = policy

    def entitlements_for(
        self,
        installation_id: str,
    ) -> AccessEntitlements:
        return (
            self._entitlements_resolver.resolve(
                installation_id,
            )
        )

    def can_monitor_another_asset(
        self,
        *,
        installation_id: str,
        current_monitored_assets: int,
    ) -> bool:
        entitlements = (
            self.entitlements_for(
                installation_id,
            )
        )

        return (
            self._policy
            .can_monitor_another_asset(
                entitlements=entitlements,
                current_monitored_assets=(
                    current_monitored_assets
                ),
            )
        )

    def can_use_automatic_market_alerts(
        self,
        installation_id: str,
    ) -> bool:
        entitlements = (
            self.entitlements_for(
                installation_id,
            )
        )

        return (
            self._policy
            .can_use_automatic_market_alerts(
                entitlements=entitlements,
            )
        )

    def can_use_futures(
        self,
        installation_id: str,
    ) -> bool:
        entitlements = (
            self.entitlements_for(
                installation_id,
            )
        )

        return (
            self._policy.can_use_futures(
                entitlements=entitlements,
            )
        )