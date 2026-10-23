
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ActiveFollowupEntry:
    coin_id: str
    last_seen_cycle: int


class EarlyMovementScannerActiveFollowup:
    DEFAULT_MAX_ASSETS = 8
    DEFAULT_TTL_CYCLES = 12

    def __init__(
        self,
        *,
        max_assets: int = DEFAULT_MAX_ASSETS,
        ttl_cycles: int = DEFAULT_TTL_CYCLES,
    ) -> None:
        if max_assets < 1:
            raise ValueError(
                "O limite de ativos deve ser maior que zero."
            )

        if ttl_cycles < 1:
            raise ValueError(
                "O prazo de acompanhamento deve ser maior que zero."
            )

        self._max_assets = max_assets
        self._ttl_cycles = ttl_cycles
        self._cycle = 0
        self._entries: dict[str, ActiveFollowupEntry] = {}

    def advance_cycle(self) -> None:
        self._cycle += 1
        self._expire()

    def observe(self, coin_ids: Iterable[str]) -> None:
        for coin_id in coin_ids:
            if not isinstance(coin_id, str):
                continue

            normalized = coin_id.strip()

            if not normalized:
                continue

            self._entries[normalized] = ActiveFollowupEntry(
                coin_id=normalized,
                last_seen_cycle=self._cycle,
            )

        self._expire()
        self._trim()

    def active_ids(self) -> tuple[str, ...]:
        self._expire()

        ordered = sorted(
            self._entries.values(),
            key=lambda entry: (
                -entry.last_seen_cycle,
                entry.coin_id,
            ),
        )

        return tuple(
            entry.coin_id
            for entry in ordered
        )

    def _expire(self) -> None:
        self._entries = {
            coin_id: entry
            for coin_id, entry in self._entries.items()
            if (
                self._cycle - entry.last_seen_cycle
                < self._ttl_cycles
            )
        }

    def _trim(self) -> None:
        if len(self._entries) <= self._max_assets:
            return

        ordered = sorted(
            self._entries.values(),
            key=lambda entry: (
                -entry.last_seen_cycle,
                entry.coin_id,
            ),
        )

        self._entries = {
            entry.coin_id: entry
            for entry in ordered[:self._max_assets]
        }
