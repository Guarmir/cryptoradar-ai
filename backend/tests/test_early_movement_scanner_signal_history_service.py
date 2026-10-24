from types import SimpleNamespace

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecision,
)
from app.early_movement.scanner.scanner_signal_history_service import (
    EarlyMovementScannerSignalHistoryService,
)
from app.early_movement.early_movement_direction import (
    EarlyMovementDirection,
)
from app.early_movement.early_movement_direction_transition import (
    EarlyMovementDirectionTransitionType,
)


class FakeHistoryStore:
    def __init__(
        self,
    ) -> None:
        self.records = []

    def save(
        self,
        record,
    ) -> None:
        self.records.append(
            record,
        )

    def load_recent(
        self,
        *,
        limit: int = 100,
    ):
        return tuple(
            self.records[-limit:]
        )

    
    def load_latest_for_coin(
        self,
        *,
        coin_id: str,
    ):
        matching = [
            record
            for record in self.records
            if record.coin_id == coin_id
        ]

        if not matching:
            return None

        return max(
            enumerate(matching),
            key=lambda item: (
                item[1].observed_at,
                item[0],
            ),
        )[1]




def _ranked_result(
    *,
    coin_id: str,
    symbol: str,
    state: EarlyMovementState,
    relevance_score: float,
):
    asset = SimpleNamespace(
        coin_id=coin_id,
        symbol=symbol,
        name=symbol,
        current_price=10.0,
    )

    candidate = SimpleNamespace(
        asset=asset,
    )

    evidence = SimpleNamespace(
        state=state,
        price_acceleration=2.0,
        abnormal_volume_ratio=1.8,
        liquidity_score=85.0,
        volatility_expansion=1.4,
        persistence_score=70.0,
        false_breakout_risk=20.0,
        support_break=False,
        resistance_break=True,
        retest_confirmed=True,
    )

    metrics = SimpleNamespace(
        recent_price_return=2.5,
        price_acceleration=2.0,
        abnormal_volume_ratio=1.8,
        persistence_score=70.0,
    )

    price_structure = SimpleNamespace(
        support_break=False,
        resistance_break=True,
    )

    breakout_confirmation = SimpleNamespace(
        breakout_direction="up",
    )

    analysis = SimpleNamespace(
        metrics=metrics,
        price_structure=price_structure,
        evidence=evidence,
        breakout_confirmation=breakout_confirmation,
    )

    analysis_result = SimpleNamespace(
        candidate=candidate,
        analysis=analysis,
    )

    return SimpleNamespace(
        relevance_score=relevance_score,
        result=analysis_result,
    )



def test_history_service_records_scanner_results() -> None:
    store = FakeHistoryStore()

    service = (
        EarlyMovementScannerSignalHistoryService(
            store=store,
        )
    )

    early = _ranked_result(
        coin_id="near",
        symbol="NEAR",
        state=EarlyMovementState.EARLY_MOVEMENT,
        relevance_score=78.0,
    )

    observation = _ranked_result(
        coin_id="uniswap",
        symbol="UNI",
        state=EarlyMovementState.OBSERVATION,
        relevance_score=52.0,
    )

    scan_result = SimpleNamespace(
        ranked_results=(
            early,
            observation,
        ),
    )

    alert_decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=True,
            results=(
                early,
            ),
        )
    )

    records = service.record(
        scan_result=scan_result,
        alert_decision=alert_decision,
    )

    assert len(records) == 2

    assert records[0].coin_id == "near"
    assert records[0].recent_price_return == 2.5
    assert records[0].direction == EarlyMovementDirection.UP

    assert records[1].coin_id == "uniswap"
    assert records[1].recent_price_return == 2.5
    assert records[1].direction == EarlyMovementDirection.UP

    assert len(records) == 2
    assert len(store.records) == 2

    first = records[0]

    assert first.coin_id == "near"
    assert first.symbol == "NEAR"
    assert (
        first.state
        == EarlyMovementState.EARLY_MOVEMENT
    )
    assert first.relevance_score == 78.0
    assert first.alertable is True
    assert first.resistance_break is True
    assert first.retest_confirmed is True
    assert (
        first.breakout_direction
        == "up"
    )

    second = records[1]

    assert second.coin_id == "uniswap"
    assert second.alertable is False

        # Simula uma mudança para pressão de baixa.
    down = _ranked_result(
        coin_id="down-asset",
        symbol="DOWN",
        state=EarlyMovementState.EARLY_MOVEMENT,
        relevance_score=70.0,
    )

    down.result.analysis.metrics.recent_price_return = -2.5
    down.result.analysis.metrics.price_acceleration = -2.0
    down.result.analysis.price_structure.resistance_break = False
    down.result.analysis.price_structure.support_break = True

    down_records = service.record(
        scan_result=SimpleNamespace(ranked_results=(down,)),
        alert_decision=EarlyMovementScannerAlertDecision(
            should_alert=False,
            results=(),
        ),
    )

    assert down_records[0].direction == EarlyMovementDirection.DOWN
    assert down_records[0].recent_price_return == -2.5

    # Simula ausência de pressão direcional suficiente.
    neutral = _ranked_result(
        coin_id="neutral-asset",
        symbol="NEUTRAL",
        state=EarlyMovementState.OBSERVATION,
        relevance_score=40.0,
    )

    neutral.result.analysis.metrics.recent_price_return = 0.1
    neutral.result.analysis.metrics.price_acceleration = 0.0
    neutral.result.analysis.price_structure.resistance_break = False

    neutral_records = service.record(
        scan_result=SimpleNamespace(ranked_results=(neutral,)),
        alert_decision=EarlyMovementScannerAlertDecision(
            should_alert=False,
            results=(),
        ),
    )

    assert neutral_records[0].direction == EarlyMovementDirection.NEUTRAL
    assert neutral_records[0].recent_price_return == 0.1

    
