from typing import Any, Optional

from app.early_movement.scanner.scanner_runtime import (
    EarlyMovementScannerRuntime,
)


def build_early_movement_scanner_runtime_status(
    runtime: Optional[
        EarlyMovementScannerRuntime
    ],
) -> dict[str, Any]:
    if runtime is None:
        return {
            "enabled": False,
            "running": False,
            "interval_seconds": None,
            "last_cycle_available": False,
            "last_scheduler_error": None,
        }

    scheduler = runtime.scheduler

    last_cycle_result = (
        scheduler.last_cycle_result
    )

    status: dict[str, Any] = {
        "enabled": True,
        "running": runtime.is_running,
        "interval_seconds": (
            scheduler.interval_seconds
        ),
        "last_cycle_available": (
            last_cycle_result is not None
        ),
        "last_scheduler_error": (
            scheduler.last_scheduler_error
        ),
    }

    if last_cycle_result is not None:
        status["last_cycle"] = {
            "started_at": (
                last_cycle_result
                .started_at
                .isoformat()
            ),
            "finished_at": (
                last_cycle_result
                .finished_at
                .isoformat()
            ),
            "signal_count": (
                last_cycle_result.signal_count
            ),
            "should_alert": (
                last_cycle_result.should_alert
            ),
            "push_batch_count": (
                len(
                    last_cycle_result.push_results
                )
            ),
            "delivered_push_count": (
                last_cycle_result
                .delivered_push_count
            ),
        }

    return status