from app.ai.asset_market_context_assessment import (
    calculate_asset_market_context,
)
from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)


def _asset(
    symbol: str,
    change: float | None,
) -> MarketOverviewAsset:
    return MarketOverviewAsset(
        symbol=symbol,
        name=symbol,
        price_usd=100.0,
        change_24h_percent=change,
        market_cap_usd=1_000_000_000.0,
        volume_24h_usd=100_000_000.0,
    )


def test_market_context_is_favorable():
    snapshot = MarketOverviewSnapshot(
        total_market_cap_usd=3_000_000_000_000.0,
        total_volume_24h_usd=150_000_000_000.0,
        market_cap_change_24h_percent=1.20,
        btc_dominance_percent=57.50,
        eth_dominance_percent=12.0,
        assets=(
            _asset("BTC", 1.40),
            _asset("ETH", 2.00),
            _asset("SOL", 3.00),
            _asset("XRP", 0.80),
        ),
    )

    result = calculate_asset_market_context(
        asset_change_24h_percent=3.00,
        snapshot=snapshot,
    )

    assert result.state == "favorable"
    assert result.btc_state == "positive"
    assert result.market_state == "positive"
    assert result.breadth_state == "positive"

    assert (
        result.relative_strength_state
        == "outperforming"
    )

    assert result.btc_change_24h_percent == 1.40

    assert (
        result.relative_change_vs_btc_pp
        == 1.60
    )


def test_market_context_is_unfavorable():
    snapshot = MarketOverviewSnapshot(
        total_market_cap_usd=3_000_000_000_000.0,
        total_volume_24h_usd=150_000_000_000.0,
        market_cap_change_24h_percent=-1.40,
        btc_dominance_percent=58.0,
        eth_dominance_percent=11.5,
        assets=(
            _asset("BTC", -2.00),
            _asset("ETH", -1.50),
            _asset("SOL", -3.00),
            _asset("XRP", 0.40),
        ),
    )

    result = calculate_asset_market_context(
        asset_change_24h_percent=-3.50,
        snapshot=snapshot,
    )

    assert result.state == "unfavorable"
    assert result.btc_state == "negative"
    assert result.market_state == "negative"
    assert result.breadth_state == "negative"

    assert (
        result.relative_strength_state
        == "underperforming"
    )

    assert (
        result.relative_change_vs_btc_pp
        == -1.50
    )


def test_market_context_can_be_mixed():
    snapshot = MarketOverviewSnapshot(
        total_market_cap_usd=3_000_000_000_000.0,
        total_volume_24h_usd=150_000_000_000.0,
        market_cap_change_24h_percent=-0.10,
        btc_dominance_percent=56.0,
        eth_dominance_percent=12.5,
        assets=(
            _asset("BTC", 0.20),
            _asset("ETH", 0.30),
            _asset("SOL", -0.20),
            _asset("XRP", -0.40),
        ),
    )

    result = calculate_asset_market_context(
        asset_change_24h_percent=0.50,
        snapshot=snapshot,
    )

    assert result.state == "mixed"
    assert result.btc_state == "neutral"
    assert result.market_state == "neutral"
    assert result.breadth_state == "balanced"

    assert (
        result.relative_strength_state
        == "aligned"
    )


def test_market_context_handles_missing_btc():
    snapshot = MarketOverviewSnapshot(
        total_market_cap_usd=3_000_000_000_000.0,
        total_volume_24h_usd=150_000_000_000.0,
        market_cap_change_24h_percent=1.00,
        btc_dominance_percent=57.0,
        eth_dominance_percent=12.0,
        assets=(
            _asset("ETH", 2.00),
            _asset("SOL", 1.50),
            _asset("XRP", 0.80),
        ),
    )

    result = calculate_asset_market_context(
        asset_change_24h_percent=2.50,
        snapshot=snapshot,
    )

    assert result.state == "favorable"
    assert result.btc_state == "unavailable"

    assert (
        result.relative_strength_state
        == "unavailable"
    )

    assert result.btc_change_24h_percent is None
    assert result.relative_change_vs_btc_pp is None


def test_btc_dominance_is_context_not_direction():
    snapshot = MarketOverviewSnapshot(
        total_market_cap_usd=3_000_000_000_000.0,
        total_volume_24h_usd=150_000_000_000.0,
        market_cap_change_24h_percent=0.0,
        btc_dominance_percent=70.0,
        eth_dominance_percent=10.0,
        assets=(
            _asset("BTC", 0.0),
            _asset("ETH", 0.0),
        ),
    )

    result = calculate_asset_market_context(
        asset_change_24h_percent=0.0,
        snapshot=snapshot,
    )

    assert result.state == "mixed"
    assert result.btc_dominance_percent == 70.0