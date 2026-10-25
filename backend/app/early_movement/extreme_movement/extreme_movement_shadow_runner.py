from dataclasses import dataclass
from typing import Optional

from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisAdapter,
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)


@dataclass(frozen=True)
class ExtremeMovementShadowResult:
    analyzed_count: int
    evaluated_count: int
    extreme_acceleration_count: int
    movement_pressure_count: int
    possible_reversal_count: int
    insufficient_evidence_count: int
    entries: tuple[
        ExtremeMovementAnalysisEntry,
        ...,
    ] = ()


class ExtremeMovementShadowRunner:
    def __init__(
        self,
        *,
        adapter: Optional[
            ExtremeMovementAnalysisAdapter
        ] = None,
    ) -> None:
        self._adapter = (
            adapter
            if adapter is not None
            else ExtremeMovementAnalysisAdapter()
        )

    def run(
        self,
        scan_result: EarlyMovementScannerRunResult,
    ) -> ExtremeMovementShadowResult:
        entries = self._adapter.adapt(
            scan_result.analysis_results
        )

        states = [
            entry.assessment.state
            for entry in entries
        ]

        return ExtremeMovementShadowResult(
            analyzed_count=scan_result.analyzed_count,
            evaluated_count=len(entries),
            extreme_acceleration_count=states.count(
                "extreme_acceleration"
            ),
            movement_pressure_count=states.count(
                "movement_pressure"
            ),
            possible_reversal_count=states.count(
                "possible_reversal"
            ),
            insufficient_evidence_count=states.count(
                "insufficient_evidence"
            ),
            entries=entries,
        )