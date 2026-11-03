
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

    
def test_records_discovery_candidate_trace():
    provider = FakeMarketProvider(
        [
            make_asset("coin-a", 30),
            make_asset("coin-b", 20),
            make_asset("coin-c", 15),
            make_asset("coin-d", 2),
        ]
    )
    analyzer = FakeDeepAnalyzer()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
        max_analysis_candidates=1,
    )

    result = runner.run(
        excluded_coin_ids={"coin-a"},
    )

    assert result.universe_size == 4
    assert result.excluded_count == 1
    assert result.candidate_count == 2

    assert result.selected_coin_ids == (
        "coin-b",
        "coin-c",
    )

    assert result.submitted_coin_ids == (
        "coin-b",
    )

    assert result.not_submitted_coin_ids == (
        "coin-c",
    )

    assert result.analyzed_count == 1
    assert provider.calls == 1
    assert analyzer.calls == 1

    
class FakeExperimentalComparator:
    def __init__(self):
        self.calls = 0
        self.received = []

    def compare(self, assets):
        self.calls += 1
        self.received.append(tuple(assets))
        return {"cycle": self.calls}


class FailingExperimentalComparator:
    def compare(self, assets):
        raise RuntimeError("Falha experimental simulada")


def test_experimental_comparison_runs_without_changing_selection():
    provider = FakeMarketProvider(
        [
            make_asset("coin-a", 30),
            make_asset("coin-b", 15),
            make_asset("coin-c", 1),
        ]
    )
    analyzer = FakeDeepAnalyzer()
    comparator = FakeExperimentalComparator()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
        experimental_comparator=comparator,
    )

    result = runner.run()

    assert comparator.calls == 1
    assert len(comparator.received[0]) == 3
    assert runner.last_experimental_comparison == {"cycle": 1}
    assert runner.last_experimental_error is None

    assert result.selected_coin_ids == ("coin-a", "coin-b")
    assert result.submitted_coin_ids == ("coin-a", "coin-b")
    assert result.analyzed_count == 2


def test_experimental_comparison_reuses_instance_between_cycles():
    provider = FakeMarketProvider(
        [make_asset("coin-a", 10)]
    )
    analyzer = FakeDeepAnalyzer()
    comparator = FakeExperimentalComparator()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
        experimental_comparator=comparator,
    )

    runner.run()
    runner.run()

    assert comparator.calls == 2
    assert runner.last_experimental_comparison == {"cycle": 2}
    assert provider.calls == 2


def test_experimental_failure_does_not_interrupt_discovery():
    provider = FakeMarketProvider(
        [make_asset("coin-a", 20)]
    )
    analyzer = FakeDeepAnalyzer()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
        experimental_comparator=FailingExperimentalComparator(),
    )

    result = runner.run()

    assert result.analyzed_count == 1
    assert result.submitted_coin_ids == ("coin-a",)
    assert runner.last_experimental_comparison is None
    assert isinstance(
        runner.last_experimental_error,
        RuntimeError,
    )


def test_experimental_comparison_respects_excluded_assets():
    provider = FakeMarketProvider(
        [
            make_asset("coin-a", 30),
            make_asset("coin-b", 20),
        ]
    )
    analyzer = FakeDeepAnalyzer()
    comparator = FakeExperimentalComparator()

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
        experimental_comparator=comparator,
    )

    result = runner.run(
        excluded_coin_ids={"coin-a"},
    )

    assert result.selected_coin_ids == ("coin-b",)
    assert len(comparator.received[0]) == 1
    assert comparator.received[0][0].coin_id == "coin-b"

    

def test_real_comparator_detects_candidate_between_cycles():
    from datetime import datetime, timedelta, timezone

    from app.early_movement.extreme_movement.extreme_movement_candidate_comparator import (
        ExtremeMovementCandidateComparator,
    )
    from app.early_movement.extreme_movement.extreme_movement_candidate_tracker import (
        ExtremeMovementCandidateTracker,
    )

    class ControlledTimeTracker(ExtremeMovementCandidateTracker):
        def __init__(self):
            super().__init__()
            self._times = iter(
                (
                    datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc),
                    datetime(2026, 11, 2, 12, 15, tzinfo=timezone.utc),
                )
            )

        def observe(self, assets, *, observed_at=None):
            return super().observe(
                assets,
                observed_at=next(self._times),
            )

    provider = FakeMarketProvider(
        [
            make_asset("coin-a", 20),
            make_asset("coin-b", 1),
        ]
    )
    analyzer = FakeDeepAnalyzer()

    comparator = ExtremeMovementCandidateComparator(
        tracker=ControlledTimeTracker(),
    )

    runner = ExtremeMovementDiscoveryRunner(
        market_provider=provider,
        deep_analyzer=analyzer,
        experimental_comparator=comparator,
    )

    first = runner.run()

    assert first.selected_coin_ids == ("coin-a",)
    assert (
        runner.last_experimental_comparison.experimental_coin_ids
        == ()
    )

    provider.assets = (
        make_asset("coin-a", 20),
        EarlyMovementScannerMarketAsset(
            coin_id="coin-b",
            symbol="B",
            name="Coin B",
            current_price=1.05,
            total_volume=2_600_000,
            market_cap=10_000_000,
            price_change_percentage_24h=2.0,
        ),
    )

    second = runner.run()
    comparison = runner.last_experimental_comparison

    assert second.selected_coin_ids == ("coin-a",)
    assert comparison is not None
    assert "coin-b" in comparison.experimental_coin_ids
    assert "coin-b" in comparison.experimental_only_coin_ids
    assert runner.last_experimental_error is None
    assert provider.calls == 2
    assert analyzer.calls == 2


