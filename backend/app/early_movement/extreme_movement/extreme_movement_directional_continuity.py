"""Avaliacao experimental, somente leitura, da continuidade direcional.

Nao altera selecao, score, persistencia ou alertas. Usa exclusivamente o
historico de precos ja coletado pelo ExtremeMovementCandidateTracker.
"""

import math
from dataclasses import dataclass
from typing import Literal, Sequence

from app.early_movement.extreme_movement.extreme_movement_candidate_tracker import (
    ExtremeMovementCandidateObservation,
)

DirectionalState = Literal[
    "insufficient_data",
    "neutral",
    "detected",
    "sustained",
    "unstable",
    "opposite_detected",
    "opposite_sustained",
]
Direction = Literal["up", "down", "neutral", "unknown"]


@dataclass(frozen=True)
class ExtremeMovementDirectionalContinuity:
    coin_id: str
    state: DirectionalState
    direction: Direction
    previous_direction: Direction
    observation_count: int
    consecutive_moves: int
    alternating_moves: int
    latest_price_change_pct: float | None


class ExtremeMovementDirectionalContinuityEvaluator:
    """Classificacao preliminar: nao indica probabilidade nem confirma trade.

    Os limiares sao configuraveis para testes. Um movimento so conta quando
    ultrapassa min_move_pct; variacoes menores sao neutras. A comparacao usa
    pares consecutivos e nao faz chamadas de rede.
    """

    def __init__(
        self,
        *,
        min_move_pct: float = 0.1,
        sustained_moves: int = 2,
    ) -> None:
        if not math.isfinite(min_move_pct) or min_move_pct <= 0:
            raise ValueError("min_move_pct deve ser positivo e finito.")
        if sustained_moves < 2:
            raise ValueError("sustained_moves deve ser >= 2.")
        self._min_move_pct = min_move_pct
        self._sustained_moves = sustained_moves

    def evaluate(
        self,
        history: Sequence[ExtremeMovementCandidateObservation],
    ) -> ExtremeMovementDirectionalContinuity:
        if not history:
            raise ValueError("Historico vazio: coin_id indisponivel.")

        coin_id = history[0].coin_id
        if not coin_id or any(item.coin_id != coin_id for item in history):
            raise ValueError("Historico contem identificadores diferentes.")
        for i, item in enumerate(history):
            if not math.isfinite(item.price) or item.price <= 0:
                raise ValueError("Historico contem preco invalido.")
            if i and item.observed_at <= history[i - 1].observed_at:
                raise ValueError("Historico fora de ordem.")

        if len(history) < 2:
            return ExtremeMovementDirectionalContinuity(
                coin_id=coin_id,
                state="insufficient_data",
                direction="unknown",
                previous_direction="unknown",
                observation_count=len(history),
                consecutive_moves=0,
                alternating_moves=0,
                latest_price_change_pct=None,
            )

        changes = [
            (current.price - previous.price) / previous.price * 100
            for previous, current in zip(history, history[1:])
        ]
        directions: list[Direction] = [
            "up" if value >= self._min_move_pct else
            "down" if value <= -self._min_move_pct else "neutral"
            for value in changes
        ]
        direction = directions[-1]
        significant = [value for value in directions if value != "neutral"]
        previous_direction: Direction = significant[-2] if len(significant) > 1 else "unknown"
        alternating_moves = sum(
            a != b for a, b in zip(significant, significant[1:])
        )

        consecutive_moves = 0
        if direction != "neutral":
            for item in reversed(directions):
                if item != direction:
                    break
                consecutive_moves += 1

        if direction == "neutral":
            state: DirectionalState = "neutral"
        elif alternating_moves >= 2 and len(significant) >= 3 and consecutive_moves < self._sustained_moves:
            state = "unstable"
        elif previous_direction not in ("unknown", direction):
            state = (
                "opposite_sustained"
                if consecutive_moves >= self._sustained_moves
                else "opposite_detected"
            )
        elif consecutive_moves >= self._sustained_moves:
            state = "sustained"
        else:
            state = "detected"

        # Para uma sequencia de movimentos contrarios, direcao de referencia
        # e o ultimo movimento significativo antes da sequencia atual.
        if direction != "neutral" and consecutive_moves > 0:
            prior = directions[:-consecutive_moves]
            previous_direction = next(
                (item for item in reversed(prior) if item != "neutral"),
                "unknown",
            )
            if state in ("opposite_detected", "opposite_sustained") and previous_direction == "unknown":
                state = "sustained" if consecutive_moves >= self._sustained_moves else "detected"
            elif previous_direction not in ("unknown", direction) and state not in ("unstable",):
                state = "opposite_sustained" if consecutive_moves >= self._sustained_moves else "opposite_detected"

        return ExtremeMovementDirectionalContinuity(
            coin_id=coin_id,
            state=state,
            direction=direction,
            previous_direction=previous_direction,
            observation_count=len(history),
            consecutive_moves=consecutive_moves,
            alternating_moves=alternating_moves,
            latest_price_change_pct=round(changes[-1], 4),
        )
