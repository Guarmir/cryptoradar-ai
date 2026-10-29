
from typing import Any, Optional

from app.early_movement.scanner.scanner_runtime import (
    EarlyMovementScannerRuntime,
)


def build_early_movement_scanner_runtime_status(
    runtime: Optional[EarlyMovementScannerRuntime],
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
    last_cycle_result = scheduler.last_cycle_result

    status: dict[str, Any] = {
        "enabled": True,
        "running": runtime.is_running,
        "interval_seconds": scheduler.interval_seconds,
        "last_cycle_available": last_cycle_result is not None,
        "last_scheduler_error": scheduler.last_scheduler_error,
    }

    if last_cycle_result is not None:
        last_cycle: dict[str, Any] = {
            "started_at": last_cycle_result.started_at.isoformat(),
            "finished_at": last_cycle_result.finished_at.isoformat(),
            "signal_count": last_cycle_result.signal_count,
            "should_alert": last_cycle_result.should_alert,
            "push_batch_count": len(last_cycle_result.push_results),
            "delivered_push_count": (
                last_cycle_result.delivered_push_count
            ),
        }

        chart_stats = getattr(
            last_cycle_result,
            "chart_loader_stats",
            None,
        )

        if chart_stats is not None:
            last_cycle["chart_diagnostics"] = {
                "cache_hits": chart_stats.cache_hits,
                "acquisition_attempts": chart_stats.acquisition_attempts,
                "budget_exhausted": chart_stats.budget_exhausted,
                "empty_results": chart_stats.empty_results,
            }

        status["last_cycle"] = last_cycle

    # Os testes antigos podem usar agendadores simulados
    # sem a propriedade cycle.
    cycle = getattr(
        scheduler,
        "cycle",
        None,
    )

    if cycle is None:
        return status

    bridge = getattr(
        cycle,
        "_extreme_discovery_bridge",
        None,
    )

    discovery_status: dict[str, Any] = {
        "enabled": bridge is not None,
        "last_run_available": False,
        "last_error": None,
    }

    if bridge is not None:
        last_result = bridge.last_result
        last_error = bridge.last_error

        if last_error is not None:
            discovery_status["last_error"] = (
                last_error.__class__.__name__
            )

        if last_result is not None:
            discovery_status["last_run_available"] = True

            discovery = last_result.discovery

            for field in (
                "universe_size",
                "candidate_count",
                "analyzed_count",
                "successful_analysis_count",
            ):
                if hasattr(discovery, field):
                    discovery_status[field] = getattr(
                        discovery,
                        field,
                    )

            discovery_status["shadow_entry_count"] = len(
                last_result.shadow.entries
            )

    status["extreme_discovery"] = discovery_status

    return status
