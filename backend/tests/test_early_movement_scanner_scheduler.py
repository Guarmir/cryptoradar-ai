from datetime import (
    datetime,
    timezone,
)

from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecision,
)
from app.early_movement.scanner.scanner_automation_cycle import (
    EarlyMovementScannerAutomationCycleResult,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)
from app.early_movement.scanner.scanner_scheduler import (
    EarlyMovementScannerScheduler,
)


class FakeCycle:
    def __init__(
        self,
        result: EarlyMovementScannerAutomationCycleResult,
    ) -> None:
        self.result = result
        self.call_count = 0

    def run(
        self,
    ) -> EarlyMovementScannerAutomationCycleResult:
        self.call_count += 1

        return self.result


def test_scheduler_runs_cycle_once() -> None:
    scan_result = EarlyMovementScannerRunResult(
        universe_size=100,
        candidate_count=20,
        analyzed_count=20,
        successful_analysis_count=8,
        ranked_results=(),
    )

    decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=False,
            results=(),
        )
    )

    now = datetime.now(
        timezone.utc,
    )

    cycle_result = (
        EarlyMovementScannerAutomationCycleResult(
            started_at=now,
            finished_at=now,
            scan_result=scan_result,
            alert_decision=decision,
        )
    )

    cycle = FakeCycle(
        cycle_result,
    )

    scheduler = EarlyMovementScannerScheduler(
        cycle=cycle,
        interval_seconds=300,
    )

    result = scheduler.run_once()

    assert cycle.call_count == 1
    assert result is cycle_result

    assert (
        scheduler.last_cycle_result
        is cycle_result
    )

    assert (
        scheduler.last_scheduler_error
        is None
    )


def test_scheduler_rejects_invalid_interval() -> None:
    try:
        EarlyMovementScannerScheduler(
            cycle=None,
            interval_seconds=0,
        )

    except ValueError:
        return

    raise AssertionError(
        "Era esperado ValueError."
    )