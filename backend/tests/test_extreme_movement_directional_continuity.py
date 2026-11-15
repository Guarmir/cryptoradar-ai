from datetime import datetime, timedelta, timezone

import pytest

from app.early_movement.extreme_movement.extreme_movement_candidate_tracker import (
    ExtremeMovementCandidateObservation,
)
from app.early_movement.extreme_movement.extreme_movement_directional_continuity import (
    ExtremeMovementDirectionalContinuityEvaluator,
)


def _history(prices, coin_id="bitcoin"):
    start = datetime(2026, 11, 14, tzinfo=timezone.utc)
    return tuple(
        ExtremeMovementCandidateObservation(
            coin_id=coin_id,
            observed_at=start + timedelta(minutes=index * 5),
            price=price,
            total_volume=None,
            change_24h=None,
        )
        for index, price in enumerate(prices)
    )


def test_primeira_leitura_sem_direcao():
    result = ExtremeMovementDirectionalContinuityEvaluator().evaluate(_history([100]))
    assert result.state == "insufficient_data"
    assert result.direction == "unknown"


def test_uma_alta_e_apenas_detectada():
    result = ExtremeMovementDirectionalContinuityEvaluator().evaluate(_history([100, 101]))
    assert result.state == "detected"
    assert result.direction == "up"


def test_altas_consecutivas_sao_sustentadas_na_janela():
    result = ExtremeMovementDirectionalContinuityEvaluator().evaluate(_history([100, 101, 102]))
    assert result.state == "sustained"
    assert result.consecutive_moves == 2


def test_queda_contraria_identificada():
    result = ExtremeMovementDirectionalContinuityEvaluator().evaluate(_history([100, 102, 104, 103]))
    assert result.state == "opposite_detected"
    assert result.direction == "down"
    assert result.previous_direction == "up"


def test_queda_contraria_com_continuidade():
    result = ExtremeMovementDirectionalContinuityEvaluator().evaluate(_history([100, 102, 104, 103, 101]))
    assert result.state == "opposite_sustained"
    assert result.direction == "down"
    assert result.previous_direction == "up"


def test_alternancia_e_instavel():
    result = ExtremeMovementDirectionalContinuityEvaluator().evaluate(_history([100, 102, 100, 103]))
    assert result.state == "unstable"


def test_variacao_muito_pequena_e_neutra():
    result = ExtremeMovementDirectionalContinuityEvaluator().evaluate(_history([100, 100.01]))
    assert result.state == "neutral"


def test_rejeita_historico_de_moedas_misturadas():
    history = list(_history([100, 101]))
    history[1] = _history([101], "ethereum")[0]
    with pytest.raises(ValueError):
        ExtremeMovementDirectionalContinuityEvaluator().evaluate(history)


def test_rejeita_preco_invalido():
    with pytest.raises(ValueError):
        ExtremeMovementDirectionalContinuityEvaluator().evaluate(_history([100, float("nan")]))
