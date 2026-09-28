from dataclasses import dataclass

from app.early_movement.liquidity import (
    EarlyMovementLiquidityAssessment,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


@dataclass(frozen=True)
class EarlyMovementScannerCandidate:
    asset: EarlyMovementScannerMarketAsset
    liquidity: EarlyMovementLiquidityAssessment

    @property
    def coin_id(
        self,
    ) -> str:
        return self.asset.coin_id

    @property
    def symbol(
        self,
    ) -> str:
        return self.asset.symbol

    @property
    def name(
        self,
    ) -> str:
        return self.asset.name