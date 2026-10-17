
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


class EarlyMovementScannerAssetEligibilityFilter:
    EXCLUDED_COIN_IDS = frozenset(
        {
            "tether",
            "usd-coin",
            "dai",
            "first-digital-usd",
            "paypal-usd",
            "ethena-usde",
            "usdd",
            "true-usd",
            "frax",
            "global-dollar",
            "usd1-wlfi",
        }
    )

    EXCLUDED_SYMBOLS = frozenset(
        {
            "USDT",
            "USDC",
            "DAI",
            "FDUSD",
            "PYUSD",
            "USDE",
            "USDD",
            "TUSD",
            "FRAX",
            "USDG",
            "USD1",
        }
    )

    def is_eligible(
        self,
        asset: EarlyMovementScannerMarketAsset,
    ) -> bool:
        coin_id = asset.coin_id.strip().lower()
        symbol = asset.symbol.strip().upper()

        return (
            coin_id not in self.EXCLUDED_COIN_IDS
            and symbol not in self.EXCLUDED_SYMBOLS
        )
