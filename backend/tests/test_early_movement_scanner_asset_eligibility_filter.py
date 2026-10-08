from app.early_movement.scanner.scanner_asset_eligibility_filter import (
    EarlyMovementScannerAssetEligibilityFilter,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


def _asset(
    *,
    coin_id: str,
    symbol: str,
    name: str,
) -> EarlyMovementScannerMarketAsset:
    return EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=symbol,
        name=name,
        current_price=1.0,
    )


def test_excludes_tether() -> None:
    eligibility_filter = (
        EarlyMovementScannerAssetEligibilityFilter()
    )

    asset = _asset(
        coin_id="tether",
        symbol="USDT",
        name="Tether",
    )

    assert (
        eligibility_filter.is_eligible(
            asset,
        )
        is False
    )


def test_excludes_usd_coin() -> None:
    eligibility_filter = (
        EarlyMovementScannerAssetEligibilityFilter()
    )

    asset = _asset(
        coin_id="usd-coin",
        symbol="USDC",
        name="USDC",
    )

    assert (
        eligibility_filter.is_eligible(
            asset,
        )
        is False
    )


def test_keeps_operational_crypto_assets() -> None:
    eligibility_filter = (
        EarlyMovementScannerAssetEligibilityFilter()
    )

    assets = (
        _asset(
            coin_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
        ),
        _asset(
            coin_id="worldcoin-wld",
            symbol="WLD",
            name="Worldcoin",
        ),
        _asset(
            coin_id="pump-fun",
            symbol="PUMP",
            name="Pump.fun",
        ),
    )

    assert all(
        eligibility_filter.is_eligible(
            asset,
        )
        for asset in assets
    )