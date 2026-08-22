import threading

from app.monitoring.monitoring_execution_result import (
    MonitoringBatchResult,
    MonitoringTargetExecution,
)
from app.monitoring.monitoring_service import MonitoringService


class MonitoringCycleRunner:
    def __init__(
        self,
        *,
        service: MonitoringService,
    ):
        self._service = service

        self._run_lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._run_lock.locked()

    def run_once(
        self,
    ) -> MonitoringBatchResult:
        acquired = self._run_lock.acquire(
            blocking=False,
        )

        if not acquired:
            return MonitoringBatchResult(
                executions=(),
                skipped_due_to_overlap=True,
            )

        try:
            symbols = tuple(
                self._service.registered_symbols
            )

            executions: list[
                MonitoringTargetExecution
            ] = []

            for symbol in symbols:
                try:
                    result = self._service.run_cycle(
                        symbol,
                    )

                    executions.append(
                        MonitoringTargetExecution.success(
                            result,
                        )
                    )

                except Exception as error:
                    executions.append(
                        MonitoringTargetExecution.failure(
                            symbol=symbol,
                            error=error,
                        )
                    )

            return MonitoringBatchResult(
                executions=tuple(
                    executions,
                ),
            )

        finally:
            self._run_lock.release()