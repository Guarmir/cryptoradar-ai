from dataclasses import dataclass

from app.early_movement.scanner.scanner_analysis_result import (
    EarlyMovementScannerAnalysisResult,
)
from app.early_movement.scanner.scanner_ranked_result import (
    EarlyMovementScannerRankedResult,
)


@dataclass(frozen=True)
class EarlyMovementScannerRunResult:
    universe_size: int
    candidate_count: int
    analyzed_count: int
    successful_analysis_count: int

    ranked_results: tuple[
        EarlyMovementScannerRankedResult,
        ...,
    ]

    analysis_results: tuple[
        EarlyMovementScannerAnalysisResult,
        ...,
    ] = ()

    @property
    def signal_count(
        self,
    ) -> int:
        return len(
            self.ranked_results,
        )