from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


class EarlyMovementScannerAssetEligibilityFilter:
    EXCLUDED_COIN_IDS = frozenset(
        {
            "tether",
            "usd-coin",
        }
    )

    def is_eligible(
        self,
        asset: EarlyMovementScannerMarketAsset,
    ) -> bool:
        return (
            asset.coin_id.lower()
            not in self.EXCLUDED_COIN_IDS
        )