def test_history_service_detects_direction_change_between_cycles():
    store = FakeHistoryStore()

    service = EarlyMovementScannerSignalHistoryService(
        store=store,
    )

    def run_cycle(recent_return, acceleration, support_break, resistance_break):
        ranked = _ranked_result(
            coin_id="uniswap",
            symbol="UNI",
            state=EarlyMovementState.EARLY_MOVEMENT,
            relevance_score=78.0,
        )

        ranked.result.analysis.metrics.recent_price_return = recent_return
        ranked.result.analysis.metrics.price_acceleration = acceleration
        ranked.result.analysis.price_structure.support_break = support_break
        ranked.result.analysis.price_structure.resistance_break = resistance_break

        return service.record(
            scan_result=SimpleNamespace(
                ranked_results=(ranked,),
            ),
            alert_decision=EarlyMovementScannerAlertDecision(
                should_alert=False,
                results=(),
            ),
        )

    run_cycle(2.5, 2.0, False, True)

    assert (
        service.last_transitions[0].transition_type
        == EarlyMovementDirectionTransitionType.INITIAL
    )

    run_cycle(-2.5, -2.0, True, False)

    assert (
        service.last_transitions[0].previous
        == EarlyMovementDirection.UP
    )

    assert (
        service.last_transitions[0].current
        == EarlyMovementDirection.DOWN
    )

    assert (
        service.last_transitions[0].transition_type
        == EarlyMovementDirectionTransitionType.REVERSAL
    )

    
def test_history_service_tracks_direction_evolution():
    store = FakeHistoryStore()
    service = EarlyMovementScannerSignalHistoryService(
        store=store,
    )

    def run(coin_id, recent_return, acceleration, support, resistance):
        ranked = _ranked_result(
            coin_id=coin_id,
            symbol=coin_id.upper(),
            state=EarlyMovementState.EARLY_MOVEMENT,
            relevance_score=78.0,
        )

        analysis = ranked.result.analysis
        analysis.metrics.recent_price_return = recent_return
        analysis.metrics.price_acceleration = acceleration
        analysis.price_structure.support_break = support
        analysis.price_structure.resistance_break = resistance

        service.record(
            scan_result=SimpleNamespace(
                ranked_results=(ranked,),
            ),
            alert_decision=EarlyMovementScannerAlertDecision(
                should_alert=False,
                results=(),
            ),
        )

        return service.last_transitions[0]

    first = run("uniswap", 2.5, 2.0, False, True)
    assert first.transition_type == (
        EarlyMovementDirectionTransitionType.INITIAL
    )

    unchanged = run("uniswap", 2.5, 2.0, False, True)
    assert unchanged.transition_type == (
        EarlyMovementDirectionTransitionType.UNCHANGED
    )

    weakening = run("uniswap", 0.1, 0.0, False, False)
    assert weakening.transition_type == (
        EarlyMovementDirectionTransitionType.WEAKENING
    )

    emerging = run("uniswap", -2.5, -2.0, True, False)
    assert emerging.transition_type == (
        EarlyMovementDirectionTransitionType.EMERGING
    )

    other_coin = run("bitcoin", -2.5, -2.0, True, False)
    assert other_coin.transition_type == (
        EarlyMovementDirectionTransitionType.INITIAL
    )

