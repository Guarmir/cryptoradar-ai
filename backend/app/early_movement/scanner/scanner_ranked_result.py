from dataclasses import dataclass
from typing import Optional

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_analysis_result import (
    EarlyMovementScannerAnalysisResult,
)


@dataclass(frozen=True)
class EarlyMovementScannerRankedResult:
    rank: int
    relevance_score: float
    result: EarlyMovementScannerAnalysisResult

    @property
    def coin_id(
        self,
    ) -> str:
        return self.result.coin_id

    @property
    def symbol(
        self,
    ) -> str:
        return self.result.symbol

    @property
    def name(
        self,
    ) -> str:
        return self.result.name

    @property
    def state(
        self,
    ) -> Optional[
        EarlyMovementState
    ]:
        analysis = self.result.analysis

        if analysis is None:
            return None

        return analysis.evidence.state