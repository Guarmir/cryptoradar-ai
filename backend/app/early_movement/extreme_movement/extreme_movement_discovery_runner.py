
from dataclasses import dataclass
from typing import Any, Optional

from app.early_movement.extreme_movement.extreme_movement_candidate_selector import (
    ExtremeMovementCandidateSelector,
)
from app.early_movement.liquidity.liquidity_evaluator import (
    EarlyMovementLiquidityEvaluator,
)
from app.early_movement.scanner.scanner_candidate import (
    EarlyMovementScannerCandidate,
)
from app.early_movement.scanner.scanner_chart_loader import (
    EarlyMovementScannerChartLoader,
)
from app.early_movement.scanner.scanner_deep_analyzer import (
    EarlyMovementScannerDeepAnalyzer,
)


@dataclass(frozen=True)
class ExtremeMovementDiscoveryResult:
    universe_size: int
    candidate_count: int
    analyzed_count: int
    analysis_results: tuple


class ExtremeMovementDiscoveryRunner:
    def __init__(
        self,
        *,
        market_provider: Any,
        candidate_selector: Optional[
            ExtremeMovementCandidateSelector
        ] = None,
        liquidity_evaluator: Optional[
            EarlyMovementLiquidityEvaluator
        ] = None,
        deep_analyzer: Optional[
            EarlyMovementScannerDeepAnalyzer
        ] = None,
        max_analysis_candidates: int = 2,
    ) -> None:
        if max_analysis_candidates < 1:
            raise ValueError(
                "max_analysis_candidates deve ser positivo."
            )

        self._market_provider = market_provider

        self._candidate_selector = (
            candidate_selector
            if candidate_selector is not None
            else ExtremeMovementCandidateSelector(
                min_absolute_change_24h=3.0,
                min_total_volume=100_000.0,
            )
        )

        self._liquidity_evaluator = (
            liquidity_evaluator
            if liquidity_evaluator is not None
            else EarlyMovementLiquidityEvaluator()
        )

        self._chart_loader: Optional[
            EarlyMovementScannerChartLoader
        ] = None

        if deep_analyzer is not None:
            self._deep_analyzer = deep_analyzer
        else:
            self._chart_loader = (
                EarlyMovementScannerChartLoader(
                    request_budget=2,
                )
            )

            self._deep_analyzer = (
                EarlyMovementScannerDeepAnalyzer(
                    chart_loader=self._chart_loader,
                    max_chart_age_seconds=7200,
                )
            )

        self._max_analysis_candidates = (
            max_analysis_candidates
        )

    def run(
        self,
        *,
        excluded_coin_ids: Optional[
            set[str]
        ] = None,
    ) -> ExtremeMovementDiscoveryResult:

        if self._chart_loader is not None:
            self._chart_loader.reset_budget()

        assets = tuple(
            self._market_provider.fetch()
        )

        excluded = (
            excluded_coin_ids
            if excluded_coin_ids is not None
            else set()
        )

        eligible_assets = tuple(
            asset
            for asset in assets
            if asset.coin_id not in excluded
        )

        selected = tuple(
            self._candidate_selector.select(
                eligible_assets
            )
        )

        candidates = []

        for item in selected:
            if (
                len(candidates)
                >= self._max_analysis_candidates
            ):
                break

            asset = item.asset

            liquidity = (
                self._liquidity_evaluator.evaluate(
                    {
                        "total_volume": (
                            asset.total_volume
                        ),
                        "market_cap": (
                            asset.market_cap
                        ),
                    }
                )
            )

            if not liquidity.available:
                continue

            candidates.append(
                EarlyMovementScannerCandidate(
                    asset=asset,
                    liquidity=liquidity,
                )
            )

        analysis_results = tuple(
            self._deep_analyzer.analyze_candidates(
                candidates
            )
        )

        return ExtremeMovementDiscoveryResult(
            universe_size=len(assets),
            candidate_count=len(selected),
            analyzed_count=len(analysis_results),
            analysis_results=analysis_results,
        )
