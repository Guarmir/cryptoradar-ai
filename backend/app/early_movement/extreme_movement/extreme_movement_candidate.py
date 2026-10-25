from dataclasses import dataclass

from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


@dataclass(frozen=True)
class ExtremeMovementCandidate:
    asset: EarlyMovementScannerMarketAsset
    absolute_change_24h: float
    direction: str
    activity_score: float

    @property
    def coin_id(self) -> str:
        return self.asset.coin_id