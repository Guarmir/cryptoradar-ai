import threading

from app.monitoring.monitoring_scheduler import (
    MonitoringScheduler,
)
from app.monitoring.monitoring_service import (
    MonitoringService,
)


class MonitoringRuntime:
    def __init__(
        self,
        *,
        service: MonitoringService,
        scheduler: MonitoringScheduler,
    ):
        self._service = service
        self._scheduler = scheduler

        self._lifecycle_lock = (
            threading.Lock()
        )

        self._started = False
        self._restored_state_count = 0

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def is_running(self) -> bool:
        return (
            self._started
            and self._scheduler.is_running
        )

    @property
    def restored_state_count(
        self,
    ) -> int:
        return self._restored_state_count

    @property
    def target_count(self) -> int:
        return self._service.target_count

    @property
    def registered_symbols(
        self,
    ) -> tuple[str, ...]:
        return self._service.registered_symbols

    def start(self) -> bool:
        with self._lifecycle_lock:
            if self._started:
                return False

            restored_states = (
                self._service.restore_from_store()
            )

            scheduler_started = (
                self._scheduler.start()
            )

            if (
                not scheduler_started
                and not self._scheduler.is_running
            ):
                raise RuntimeError(
                    "O scheduler de monitoramento "
                    "não pôde ser iniciado."
                )

            self._restored_state_count = len(
                restored_states,
            )

            self._started = True

            return True

    def stop(self) -> bool:
        with self._lifecycle_lock:
            if not self._started:
                return False

            self._scheduler.stop()

            self._started = False

            return True