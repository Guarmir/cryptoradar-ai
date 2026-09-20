from app.access.access_entitlements import (
    AccessEntitlements,
)


class AccessPolicy:
    def can_monitor_another_asset(
        self,
        *,
        entitlements: AccessEntitlements,
        current_monitored_assets: int,
    ) -> bool:
        if current_monitored_assets < 0:
            raise ValueError(
                "A quantidade atual de ativos "
                "nao pode ser negativa."
            )

        return (
            current_monitored_assets
            < entitlements.monitored_asset_limit
        )

    def can_use_automatic_market_alerts(
        self,
        *,
        entitlements: AccessEntitlements,
    ) -> bool:
        return entitlements.automatic_market_alerts

    def can_use_futures(
        self,
        *,
        entitlements: AccessEntitlements,
    ) -> bool:
        return entitlements.futures_enabled