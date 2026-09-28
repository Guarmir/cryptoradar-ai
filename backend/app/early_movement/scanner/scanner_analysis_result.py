from dataclasses import dataclass
from typing import Optional

from app.early_movement.early_movement_analyzer import (
    EarlyMovementAnalysis,
)
from app.early_movement.scanner.scanner_candidate import (
    EarlyMovementScannerCandidate,
)


@dataclass(frozen=True)
class EarlyMovementScannerAnalysisResult:
    candidate: EarlyMovementScannerCandidate

    analysis: Optional[
        EarlyMovementAnalysis
    ] = None

    chart_available: bool = False

    error: Optional[str] = None

    @property
    def coin_id(
        self,
    ) -> str:
        return self.candidate.coin_id

    @property
    def symbol(
        self,
    ) -> str:
        return self.candidate.symbol

    @property
    def name(
        self,
    ) -> str:
        return self.candidate.name