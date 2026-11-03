
from types import SimpleNamespace
from unittest.mock import Mock

from app.early_movement.extreme_movement.extreme_movement_discovery_bridge import (
    ExtremeMovementDiscoveryBridge,
)
from app.early_movement.extreme_movement.extreme_movement_discovery_schedule import (
    ExtremeMovementDiscoverySchedule,
)
from app.early_movement.extreme_movement.extreme_movement_discovery_trace import (
    ExtremeMovementDiscoveryTrace,
)


class FakeDiscoveryRunner:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def run(self, *, excluded_coin_ids=None):
        self.calls.append(set(excluded_coin_ids or set()))

        if self.fail:
            raise RuntimeError("Falha simulada na descoberta")

        return SimpleNamespace(
            universe_size=500,
            candidate_count=3,
            analyzed_count=2,
            excluded_count=1,
            selected_coin_ids=("coin-a", "coin-b", "coin-c"),
            submitted_coin_ids=("coin-a", "coin-b"),
            not_submitted_coin_ids=("coin-c",),
            analysis_results=("analysis-a",),
        )


class FakeShadowRunner:
    def __init__(self):
        self.calls = []

    def run_analysis_results(self, analysis_results):
        self.calls.append(analysis_results)
        return SimpleNamespace(entries=("entry-a",))


def make_bridge(
    discovery,
    shadow,
    *,
    clock=None,
    trace_store=None,
):
    if clock is None:
        clock = [0.0]

    return ExtremeMovementDiscoveryBridge(
        discovery_runner=discovery,
        shadow_runner=shadow,
        trace_store=trace_store,
        schedule=ExtremeMovementDiscoverySchedule(
            interval_seconds=900,
            clock=lambda: clock[0],
        ),
    )


def test_bridge_runs_when_due_and_excludes_existing_coins():
    clock = [0.0]
    discovery = FakeDiscoveryRunner()
    shadow = FakeShadowRunner()

    bridge = make_bridge(
        discovery,
        shadow,
        clock=clock,
    )

    result = bridge.run_if_due(
        excluded_coin_ids={"bitcoin", "ethereum"},
    )

    assert result is not None
    assert discovery.calls == [{"bitcoin", "ethereum"}]
    assert shadow.calls == [("analysis-a",)]
    assert result.shadow.entries == ("entry-a",)

    assert bridge.run_if_due() is None
    assert len(discovery.calls) == 1

    clock[0] = 900.0

    assert bridge.run_if_due() is not None
    assert len(discovery.calls) == 2


def test_bridge_isolates_discovery_failures():
    clock = [0.0]
    discovery = FakeDiscoveryRunner(fail=True)
    shadow = FakeShadowRunner()

    bridge = make_bridge(
        discovery,
        shadow,
        clock=clock,
    )

    assert bridge.run_if_due() is None
    assert isinstance(bridge.last_error, RuntimeError)
    assert shadow.calls == []

    clock[0] = 100.0

    assert bridge.run_if_due() is None
    assert len(discovery.calls) == 1


def test_bridge_saves_discovery_trace():
    discovery = FakeDiscoveryRunner()
    shadow = FakeShadowRunner()
    trace_store = Mock()

    bridge = make_bridge(
        discovery,
        shadow,
        trace_store=trace_store,
    )

    result = bridge.run_if_due()

    assert result is not None
    assert bridge.last_error is None
    assert bridge.last_trace_error is None

    trace_store.save.assert_called_once()

    trace = trace_store.save.call_args.args[0]

    assert isinstance(trace, ExtremeMovementDiscoveryTrace)
    assert trace.universe_size == 500
    assert trace.candidate_count == 3
    assert trace.analyzed_count == 2
    assert trace.excluded_count == 1
    assert trace.selected_coin_ids == (
        "coin-a",
        "coin-b",
        "coin-c",
    )
    assert trace.submitted_coin_ids == (
        "coin-a",
        "coin-b",
    )
    assert trace.not_submitted_coin_ids == ("coin-c",)

    assert shadow.calls == [("analysis-a",)]


def test_bridge_continues_when_trace_storage_fails():
    discovery = FakeDiscoveryRunner()
    shadow = FakeShadowRunner()
    trace_store = Mock()

    trace_store.save.side_effect = RuntimeError(
        "Falha simulada no Neon"
    )

    bridge = make_bridge(
        discovery,
        shadow,
        trace_store=trace_store,
    )

    result = bridge.run_if_due()

    assert result is not None
    assert result.shadow.entries == ("entry-a",)
    assert bridge.last_error is None

    assert isinstance(
        bridge.last_trace_error,
        RuntimeError,
    )

    trace_store.save.assert_called_once()
    assert shadow.calls == [("analysis-a",)]


def test_bridge_does_not_save_trace_when_discovery_fails():
    discovery = FakeDiscoveryRunner(fail=True)
    shadow = FakeShadowRunner()
    trace_store = Mock()

    bridge = make_bridge(
        discovery,
        shadow,
        trace_store=trace_store,
    )

    result = bridge.run_if_due()

    assert result is None
    assert isinstance(bridge.last_error, RuntimeError)

    trace_store.save.assert_not_called()
    assert shadow.calls == []

    
def test_bridge_saves_experimental_comparison():
    from types import SimpleNamespace

    discovery = FakeDiscoveryRunner()
    shadow = FakeShadowRunner()
    trace_store = Mock()

    discovery.last_experimental_comparison = SimpleNamespace(
        experimental_coin_ids=("coin-a", "coin-b"),
        experimental_only_coin_ids=("coin-b",),
        common_coin_ids=("coin-a",),
        experimental_priorities=(
            SimpleNamespace(
                coin_id="coin-b",
                score=76.0,
                state="priority",
                direction="up",
                evidence_count=3,
            ),
        ),
    )
    discovery.last_experimental_error = None

    bridge = make_bridge(
        discovery,
        shadow,
        trace_store=trace_store,
    )

    result = bridge.run_if_due()

    assert result is not None
    assert bridge.last_error is None
    assert bridge.last_trace_error is None

    trace_store.save.assert_called_once()
    trace = trace_store.save.call_args.args[0]

    assert trace.experimental_status == "completed"
    assert trace.experimental_coin_ids == (
        "coin-a",
        "coin-b",
    )
    assert trace.experimental_only_coin_ids == ("coin-b",)
    assert trace.common_coin_ids == ("coin-a",)
    assert trace.experimental_priorities[0]["score"] == 76.0
    assert trace.experimental_priorities[0]["direction"] == "up"

