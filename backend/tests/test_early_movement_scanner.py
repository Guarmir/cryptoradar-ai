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