from app.early_movement.scanner.scanner_runtime import (
    EarlyMovementScannerRuntime,
)


class FakeScheduler:
    def __init__(self) -> None:
        self.running = False
        self.start_count = 0
        self.stop_count = 0
        self.last_join_timeout = None

    @property
    def is_running(
        self,
    ) -> bool:
        return self.running

    def start(
        self,
    ) -> bool:
        self.start_count += 1

        if self.running:
            return False

        self.running = True
        return True

    def stop(
        self,
        *,
        join_timeout: float = 5,
    ) -> bool:
        self.stop_count += 1
        self.last_join_timeout = join_timeout

        if not self.running:
            return False

        self.running = False
        return True


def test_runtime_controls_scheduler_lifecycle() -> None:
    scheduler = FakeScheduler()

    runtime = EarlyMovementScannerRuntime(
        scheduler=scheduler,
    )

    assert runtime.scheduler is scheduler
    assert runtime.is_running is False

    assert runtime.start() is True
    assert runtime.is_running is True
    assert scheduler.start_count == 1

    assert (
        runtime.stop(
            join_timeout=2,
        )
        is True
    )

    assert runtime.is_running is False
    assert scheduler.stop_count == 1
    assert scheduler.last_join_timeout == 2