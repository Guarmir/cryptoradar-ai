
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)


class ExtremeMovementCollectionHealth:
    @staticmethod
    def is_healthy(
        result: EarlyMovementScannerRunResult,
    ) -> bool:
        if result.universe_size <= 0:
            return False

        if result.candidate_count <= 0:
            return False

        if result.analyzed_count <= 0:
            return False

        if result.successful_analysis_count <= 0:
            return False

        return True
