
from dataclasses import dataclass

from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_observation_tracker import (
    ExtremeMovementObservation,
    ExtremeMovementObservationTracker,
)


@dataclass(frozen=True)
class ExtremeMovementTrackedAsset:
    coin_id: str
    last_entry: ExtremeMovementAnalysisEntry
    missed_cycles: int = 0


@dataclass(frozen=True)
class ExtremeMovementObservationCycle:
    observations: tuple[ExtremeMovementObservation, ...]
    active_assets: tuple[ExtremeMovementTrackedAsset, ...]
    missing_assets: tuple[ExtremeMovementTrackedAsset, ...]


class ExtremeMovementObservationStore:
    def __init__(
        self,
        *,
        tracker: ExtremeMovementObservationTracker | None = None,
    ) -> None:
        self._tracker = tracker or ExtremeMovementObservationTracker()
        self._assets: dict[str, ExtremeMovementTrackedAsset] = {}

    def restore(
        self,
        assets: tuple[ExtremeMovementTrackedAsset, ...],
    ) -> None:
        restored: dict[str, ExtremeMovementTrackedAsset] = {}

        for asset in assets:
            coin_id = asset.coin_id.strip()

            if not coin_id:
                raise ValueError(
                    "coin_id nao pode ser vazio."
                )

            if asset.last_entry.coin_id != coin_id:
                raise ValueError(
                    "coin_id do ativo e da avaliacao "
                    "devem ser iguais."
                )

            if asset.missed_cycles < 0:
                raise ValueError(
                    "missed_cycles nao pode ser negativo."
                )

            if coin_id in restored:
                raise ValueError(
                    "Ativo duplicado na restauracao."
                )

            restored[coin_id] = asset

        self._assets = restored

    def update(
        self,
        entries: tuple[ExtremeMovementAnalysisEntry, ...],
    ) -> ExtremeMovementObservationCycle:
        observations = []
        seen = set()

        for entry in entries:
            coin_id = entry.coin_id
            seen.add(coin_id)

            previous_asset = self._assets.get(coin_id)
            previous_entry = (
                previous_asset.last_entry
                if previous_asset is not None
                else None
            )

            observation = self._tracker.compare(
                previous_entry,
                entry,
            )

            observations.append(observation)

            self._assets[coin_id] = ExtremeMovementTrackedAsset(
                coin_id=coin_id,
                last_entry=entry,
                missed_cycles=0,
            )

        missing_assets = []

        for coin_id, asset in tuple(self._assets.items()):
            if coin_id in seen:
                continue

            updated_asset = ExtremeMovementTrackedAsset(
                coin_id=coin_id,
                last_entry=asset.last_entry,
                missed_cycles=asset.missed_cycles + 1,
            )

            self._assets[coin_id] = updated_asset
            missing_assets.append(updated_asset)

        return ExtremeMovementObservationCycle(
            observations=tuple(observations),
            active_assets=tuple(self._assets.values()),
            missing_assets=tuple(missing_assets),
        )
