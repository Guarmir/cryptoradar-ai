from app.early_movement.scanner.scanner_scheduler import (
    EarlyMovementScannerScheduler,
)


class EarlyMovementScannerRuntime:
    def __init__(
        self,
        *,
        scheduler: EarlyMovementScannerScheduler,
    ) -> None:
        self._scheduler = scheduler

    @property
    def scheduler(
        self,
    ) -> EarlyMovementScannerScheduler:
        return self._scheduler

    @property
    def is_running(
        self,
    ) -> bool:
        return self._scheduler.is_running

    def start(
        self,
    ) -> bool:
        return self._scheduler.start()

    def stop(
        self,
        *,
        join_timeout: float = 5,
    ) -> bool:
        return self._scheduler.stop(
            join_timeout=join_timeout,
        )