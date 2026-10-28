
import pytest

from app.early_movement.extreme_movement.extreme_movement_discovery_runner import (
    ExtremeMovementDiscoveryRunner,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


def make_asset(
    coin_id,
    change,
    volume=2_000_000,
    market_cap=10_000_000,
):
    return EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=coin_id.upper(),
        name=coin_id,
        current_price=1.0,
        total_volume=volume,
        market_cap=market_cap,
        price_change_percentage_24h=change,
    )


class FakeMarketProvider:
    def __init__(self, assets):
        self.assets = tuple(assets)
        self.calls = 0

    def fetch(self):
        self.calls += 1
        return self.assets


class FakeDeepAnalyzer:
    def __init__(self):
        self.received = ()
        self.calls = 0

    def analyze_candidates(self, candidates):
        self.calls += 1
        self.received = tuple(candidates)
        return self.received


def test_discovers_and_analyzes_candidates():
    provider = FakeMarketProvider(
        [
            make_asset("coin-a", 15),
            make_asset("coin-b", -20),
            make_asset("coin-c", 3),
        ]
    )
    analyzer = FakeDeepAnalyzer()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
    )

    result = runner.run()

    assert result.universe_size == 3
    assert result.candidate_count == 3
    assert result.analyzed_count == 2
    assert provider.calls == 1
    assert analyzer.calls == 1
    assert {
        candidate.coin_id
        for candidate in analyzer.received
    } == {"coin-a", "coin-b"}


def test_respects_independent_analysis_limit():
    provider = FakeMarketProvider(
        [
            make_asset("coin-a", 30),
            make_asset("coin-b", 20),
            make_asset("coin-c", 15),
        ]
    )
    analyzer = FakeDeepAnalyzer()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
        max_analysis_candidates=1,
    )

    result = runner.run()

    assert result.candidate_count == 3
    assert result.analyzed_count == 1
    assert analyzer.received[0].coin_id == "coin-a"


def test_rejects_invalid_analysis_limit():
    with pytest.raises(ValueError):
        ExtremeMovementDiscoveryRunner(
            market_provider=FakeMarketProvider([]),
            max_analysis_candidates=0,
        )


def test_ignores_assets_without_sufficient_activity():
    provider = FakeMarketProvider(
        [
            make_asset("coin-a", 2),
            make_asset("coin-b", 15, volume=100),
        ]
    )
    analyzer = FakeDeepAnalyzer()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
    )

    result = runner.run()

    assert result.universe_size == 2
    assert result.candidate_count == 0
    assert result.analyzed_count == 0
    assert analyzer.received == ()


def test_preserves_liquidity_information():
    provider = FakeMarketProvider(
        [make_asset("coin-a", 18)]
    )
    analyzer = FakeDeepAnalyzer()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
    )

    runner.run()

    candidate = analyzer.received[0]

    assert candidate.liquidity.available is True
    assert candidate.liquidity.total_volume == 2_000_000
    assert candidate.liquidity.market_cap == 10_000_000

    
def test_excludes_assets_already_analyzed_by_conservative_scanner():
    provider = FakeMarketProvider(
        [
            make_asset("coin-a", 25),
            make_asset("coin-b", 18),
            make_asset("coin-c", 7),
        ]
    )
    analyzer = FakeDeepAnalyzer()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
    )

    result = runner.run(
        excluded_coin_ids={"coin-a", "coin-b"},
    )

    assert result.universe_size == 3
    assert result.candidate_count == 1
    assert result.analyzed_count == 1
    assert analyzer.received[0].coin_id == "coin-c"

