import pytest

from app.early_movement.scanner import (
    EarlyMovementScanner,
)


class FakeMarketProvider:
    def __init__(
        self,
        assets,
    ) -> None:
        self.assets = assets
        self.calls = 0

    def fetch(
        self,
    ):
        self.calls += 1
        return self.assets


class FakeCandidateSelector:
    def __init__(
        self,
        candidates,
    ) -> None:
        self.candidates = candidates
        self.calls = []

    def select(
        self,
        assets,
        *,
        limit: int,
    ):
        self.calls.append(
            (
                assets,
                limit,
            )
        )

        return self.candidates


class FakeAnalysisResult:
    def __init__(
        self,
        *,
        analysis,
    ) -> None:
        self.analysis = analysis


class FakeDeepAnalyzer:
    def __init__(
        self,
        results,
    ) -> None:
        self.results = results
        self.calls = []

    def analyze_candidates(
        self,
        candidates,
    ):
        self.calls.append(
            candidates,
        )

        return self.results


class FakeRanker:
    def __init__(
        self,
        ranked,
    ) -> None:
        self.ranked = ranked
        self.calls = []

    def rank(
        self,
        results,
        *,
        limit: int,
    ):
        self.calls.append(
            (
                results,
                limit,
            )
        )

        return self.ranked


def test_scanner_connects_complete_pipeline() -> None:
    assets = (
        object(),
        object(),
        object(),
    )

    candidates = (
        object(),
        object(),
    )

    analysis_results = (
        FakeAnalysisResult(
            analysis=object(),
        ),
        FakeAnalysisResult(
            analysis=object(),
        ),
    )

    ranked = (
        object(),
    )

    market_provider = (
        FakeMarketProvider(
            assets,
        )
    )

    selector = (
        FakeCandidateSelector(
            candidates,
        )
    )

    deep_analyzer = (
        FakeDeepAnalyzer(
            analysis_results,
        )
    )

    ranker = (
        FakeRanker(
            ranked,
        )
    )

    scanner = EarlyMovementScanner(
        market_provider=market_provider,
        candidate_selector=selector,
        deep_analyzer=deep_analyzer,
        result_ranker=ranker,
        candidate_limit=15,
        result_limit=3,
    )

    result = scanner.scan()

    assert market_provider.calls == 1

    assert selector.calls == [
        (
            assets,
            15,
        )
    ]

    assert deep_analyzer.calls == [
        candidates,
    ]

    assert ranker.calls == [
        (
            analysis_results,
            3,
        )
    ]

    assert result.universe_size == 3
    assert result.candidate_count == 2
    assert result.analyzed_count == 2

    assert (
        result.successful_analysis_count
        == 2
    )

    assert result.signal_count == 1
    assert result.ranked_results == ranked


def test_scanner_handles_empty_candidate_set() -> None:
    market_provider = (
        FakeMarketProvider(
            (
                object(),
                object(),
            )
        )
    )

    selector = (
        FakeCandidateSelector(
            (),
        )
    )

    deep_analyzer = (
        FakeDeepAnalyzer(
            (),
        )
    )

    ranker = (
        FakeRanker(
            (),
        )
    )

    scanner = EarlyMovementScanner(
        market_provider=market_provider,
        candidate_selector=selector,
        deep_analyzer=deep_analyzer,
        result_ranker=ranker,
    )

    result = scanner.scan()

    assert result.universe_size == 2
    assert result.candidate_count == 0
    assert result.analyzed_count == 0

    assert (
        result.successful_analysis_count
        == 0
    )

    assert result.signal_count == 0


def test_scanner_counts_partial_analysis_failures() -> None:
    analysis_results = (
        FakeAnalysisResult(
            analysis=object(),
        ),
        FakeAnalysisResult(
            analysis=None,
        ),
        FakeAnalysisResult(
            analysis=object(),
        ),
    )

    scanner = EarlyMovementScanner(
        market_provider=(
            FakeMarketProvider(
                (
                    object(),
                    object(),
                    object(),
                )
            )
        ),
        candidate_selector=(
            FakeCandidateSelector(
                (
                    object(),
                    object(),
                    object(),
                )
            )
        ),
        deep_analyzer=(
            FakeDeepAnalyzer(
                analysis_results,
            )
        ),
        result_ranker=(
            FakeRanker(
                (),
            )
        ),
    )

    result = scanner.scan()

    assert result.analyzed_count == 3

    assert (
        result.successful_analysis_count
        == 2
    )


def test_scanner_rejects_invalid_limits() -> None:
    with pytest.raises(
        ValueError,
        match="candidatos",
    ):
        EarlyMovementScanner(
            candidate_limit=0,
        )

    with pytest.raises(
        ValueError,
        match="resultados",
    ):
        EarlyMovementScanner(
            result_limit=0,
        )

def test_scanner_preserves_followup_between_cycles() -> None:
    from types import SimpleNamespace

    from app.early_movement.scanner.scanner_active_followup import (
        EarlyMovementScannerActiveFollowup,
    )
    from app.early_movement.scanner.scanner_candidate_selector import (
        EarlyMovementScannerCandidateSelector,
    )
    from app.early_movement.scanner.scanner_market_asset import (
        EarlyMovementScannerMarketAsset,
    )

    def make_asset(coin_id, change):
        return EarlyMovementScannerMarketAsset(
            coin_id=coin_id,
            symbol=coin_id.upper(),
            name=coin_id,
            current_price=10.0,
            total_volume=500_000_000,
            market_cap=5_000_000_000,
            price_change_percentage_24h=change,
            market_cap_rank=10,
        )

    class ChangingMarketProvider:
        def __init__(self):
            self.cycle = 0

        def fetch(self):
            self.cycle += 1

            if self.cycle == 1:
                changes = {
                    "akedo": 5.0,
                    "dash": 4.0,
                    "zama": 3.0,
                }
            else:
                changes = {
                    "akedo": 0.5,
                    "dash": 5.0,
                    "zama": 4.0,
                }

            return tuple(
                make_asset(coin_id, change)
                for coin_id, change in changes.items()
            )

    class TrackingAnalyzer:
        def __init__(self):
            self.cycles = []

        def analyze_candidates(self, candidates):
            self.cycles.append(
                tuple(candidate.coin_id for candidate in candidates)
            )

            return tuple(
                SimpleNamespace(
                    candidate=candidate,
                    analysis=object(),
                )
                for candidate in candidates
            )

    class TrackingRanker:
        def rank(self, results, *, limit):
            return tuple(
                SimpleNamespace(result=result)
                for result in results[:limit]
            )

    analyzer = TrackingAnalyzer()
    followup = EarlyMovementScannerActiveFollowup()

    scanner = EarlyMovementScanner(
        market_provider=ChangingMarketProvider(),
        candidate_selector=EarlyMovementScannerCandidateSelector(),
        deep_analyzer=analyzer,
        result_ranker=TrackingRanker(),
        candidate_limit=2,
        result_limit=1,
        active_followup=followup,
    )

    scanner.scan()

    assert analyzer.cycles[0] == ("akedo", "dash")
    assert followup.active_ids() == ()

    # Simula o registro de um ativo aprovado
    # pela decisão de alerta.
    scanner.register_followup(("akedo",))

    assert followup.active_ids() == ("akedo",)

    scanner.scan()

    assert "akedo" in analyzer.cycles[1]
    assert len(analyzer.cycles[1]) == 2
    assert analyzer.cycles[1][0] == "akedo"
