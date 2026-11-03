
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


@dataclass(frozen=True)
class ExtremeMovementCandidateObservation:
    coin_id: str
    observed_at: datetime
    price: float
    total_volume: float | None
    change_24h: float | None


@dataclass(frozen=True)
class ExtremeMovementCandidateEvolution:
    coin_id: str
    observation_count: int
    price_change_since_previous_pct: float | None
    volume_change_since_previous_pct: float | None
    change_24h_delta: float | None
    state: str


class ExtremeMovementCandidateTracker:
    def __init__(
        self,
        *,
        max_observations_per_asset: int = 12,
        max_age_minutes: int = 120,
        max_tracked_assets: int = 500,
    ) -> None:
        if max_observations_per_asset < 2:
            raise ValueError(
                "max_observations_per_asset deve ser >= 2."
            )
        if max_age_minutes < 1:
            raise ValueError(
                "max_age_minutes deve ser positivo."
            )
        if max_tracked_assets < 1:
            raise ValueError(
                "max_tracked_assets deve ser positivo."
            )

        self._max_observations = max_observations_per_asset
        self._max_age = timedelta(minutes=max_age_minutes)
        self._max_tracked_assets = max_tracked_assets

        self._history: dict[
            str, list[ExtremeMovementCandidateObservation]
        ] = {}

    @staticmethod
    def _valid_number(value: float | None) -> bool:
        return value is not None and math.isfinite(value)

    @staticmethod
    def _percentage_change(
        previous: float | None,
        current: float | None,
    ) -> float | None:
        if (
            previous is None
            or current is None
            or not math.isfinite(previous)
            or not math.isfinite(current)
            or previous <= 0
        ):
            return None

        return ((current - previous) / previous) * 100.0

    def observe(
        self,
        assets: Iterable[EarlyMovementScannerMarketAsset],
        *,
        observed_at: datetime | None = None,
    ) -> tuple[ExtremeMovementCandidateEvolution, ...]:
        now = (
            observed_at
            if observed_at is not None
            else datetime.now(timezone.utc)
        )

        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError(
                "observed_at deve conter fuso horário."
            )

        cutoff = now - self._max_age

        for coin_id in tuple(self._history):
            retained = [
                item
                for item in self._history[coin_id]
                if cutoff <= item.observed_at <= now
            ]

            if retained:
                self._history[coin_id] = retained
            else:
                del self._history[coin_id]

        results = []
        seen_ids: set[str] = set()

        for asset in assets:
            if asset.coin_id in seen_ids:
                continue

            seen_ids.add(asset.coin_id)

            if (
                not math.isfinite(asset.current_price)
                or asset.current_price <= 0
            ):
                continue

            history = self._history.setdefault(
                asset.coin_id, []
            )

            if history and now <= history[-1].observed_at:
                continue

            observation = ExtremeMovementCandidateObservation(
                coin_id=asset.coin_id,
                observed_at=now,
                price=asset.current_price,
                total_volume=(
                    asset.total_volume
                    if self._valid_number(asset.total_volume)
                    and asset.total_volume >= 0
                    else None
                ),
                change_24h=(
                    asset.price_change_percentage_24h
                    if self._valid_number(
                        asset.price_change_percentage_24h
                    )
                    else None
                ),
            )

            previous = history[-1] if history else None

            history.append(observation)

            if len(history) > self._max_observations:
                del history[:-self._max_observations]

            price_change = (
                self._percentage_change(
                    previous.price, observation.price
                )
                if previous is not None
                else None
            )

            volume_change = (
                self._percentage_change(
                    previous.total_volume,
                    observation.total_volume,
                )
                if previous is not None
                else None
            )

            change_delta = (
                observation.change_24h - previous.change_24h
                if previous is not None
                and observation.change_24h is not None
                and previous.change_24h is not None
                else None
            )

            if previous is None:
                state = "new"
            elif price_change is None:
                state = "insufficient_data"
            elif price_change > 0:
                state = "rising"
            elif price_change < 0:
                state = "falling"
            else:
                state = "stable"

            results.append(
                ExtremeMovementCandidateEvolution(
                    coin_id=asset.coin_id,
                    observation_count=len(history),
                    price_change_since_previous_pct=price_change,
                    volume_change_since_previous_pct=volume_change,
                    change_24h_delta=change_delta,
                    state=state,
                )
            )

        if len(self._history) > self._max_tracked_assets:
            ordered = sorted(
                self._history,
                key=lambda coin_id: (
                    self._history[coin_id][-1].observed_at,
                    coin_id,
                ),
            )

            excess = (
                len(self._history) - self._max_tracked_assets
            )

            for coin_id in ordered[:excess]:
                del self._history[coin_id]

        return tuple(results)

    def get_history(
        self,
        coin_id: str,
    ) -> tuple[ExtremeMovementCandidateObservation, ...]:
        return tuple(self._history.get(coin_id, ()))
