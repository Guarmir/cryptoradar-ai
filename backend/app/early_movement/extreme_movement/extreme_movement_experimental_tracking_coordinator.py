import math
from datetime import datetime, timedelta, timezone
from typing import Iterable

from app.early_movement.extreme_movement.extreme_movement_candidate_comparator import (
    ExtremeMovementCandidateComparison,
)
from app.early_movement.extreme_movement.extreme_movement_experimental_tracking import (
    ExtremeMovementExperimentalTracking,
    ExtremeMovementExperimentalTrackingEvaluator,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


class ExtremeMovementExperimentalTrackingCoordinator:
    def __init__(
        self,
        *,
        store,
        evaluator: ExtremeMovementExperimentalTrackingEvaluator | None = None,
        max_tracking_duration: timedelta = timedelta(hours=24),
    ) -> None:
        if max_tracking_duration <= timedelta(0):
            raise ValueError("Duracao maxima deve ser positiva.")
        self._store = store
        self._evaluator = (
            evaluator
            if evaluator is not None
            else ExtremeMovementExperimentalTrackingEvaluator()
        )
        self._max_tracking_duration = max_tracking_duration
        self._active: dict[
            str, tuple[int, ExtremeMovementExperimentalTracking]
        ] = {}
        self._loaded = False

    def _load_once(self) -> None:
        if self._loaded:
            return

        records = self._store.load_active()
        self._active = {
            tracking.coin_id: (tracking_id, tracking)
            for tracking_id, tracking in records
        }
        self._loaded = True

    def process(
        self,
        assets: Iterable[EarlyMovementScannerMarketAsset],
        comparison: ExtremeMovementCandidateComparison,
        *,
        observed_at: datetime | None = None,
    ) -> None:
        now = observed_at if observed_at is not None else datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Horario sem fuso.")

        self._load_once()

        market = {
            asset.coin_id: asset
            for asset in assets
            if math.isfinite(asset.current_price) and asset.current_price > 0
        }
        priorities = {
            item.coin_id: item
            for item in comparison.experimental_priorities
        }
        selected_ids = set(comparison.experimental_coin_ids)

        pending_updates: list[
            tuple[int, ExtremeMovementExperimentalTracking, bool]
        ] = []
        updated_by_coin: dict[
            str, tuple[int, ExtremeMovementExperimentalTracking]
        ] = {}
        pending_closes: list[
            tuple[int, ExtremeMovementExperimentalTracking]
        ] = []
        closed_coin_ids: set[str] = set()

        for coin_id, (tracking_id, tracking) in self._active.items():
            if now >= tracking.started_at + self._max_tracking_duration:
                closed = self._evaluator.close(
                    tracking,
                    closed_at=now,
                    reason="observation_window_completed",
                )
                pending_closes.append((tracking_id, closed))
                closed_coin_ids.add(coin_id)
                continue

            asset = market.get(coin_id)
            if asset is None or now <= tracking.last_observed_at:
                continue

            priority = priorities.get(coin_id)
            updated = self._evaluator.update(
                tracking,
                observed_at=now,
                price=asset.current_price,
                direction=priority.direction if priority is not None else "unknown",
                score=(
                    priority.score if priority is not None else tracking.latest_score
                ),
                evidence_count=(
                    priority.evidence_count
                    if priority is not None
                    else tracking.latest_evidence_count
                ),
                state=priority.state if priority is not None else "not_selected",
            )
            pending_updates.append(
                (tracking_id, updated, coin_id in selected_ids)
            )
            updated_by_coin[coin_id] = (tracking_id, updated)

        pending_starts: list[ExtremeMovementExperimentalTracking] = []
        new_coin_ids: list[str] = []
        seen_new: set[str] = set()
        for coin_id in comparison.experimental_coin_ids:
            if coin_id in self._active or coin_id in seen_new:
                continue
            asset = market.get(coin_id)
            priority = priorities.get(coin_id)
            if asset is None or priority is None:
                continue

            tracking = self._evaluator.start(
                coin_id=coin_id,
                observed_at=now,
                price=asset.current_price,
                direction=priority.direction,
                score=priority.score,
                evidence_count=priority.evidence_count,
                state=priority.state,
            )
            pending_starts.append(tracking)
            new_coin_ids.append(coin_id)
            seen_new.add(coin_id)

        if not pending_starts and not pending_updates and not pending_closes:
            return

        created_ids = self._store.save_batch(
            starts=tuple(pending_starts),
            updates=tuple(pending_updates),
            closes=tuple(pending_closes),
        )
        if len(created_ids) != len(pending_starts):
            # A transacao pode ter sido confirmada: recarregar no proximo ciclo.
            self._loaded = False
            self._active = {}
            raise RuntimeError("Quantidade inesperada de IDs no lote.")

        # Atualizar a memoria somente depois do COMMIT.
        for coin_id in closed_coin_ids:
            self._active.pop(coin_id, None)
        self._active.update(updated_by_coin)
        for coin_id, tracking_id, tracking in zip(
            new_coin_ids, created_ids, pending_starts
        ):
            self._active[coin_id] = (tracking_id, tracking)

    @property
    def active_count(self) -> int:
        return len(self._active)
