
from collections.abc import Callable
from typing import Optional

from app.early_movement.scanner.coingecko_scanner_market_provider import (
    CoinGeckoEarlyMovementScannerMarketProvider,
)
from app.early_movement.scanner.scanner_candidate import (
    EarlyMovementScannerCandidate,
)
from app.early_movement.scanner.scanner_candidate_selector import (
    EarlyMovementScannerCandidateSelector,
)
from app.early_movement.scanner.scanner_deep_analyzer import (
    EarlyMovementScannerDeepAnalyzer,
)
from app.early_movement.scanner.scanner_result_ranker import (
    EarlyMovementScannerResultRanker,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)


CandidateArranger = Callable[
    [tuple[EarlyMovementScannerCandidate, ...]],
    tuple[EarlyMovementScannerCandidate, ...],
]


class EarlyMovementScanner:
    DEFAULT_CANDIDATE_LIMIT = 20
    DEFAULT_RESULT_LIMIT = 5

    def __init__(
        self,
        *,
        market_provider: Optional[
            CoinGeckoEarlyMovementScannerMarketProvider
        ] = None,
        candidate_selector: Optional[
            EarlyMovementScannerCandidateSelector
        ] = None,
        deep_analyzer: Optional[
            EarlyMovementScannerDeepAnalyzer
        ] = None,
        result_ranker: Optional[
            EarlyMovementScannerResultRanker
        ] = None,
        candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
        result_limit: int = DEFAULT_RESULT_LIMIT,
        candidate_arranger: Optional[
            CandidateArranger
        ] = None,
    ) -> None:
        if candidate_limit < 1:
            raise ValueError(
                "O limite de candidatos deve ser maior que zero."
            )

        if result_limit < 1:
            raise ValueError(
                "O limite de resultados deve ser maior que zero."
            )

        self._market_provider = (
            market_provider
            or CoinGeckoEarlyMovementScannerMarketProvider()
        )

        self._candidate_selector = (
            candidate_selector
            or EarlyMovementScannerCandidateSelector()
        )

        self._deep_analyzer = (
            deep_analyzer
            or EarlyMovementScannerDeepAnalyzer()
        )

        self._result_ranker = (
            result_ranker
            or EarlyMovementScannerResultRanker()
        )

        self._candidate_limit = candidate_limit
        self._result_limit = result_limit
        self._candidate_arranger = candidate_arranger

    def scan(self) -> EarlyMovementScannerRunResult:
        assets = self._market_provider.fetch()

        candidates = self._candidate_selector.select(
            assets,
            limit=self._candidate_limit,
        )

        if self._candidate_arranger is not None:
            candidates = self._candidate_arranger(
                tuple(candidates),
            )

        analysis_results = (
            self._deep_analyzer.analyze_candidates(
                candidates,
            )
        )

        ranked_results = self._result_ranker.rank(
            analysis_results,
            limit=self._result_limit,
        )

        successful_analysis_count = sum(
            1
            for result in analysis_results
            if result.analysis is not None
        )

        return EarlyMovementScannerRunResult(
            universe_size=len(assets),
            candidate_count=len(candidates),
            analyzed_count=len(analysis_results),
            successful_analysis_count=(
                successful_analysis_count
            ),
            analysis_results=analysis_results,
            ranked_results=ranked_results,
        )
