import math
from collections.abc import Iterable

from app.early_movement.extreme_movement.extreme_movement_candidate import (
    ExtremeMovementCandidate,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


class ExtremeMovementCandidateSelector:
    DEFAULT_MIN_ABSOLUTE_CHANGE_24H = 10.0
    DEFAULT_MIN_TOTAL_VOLUME = 100_000.0
    DEFAULT_LIMIT = 20

    def __init__(
        self,
        *,
        min_absolute_change_24h: float = (
            DEFAULT_MIN_ABSOLUTE_CHANGE_24H
        ),
        min_total_volume: float = (
            DEFAULT_MIN_TOTAL_VOLUME
        ),
    ) -> None:
        if (
            not math.isfinite(min_absolute_change_24h)
            or min_absolute_change_24h <= 0
        ):
            raise ValueError(
                "A variação mínima deve ser positiva e finita."
            )

        if (
            not math.isfinite(min_total_volume)
            or min_total_volume <= 0
        ):
            raise ValueError(
                "O volume mínimo deve ser positivo e finito."
            )

        self._min_absolute_change_24h = (
            min_absolute_change_24h
        )
        self._min_total_volume = min_total_volume

    def select(
        self,
        assets: Iterable[EarlyMovementScannerMarketAsset],
        *,
        limit: int = DEFAULT_LIMIT,
    ) -> tuple[ExtremeMovementCandidate, ...]:
        if limit < 1:
            raise ValueError(
                "O limite deve ser maior que zero."
            )

        candidates: list[ExtremeMovementCandidate] = []
        seen_ids: set[str] = set()

        for asset in assets:
            if asset.coin_id in seen_ids:
                continue

            change = asset.price_change_percentage_24h
            volume = asset.total_volume

            if change is None or not math.isfinite(change):
                continue

            if (
                volume is None
                or not math.isfinite(volume)
                or volume < self._min_total_volume
            ):
                continue

            absolute_change = abs(change)

            if absolute_change < self._min_absolute_change_24h:
                continue

            direction = "up" if change > 0 else "down"

            candidates.append(
                ExtremeMovementCandidate(
                    asset=asset,
                    absolute_change_24h=absolute_change,
                    direction=direction,
                    activity_score=absolute_change,
                )
            )

            seen_ids.add(asset.coin_id)

        candidates.sort(
            key=lambda candidate: (
                -candidate.activity_score,
                -(candidate.asset.total_volume or 0.0),
                candidate.coin_id,
            )
        )

        return tuple(candidates[:limit])