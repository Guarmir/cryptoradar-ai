import pytest

from app.early_movement.scanner import (
    EarlyMovementScannerCandidateSelector,
    EarlyMovementScannerMarketAsset,
)


def _asset(
    *,
    coin_id: str,
    symbol: str,
    total_volume: float | None,
    market_cap: float | None,
    change_24h: float | None,
    rank: int | None,
) -> EarlyMovementScannerMarketAsset:
    return EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=symbol,
        name=coin_id.title(),
        current_price=10.0,
        total_volume=total_volume,
        market_cap=market_cap,
        price_change_percentage_24h=change_24h,
        market_cap_rank=rank,
    )


def test_selector_removes_low_liquidity_assets() -> None:
    selector = (
        EarlyMovementScannerCandidateSelector()
    )

    assets = (
        _asset(
            coin_id="liquid",
            symbol="liq",
            total_volume=300_000_000,
            market_cap=3_000_000_000,
            change_24h=2.0,
            rank=20,
        ),
        _asset(
            coin_id="illiquid",
            symbol="ill",
            total_volume=2_000_000,
            market_cap=200_000_000,
            change_24h=25.0,
            rank=150,
        ),
    )

    result = selector.select(
        assets,
    )

    assert len(result) == 1
    assert result[0].coin_id == "liquid"

    assert (
        result[0].liquidity.score
        is not None
    )

    assert (
        result[0].liquidity.score
        >= 50.0
    )


def test_selector_prioritizes_higher_liquidity() -> None:
    selector = (
        EarlyMovementScannerCandidateSelector()
    )

    assets = (
        _asset(
            coin_id="medium",
            symbol="med",
            total_volume=60_000_000,
            market_cap=3_000_000_000,
            change_24h=8.0,
            rank=40,
        ),
        _asset(
            coin_id="strong",
            symbol="str",
            total_volume=500_000_000,
            market_cap=5_000_000_000,
            change_24h=1.0,
            rank=50,
        ),
    )

    result = selector.select(
        assets,
    )

    assert len(result) == 2
    assert result[0].coin_id == "strong"
    assert result[1].coin_id == "medium"


def test_equal_liquidity_uses_absolute_price_change() -> None:
    selector = (
        EarlyMovementScannerCandidateSelector()
    )

    assets = (
        _asset(
            coin_id="quiet",
            symbol="qui",
            total_volume=500_000_000,
            market_cap=5_000_000_000,
            change_24h=1.0,
            rank=10,
        ),
        _asset(
            coin_id="active",
            symbol="act",
            total_volume=500_000_000,
            market_cap=5_000_000_000,
            change_24h=-6.0,
            rank=30,
        ),
    )

    result = selector.select(
        assets,
    )

    assert result[0].coin_id == "active"
    assert result[1].coin_id == "quiet"


def test_equal_liquidity_and_change_use_market_cap_rank() -> None:
    selector = (
        EarlyMovementScannerCandidateSelector()
    )

    assets = (
        _asset(
            coin_id="rank-twenty",
            symbol="r20",
            total_volume=500_000_000,
            market_cap=5_000_000_000,
            change_24h=3.0,
            rank=20,
        ),
        _asset(
            coin_id="rank-five",
            symbol="r5",
            total_volume=500_000_000,
            market_cap=5_000_000_000,
            change_24h=-3.0,
            rank=5,
        ),
    )

    result = selector.select(
        assets,
    )

    assert result[0].coin_id == "rank-five"
    assert result[1].coin_id == "rank-twenty"


def test_selector_respects_candidate_limit() -> None:
    selector = (
        EarlyMovementScannerCandidateSelector()
    )

    assets = tuple(
        _asset(
            coin_id=f"asset-{index}",
            symbol=f"a{index}",
            total_volume=500_000_000,
            market_cap=5_000_000_000,
            change_24h=float(index),
            rank=index,
        )
        for index in range(
            1,
            6,
        )
    )

    result = selector.select(
        assets,
        limit=3,
    )

    assert len(result) == 3


def test_selector_rejects_invalid_limit() -> None:
    selector = (
        EarlyMovementScannerCandidateSelector()
    )

    with pytest.raises(
        ValueError,
        match="maior que zero",
    ):
        selector.select(
            (),
            limit=0,
        )

def test_selector_excludes_stablecoins_before_candidate_limit() -> None:
    selector = (
        EarlyMovementScannerCandidateSelector()
    )

    assets = (
        _asset(
            coin_id="tether",
            symbol="usdt",
            total_volume=30_000_000_000,
            market_cap=180_000_000_000,
            change_24h=0.01,
            rank=3,
        ),
        _asset(
            coin_id="usd-coin",
            symbol="usdc",
            total_volume=6_000_000_000,
            market_cap=70_000_000_000,
            change_24h=0.02,
            rank=6,
        ),
        _asset(
            coin_id="worldcoin-wld",
            symbol="wld",
            total_volume=400_000_000,
            market_cap=2_000_000_000,
            change_24h=4.0,
            rank=50,
        ),
        _asset(
            coin_id="pump-fun",
            symbol="pump",
            total_volume=300_000_000,
            market_cap=3_000_000_000,
            change_24h=12.0,
            rank=40,
        ),
    )

    result = selector.select(
        assets,
        limit=2,
    )

    assert len(result) == 2

    selected_coin_ids = {
        candidate.coin_id
        for candidate in result
    }

    assert selected_coin_ids == {
        "worldcoin-wld",
        "pump-fun",
    }

    assert "tether" not in selected_coin_ids
    assert "usd-coin" not in selected_coin_ids