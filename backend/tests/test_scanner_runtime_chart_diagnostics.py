
from datetime import datetime, timezone
from types import SimpleNamespace

from app.early_movement.scanner.scanner_chart_loader import (
    ScannerChartLoaderStats,
)
from app.early_movement.scanner.scanner_runtime_status import (
    build_early_movement_scanner_runtime_status,
)


def make_runtime(chart_stats):
    now = datetime.now(timezone.utc)

    cycle_result = SimpleNamespace(
        started_at=now,
        finished_at=now,
        signal_count=2,
        should_alert=True,
        push_results=(),
        delivered_push_count=0,
        chart_loader_stats=chart_stats,
    )

    scheduler = SimpleNamespace(
        last_cycle_result=cycle_result,
        interval_seconds=600,
        last_scheduler_error=None,
    )

    return SimpleNamespace(
        scheduler=scheduler,
        is_running=True,
    )


def test_runtime_status_includes_chart_diagnostics():
    stats = ScannerChartLoaderStats(
        cache_hits=3,
        acquisition_attempts=4,
        budget_exhausted=13,
        empty_results=1,
    )

    status = build_early_movement_scanner_runtime_status(
        make_runtime(stats)
    )

    assert status["last_cycle"]["chart_diagnostics"] == {
        "cache_hits": 3,
        "acquisition_attempts": 4,
        "budget_exhausted": 13,
        "empty_results": 1,
    }


def test_runtime_status_without_chart_diagnostics():
    status = build_early_movement_scanner_runtime_status(
        make_runtime(None)
    )

    assert "chart_diagnostics" not in status["last_cycle"]


def test_runtime_status_without_runtime():
    status = build_early_movement_scanner_runtime_status(
        None
    )

    assert status["enabled"] is False
    assert status["last_cycle_available"] is False
