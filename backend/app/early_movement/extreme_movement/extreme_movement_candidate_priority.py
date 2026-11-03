
import math
from dataclasses import dataclass

from app.early_movement.extreme_movement.extreme_movement_candidate_tracker import (
    ExtremeMovementCandidateEvolution,
)


@dataclass(frozen=True)
class ExtremeMovementCandidatePriority:
    coin_id: str
    score: float
    state: str
    direction: str
    evidence_count: int


class ExtremeMovementCandidatePriorityEvaluator:
    MIN_OBSERVATIONS = 2

    @staticmethod
    def _valid(value: float | None) -> bool:
        return value is not None and math.isfinite(value)

    def evaluate(
        self,
        evolution: ExtremeMovementCandidateEvolution,
    ) -> ExtremeMovementCandidatePriority:
        price_change = evolution.price_change_since_previous_pct
        volume_change = evolution.volume_change_since_previous_pct
        change_delta = evolution.change_24h_delta

        if (
            evolution.observation_count < self.MIN_OBSERVATIONS
            or not self._valid(price_change)
        ):
            return ExtremeMovementCandidatePriority(
                coin_id=evolution.coin_id,
                score=0.0,
                state="observing",
                direction="unknown",
                evidence_count=0,
            )

        direction = (
            "up"
            if price_change > 0
            else "down"
            if price_change < 0
            else "neutral"
        )

        score = 0.0
        evidence_count = 0

        # Movimento de preço entre duas observações.
        price_strength = min(abs(price_change), 5.0) / 5.0
        score += price_strength * 40.0

        if abs(price_change) >= 0.5:
            evidence_count += 1

        # Crescimento relativo de atividade.
        if self._valid(volume_change) and volume_change > 0:
            volume_strength = min(volume_change, 30.0) / 30.0
            score += volume_strength * 30.0

            if volume_change >= 5.0:
                evidence_count += 1

        # Evolução da variação de 24 horas.
        if self._valid(change_delta):
            if (
                direction == "up" and change_delta > 0
            ) or (
                direction == "down" and change_delta < 0
            ):
                delta_strength = min(abs(change_delta), 5.0) / 5.0
                score += delta_strength * 30.0

                if abs(change_delta) >= 0.5:
                    evidence_count += 1

        score = round(min(score, 100.0), 2)

        if evidence_count >= 2 and score >= 50:
            state = "priority"
        elif evidence_count >= 1 and score >= 20:
            state = "strengthening"
        elif evidence_count == 0:
            state = "weakening"
        else:
            state = "observing"

        return ExtremeMovementCandidatePriority(
            coin_id=evolution.coin_id,
            score=score,
            state=state,
            direction=direction,
            evidence_count=evidence_count,
        )
