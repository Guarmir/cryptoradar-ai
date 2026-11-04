
import math
from dataclasses import dataclass, replace
from datetime import datetime, timezone


@dataclass(frozen=True)
class ExtremeMovementExperimentalTracking:
    coin_id: str
    started_at: datetime
    last_observed_at: datetime
    initial_price: float
    latest_price: float
    initial_direction: str
    latest_direction: str
    initial_score: float
    latest_score: float
    initial_evidence_count: int
    latest_evidence_count: int
    latest_state: str
    observation_count: int
    max_observed_price: float
    min_observed_price: float
    status: str = "active"
    closed_at: datetime | None = None
    close_reason: str | None = None

    @property
    def price_change_pct(self) -> float:
        return round(
            (
                (self.latest_price - self.initial_price)
                / self.initial_price
            ) * 100.0,
            4,
        )

    @property
    def maximum_rise_pct(self) -> float:
        return round(
            (
                (self.max_observed_price - self.initial_price)
                / self.initial_price
            ) * 100.0,
            4,
        )

    @property
    def maximum_fall_pct(self) -> float:
        return round(
            (
                (self.min_observed_price - self.initial_price)
                / self.initial_price
            ) * 100.0,
            4,
        )


class ExtremeMovementExperimentalTrackingEvaluator:

    @staticmethod
    def _validate_price(price: float) -> None:
        if not math.isfinite(price) or price <= 0:
            raise ValueError("Preco invalido.")

    @staticmethod
    def _validate_time(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Horario sem fuso.")

    @staticmethod
    def _validate_signal(
        score: float,
        evidence_count: int,
    ) -> None:
        if not math.isfinite(score) or not 0 <= score <= 100:
            raise ValueError("Score invalido.")

        if evidence_count < 0:
            raise ValueError("Evidencias invalidas.")

    def start(
        self,
        *,
        coin_id: str,
        observed_at: datetime,
        price: float,
        direction: str,
        score: float,
        evidence_count: int,
        state: str,
    ) -> ExtremeMovementExperimentalTracking:
        self._validate_price(price)
        self._validate_time(observed_at)
        self._validate_signal(score, evidence_count)

        if not coin_id.strip():
            raise ValueError("Ativo sem identificacao.")

        return ExtremeMovementExperimentalTracking(
            coin_id=coin_id,
            started_at=observed_at,
            last_observed_at=observed_at,
            initial_price=price,
            latest_price=price,
            initial_direction=direction,
            latest_direction=direction,
            initial_score=score,
            latest_score=score,
            initial_evidence_count=evidence_count,
            latest_evidence_count=evidence_count,
            latest_state=state,
            observation_count=1,
            max_observed_price=price,
            min_observed_price=price,
        )

    def update(
        self,
        tracking: ExtremeMovementExperimentalTracking,
        *,
        observed_at: datetime,
        price: float,
        direction: str,
        score: float,
        evidence_count: int,
        state: str,
    ) -> ExtremeMovementExperimentalTracking:
        if tracking.status != "active":
            raise ValueError("Acompanhamento encerrado.")

        self._validate_price(price)
        self._validate_time(observed_at)
        self._validate_signal(score, evidence_count)

        if observed_at <= tracking.last_observed_at:
            raise ValueError("Observacao fora de ordem.")

        return replace(
            tracking,
            last_observed_at=observed_at,
            latest_price=price,
            latest_direction=direction,
            latest_score=score,
            latest_evidence_count=evidence_count,
            latest_state=state,
            observation_count=tracking.observation_count + 1,
            max_observed_price=max(
                tracking.max_observed_price,
                price,
            ),
            min_observed_price=min(
                tracking.min_observed_price,
                price,
            ),
        )

    def close(
        self,
        tracking: ExtremeMovementExperimentalTracking,
        *,
        closed_at: datetime,
        reason: str,
    ) -> ExtremeMovementExperimentalTracking:
        if tracking.status != "active":
            raise ValueError("Acompanhamento ja encerrado.")

        self._validate_time(closed_at)

        if closed_at < tracking.last_observed_at:
            raise ValueError("Encerramento anterior a observacao.")

        if not reason.strip():
            raise ValueError("Motivo obrigatorio.")

        return replace(
            tracking,
            status="closed",
            closed_at=closed_at,
            close_reason=reason,
        )
