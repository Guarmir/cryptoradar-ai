
from collections.abc import Iterable
from typing import TypeVar

CandidateT = TypeVar("CandidateT")


class EarlyMovementScannerCandidateRotation:
    def __init__(
        self,
        *,
        priority_slots: int = 1,
    ) -> None:
        if priority_slots < 0:
            raise ValueError(
                "A reserva de prioridade não pode ser negativa."
            )

        self._priority_slots = priority_slots
        self._cycle = 0
        self._last_scheduled: dict[str, int] = {}
        self._last_successful: dict[str, int] = {}

    @staticmethod
    def _identity(candidate: CandidateT) -> str:
        coin_id = getattr(candidate, "coin_id", None)

        if isinstance(coin_id, str) and coin_id:
            return coin_id

        return str(candidate)

    def arrange(
        self,
        candidates: Iterable[CandidateT],
        *,
        acquisition_budget: int,
    ) -> tuple[CandidateT, ...]:
        if acquisition_budget < 1:
            raise ValueError(
                "O orçamento deve ser maior que zero."
            )

        ordered = tuple(candidates)

        if not ordered:
            return ()

        self._cycle += 1

        active_ids = {
            self._identity(candidate)
            for candidate in ordered
        }

        self._last_scheduled = {
            coin_id: cycle
            for coin_id, cycle in self._last_scheduled.items()
            if coin_id in active_ids
        }

        self._last_successful = {
            coin_id: cycle
            for coin_id, cycle in self._last_successful.items()
            if coin_id in active_ids
        }

        priority_count = min(
            self._priority_slots,
            acquisition_budget,
            len(ordered),
        )

        priority_candidates = ordered[:priority_count]

        fresh_priority = [
            candidate
            for candidate in priority_candidates
            if self._identity(candidate)
            not in self._last_successful
        ]

        priority = tuple(fresh_priority)

        priority_ids = {
            self._identity(candidate)
            for candidate in priority
        }

        remaining = tuple(
            candidate
            for candidate in ordered
            if self._identity(candidate)
            not in priority_ids
        )

        rotation_slots = max(
            acquisition_budget - len(priority),
            0,
        )

        rotated = sorted(
            enumerate(remaining),
            key=lambda item: (
                self._last_successful.get(
                    self._identity(item[1]),
                    -1,
                ),
                self._last_scheduled.get(
                    self._identity(item[1]),
                    -1,
                ),
                item[0],
            ),
        )

        selected = [
            candidate
            for _, candidate in rotated[:rotation_slots]
        ]

        for candidate in priority + tuple(selected):
            self._last_scheduled[
                self._identity(candidate)
            ] = self._cycle

        selected_positions = {
            index
            for index, _ in rotated[:rotation_slots]
        }

        rest = [
            candidate
            for index, candidate in enumerate(remaining)
            if index not in selected_positions
        ]

        return (
            priority
            + tuple(selected)
            + tuple(rest)
        )

    def record_success(self, coin_id: str) -> None:
        if not coin_id:
            return

        self._last_successful[coin_id] = self._cycle

    def record_failure(self, coin_id: str) -> None:
        # Uma falha não apaga o histórico
        # de aquisições bem-sucedidas.
        return
