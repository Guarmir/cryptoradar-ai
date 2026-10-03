import threading
from typing import Callable, Optional

from app.monitoring.market_event import (
    MarketEvent,
)
from app.monitoring.market_event_evaluator import (
    MarketEventEvaluator,
)
from app.monitoring.monitoring_cycle_result import (
    MonitoringCycleResult,
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
        market_event_callback: Optional[
            Callable[[MarketEvent], object]
        ] = None,
    ):
        self._service = service
        self._market_event_evaluator = (
            market_event_evaluator
        )
        self._market_event_callback = (
            market_event_callback
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

            fetch_batch = getattr(
                self._service,
                "fetch_market_data_batch",
                None,
            )

            batch_market_data = None

            if callable(fetch_batch):
                try:
                    batch_market_data = fetch_batch(
                        symbols,
                    )
                except Exception:
                    batch_market_data = None

            for symbol in symbols:
                try:
                    if (
                        batch_market_data is not None
                        and symbol in batch_market_data
                    ):
                        result = (
                            self._service.observe_market_data(
                                symbol,
                                batch_market_data[symbol],
                            )
                        )
                    else:
                        result = self._service.run_cycle(
                            symbol,
                        )

                    market_events = (
                        self._evaluate_market_events(
                            result,
                        )
                    )

                    self._dispatch_market_events(
                        market_events,
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
        result: MonitoringCycleResult,
    ) -> tuple[MarketEvent, ...]:
        evaluator = self._market_event_evaluator

        if evaluator is None:
            return ()

        return evaluator.evaluate(
            result,
        )

    def _dispatch_market_events(
        self,
        events: tuple[MarketEvent, ...],
    ) -> None:
        callback = self._market_event_callback

        if callback is None:
            return

        for event in events:
            try:
                callback(
                    event,
                )
            except Exception:
                # Uma falha na entrega de notificacao
                # nao pode interromper o monitoramento.
                continue