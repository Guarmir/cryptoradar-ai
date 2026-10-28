from types import SimpleNamespace

from app.early_movement.extreme_movement.extreme_movement_discovery_bridge import (
    ExtremeMovementDiscoveryBridge,
)
from app.early_movement.extreme_movement.extreme_movement_discovery_schedule import (
    ExtremeMovementDiscoverySchedule,
)


class FakeDiscoveryRunner:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def run(self, *, excluded_coin_ids=None):
        self.calls.append(set(excluded_coin_ids or set()))
        if self.fail:
            raise RuntimeError("Falha simulada na descoberta")
        return SimpleNamespace(analysis_results=("analysis-a",))


class FakeShadowRunner:
    def __init__(self):
        self.calls = []

    def run_analysis_results(self, analysis_results):
        self.calls.append(analysis_results)
        return SimpleNamespace(entries=("entry-a",))


def test_bridge_runs_when_due_and_excludes_existing_coins():
    clock = [0.0]
    discovery = FakeDiscoveryRunner()
    shadow = FakeShadowRunner()

    bridge = ExtremeMovementDiscoveryBridge(
        discovery_runner=discovery,
        shadow_runner=shadow,
        schedule=ExtremeMovementDiscoverySchedule(
            interval_seconds=900,
            clock=lambda: clock[0],
        ),
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

    bridge = ExtremeMovementDiscoveryBridge(
        discovery_runner=discovery,
        shadow_runner=shadow,
        schedule=ExtremeMovementDiscoverySchedule(
            interval_seconds=900,
            clock=lambda: clock[0],
        ),
    )

    assert bridge.run_if_due() is None
    assert isinstance(bridge.last_error, RuntimeError)
    assert shadow.calls == []

    clock[0] = 100.0
    assert bridge.run_if_due() is None
    assert len(discovery.calls) == 1
