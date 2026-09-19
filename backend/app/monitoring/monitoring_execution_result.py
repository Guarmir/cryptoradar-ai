from dataclasses import dataclass
from typing import Optional

from app.monitoring.market_event import MarketEvent
from app.monitoring.monitoring_cycle_result import MonitoringCycleResult


@dataclass(frozen=True)
class MonitoringTargetExecution:
    symbol: str
    cycle_result: Optional[MonitoringCycleResult] = None
    error_message: Optional[str] = None
    market_events: tuple[MarketEvent, ...] = ()

    def __post_init__(self):
        normalized_symbol = self.symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError(
                "O simbolo da execucao nao pode ser vazio."
            )

        object.__setattr__(
            self,
            "symbol",
            normalized_symbol,
        )

        has_result = self.cycle_result is not None
        has_error = self.error_message is not None

        if has_result == has_error:
            raise ValueError(
                "A execucao deve conter exatamente "
                "um resultado ou um erro."
            )

        if (
            self.cycle_result is not None
            and self.cycle_result.target.symbol
            != self.symbol
        ):
            raise ValueError(
                "O resultado deve pertencer "
                "ao mesmo ativo da execucao."
            )

        for event in self.market_events:
            if event.symbol != self.symbol:
                raise ValueError(
                    "Todo evento deve pertencer "
                    "ao mesmo ativo da execucao."
                )

        if self.failed and self.market_events:
            raise ValueError(
                "Uma execucao com falha nao pode "
                "possuir eventos de mercado."
            )

    @property
    def succeeded(self) -> bool:
        return self.cycle_result is not None

    @property
    def failed(self) -> bool:
        return self.error_message is not None

    @property
    def has_market_events(self) -> bool:
        return bool(self.market_events)

    @classmethod
    def success(
        cls,
        cycle_result: MonitoringCycleResult,
        *,
        market_events: tuple[MarketEvent, ...] = (),
    ) -> "MonitoringTargetExecution":
        return cls(
            symbol=cycle_result.target.symbol,
            cycle_result=cycle_result,
            market_events=market_events,
        )

    @classmethod
    def failure(
        cls,
        *,
        symbol: str,
        error: Exception,
    ) -> "MonitoringTargetExecution":
        message = str(error).strip()

        if not message:
            message = error.__class__.__name__

        return cls(
            symbol=symbol,
            error_message=message,
        )


@dataclass(frozen=True)
class MonitoringBatchResult:
    executions: tuple[MonitoringTargetExecution, ...]
    skipped_due_to_overlap: bool = False

    @property
    def execution_count(self) -> int:
        return len(self.executions)

    @property
    def success_count(self) -> int:
        return sum(
            1
            for execution in self.executions
            if execution.succeeded
        )

    @property
    def failure_count(self) -> int:
        return sum(
            1
            for execution in self.executions
            if execution.failed
        )

    @property
    def market_event_count(self) -> int:
        return sum(
            len(execution.market_events)
            for execution in self.executions
        )

    @property
    def has_market_events(self) -> bool:
        return self.market_event_count > 0

    @property
    def has_failures(self) -> bool:
        return self.failure_count > 0

    @property
    def all_succeeded(self) -> bool:
        return (
            not self.skipped_due_to_overlap
            and self.failure_count == 0
        )