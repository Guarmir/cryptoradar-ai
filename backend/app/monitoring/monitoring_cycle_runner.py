import threading
from typing import Optional

from app.monitoring.market_event_evaluator import (
    MarketEventEvaluator,
)
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
        market_event_evaluator: Optional[
            MarketEventEvaluator
        ] = None,
    ):
        self._service = service
        self._market_event_evaluator = (
            market_event_evaluator
        )

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

                    market_events = (
                        self._evaluate_market_events(
                            result,
                        )
                    )

                    executions.append(
                        MonitoringTargetExecution.success(
                            result,
                            market_events=market_events,
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

    def _evaluate_market_events(
        self,
        result,
    ):
        evaluator = self._market_event_evaluator

        if evaluator is None:
            return ()

        return evaluator.evaluate(
            result,
        )