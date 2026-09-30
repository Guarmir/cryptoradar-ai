from app.early_movement.scanner.scanner_runtime_status import (
    build_early_movement_scanner_runtime_status,
)


def test_runtime_status_when_disabled() -> None:
    status = (
        build_early_movement_scanner_runtime_status(
            None,
        )
    )

    assert status == {
        "enabled": False,
        "running": False,
        "interval_seconds": None,
        "last_cycle_available": False,
        "last_scheduler_error": None,
    }

from datetime import datetime, timezone
from types import SimpleNamespace


def test_runtime_status_with_completed_cycle() -> None:
    started_at = datetime(
        2026,
        9,
        30,
        10,
        0,
        tzinfo=timezone.utc,
    )

    finished_at = datetime(
        2026,
        9,
        30,
        10,
        0,
        5,
        tzinfo=timezone.utc,
    )

    last_cycle_result = SimpleNamespace(
        started_at=started_at,
        finished_at=finished_at,
        signal_count=5,
        should_alert=True,
        push_results=(
            SimpleNamespace(),
            SimpleNamespace(),
        ),
        delivered_push_count=1,
    )

    scheduler = SimpleNamespace(
        interval_seconds=300.0,
        last_cycle_result=last_cycle_result,
        last_scheduler_error=None,
    )

    runtime = SimpleNamespace(
        is_running=True,
        scheduler=scheduler,
    )

    status = (
        build_early_movement_scanner_runtime_status(
            runtime,
        )
    )

    assert status["enabled"] is True
    assert status["running"] is True
    assert status["interval_seconds"] == 300.0
    assert status["last_cycle_available"] is True
    assert status["last_scheduler_error"] is None

    last_cycle = status["last_cycle"]

    assert (
        last_cycle["started_at"]
        == "2026-09-30T10:00:00+00:00"
    )

    assert (
        last_cycle["finished_at"]
        == "2026-09-30T10:00:05+00:00"
    )

    assert last_cycle["signal_count"] == 5
    assert last_cycle["should_alert"] is True
    assert last_cycle["push_batch_count"] == 2
    assert last_cycle["delivered_push_count"] == 1
