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