from datetime import datetime, timezone

from app.monitoring.market_event_evaluator import (
    MarketEventEvaluator,
)
from app.monitoring.monitoring_cycle_runner import (
    MonitoringCycleRunner,
)
from app.monitoring.monitoring_engine import MonitoringEngine
from app.monitoring.monitoring_observation import (
    MonitoringObservation,
)
from app.monitoring.monitoring_target import MonitoringTarget


class _FakeMonitoringService:
    def __init__(
        self,
        cycle_result,
    ):
        self.registered_symbols = ("BTC",)
        self._cycle_result = cycle_result

    def run_cycle(
        self,
        symbol: str,
    ):
        if symbol != "BTC":
            raise KeyError(symbol)

        return self._cycle_result


def _build_second_observation_result(
    *,
    previous_price: float,
    current_price: float,
):
    engine = MonitoringEngine()

    engine.register_target(
        MonitoringTarget(
            symbol="BTC",
            coin_id="bitcoin",
        )
    )

    engine.observe(
        MonitoringObservation(
            symbol="BTC",
            price=previous_price,
            observed_at=datetime(
                2026,
                9,
                19,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    return engine.observe(
        MonitoringObservation(
            symbol="BTC",
            price=current_price,
            observed_at=datetime(
                2026,
                9,
                19,
                9,
                1,
                tzinfo=timezone.utc,
            ),
        )
    )


def test_runner_preserves_empty_events_without_evaluator():
    cycle_result = _build_second_observation_result(
        previous_price=100.0,
        current_price=102.0,
    )

    service = _FakeMonitoringService(
        cycle_result,
    )

    dispatched = []

    runner = MonitoringCycleRunner(
        service=service,
        market_event_callback=dispatched.append,
    )

    batch = runner.run_once()

    assert batch.success_count == 1
    assert batch.failure_count == 0
    assert batch.market_event_count == 0
    assert not batch.has_market_events
    assert dispatched == []

    execution = batch.executions[0]

    assert execution.succeeded
    assert execution.market_events == ()
    assert not execution.has_market_events


def test_runner_attaches_and_dispatches_detected_market_event():
    cycle_result = _build_second_observation_result(
        previous_price=100.0,
        current_price=102.0,
    )

    service = _FakeMonitoringService(
        cycle_result,
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
    )

    dispatched = []

    runner = MonitoringCycleRunner(
        service=service,
        market_event_evaluator=evaluator,
        market_event_callback=dispatched.append,
    )

    batch = runner.run_once()

    assert batch.success_count == 1
    assert batch.failure_count == 0
    assert batch.market_event_count == 1
    assert batch.has_market_events

    execution = batch.executions[0]

    assert execution.succeeded
    assert execution.has_market_events
    assert len(execution.market_events) == 1

    event = execution.market_events[0]

    assert event.symbol == "BTC"
    assert event.event_type == "price_move_up"
    assert event.previous_price == 100.0
    assert event.current_price == 102.0

    assert dispatched == [
        event,
    ]


def test_runner_keeps_success_without_event_below_threshold():
    cycle_result = _build_second_observation_result(
        previous_price=100.0,
        current_price=100.5,
    )

    service = _FakeMonitoringService(
        cycle_result,
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
    )

    dispatched = []

    runner = MonitoringCycleRunner(
        service=service,
        market_event_evaluator=evaluator,
        market_event_callback=dispatched.append,
    )

    batch = runner.run_once()

    assert batch.success_count == 1
    assert batch.failure_count == 0
    assert batch.market_event_count == 0
    assert not batch.has_market_events
    assert dispatched == []


def test_push_callback_failure_does_not_fail_monitoring_cycle():
    cycle_result = _build_second_observation_result(
        previous_price=100.0,
        current_price=102.0,
    )

    service = _FakeMonitoringService(
        cycle_result,
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
    )

    def failing_callback(
        event,
    ):
        raise RuntimeError(
            "push unavailable"
        )

    runner = MonitoringCycleRunner(
        service=service,
        market_event_evaluator=evaluator,
        market_event_callback=failing_callback,
    )

    batch = runner.run_once()

    assert batch.success_count == 1
    assert batch.failure_count == 0
    assert batch.market_event_count == 1
    assert batch.has_market_events

    execution = batch.executions[0]

    assert execution.succeeded
    assert execution.has_market_events