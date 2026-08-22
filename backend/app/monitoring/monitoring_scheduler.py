import threading
from typing import Optional

from app.monitoring.monitoring_cycle_runner import (
    MonitoringCycleRunner,
)
from app.monitoring.monitoring_execution_result import (
    MonitoringBatchResult,
)


class MonitoringScheduler:
    def __init__(
        self,
        *,
        runner: MonitoringCycleRunner,
        interval_seconds: float = 60,
    ):
        if interval_seconds <= 0:
            raise ValueError(
                "O intervalo deve ser maior que zero."
            )

        self._runner = runner
        self._interval_seconds = float(
            interval_seconds,
        )

        self._stop_event = threading.Event()

        self._thread: Optional[
            threading.Thread
        ] = None

        self._lifecycle_lock = threading.Lock()

        self._last_batch_result: Optional[
            MonitoringBatchResult
        ] = None

        self._last_scheduler_error: Optional[
            str
        ] = None

    @property
    def interval_seconds(self) -> float:
        return self._interval_seconds

    @property
    def is_running(self) -> bool:
        thread = self._thread

        return (
            thread is not None
            and thread.is_alive()
        )

    @property
    def last_batch_result(
        self,
    ) -> Optional[MonitoringBatchResult]:
        return self._last_batch_result

    @property
    def last_scheduler_error(
        self,
    ) -> Optional[str]:
        return self._last_scheduler_error

    def start(self) -> bool:
        with self._lifecycle_lock:
            if self.is_running:
                return False

            self._stop_event.clear()

            self._thread = threading.Thread(
                target=self._run_loop,
                name="cryptoradar-monitoring",
                daemon=True,
            )

            self._thread.start()

            return True

    def stop(
        self,
        *,
        join_timeout: float = 5,
    ) -> bool:
        with self._lifecycle_lock:
            thread = self._thread

            if (
                thread is None
                or not thread.is_alive()
            ):
                self._thread = None
                return False

            self._stop_event.set()

        if (
            thread is not threading.current_thread()
        ):
            thread.join(
                timeout=max(
                    0,
                    join_timeout,
                )
            )

        with self._lifecycle_lock:
            if not thread.is_alive():
                self._thread = None

        return True

    def run_once(
        self,
    ) -> MonitoringBatchResult:
        result = self._runner.run_once()

        self._last_batch_result = result
        self._last_scheduler_error = None

        return result

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()

            except Exception as error:
                message = str(error).strip()

                self._last_scheduler_error = (
                    message
                    or error.__class__.__name__
                )

            should_stop = self._stop_event.wait(
                self._interval_seconds,
            )

            if should_stop:
                break