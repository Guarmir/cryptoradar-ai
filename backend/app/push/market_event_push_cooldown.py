from datetime import datetime

from app.monitoring.market_event import MarketEvent


class MarketEventPushCooldown:
    def __init__(
        self,
        *,
        cooldown_seconds: float,
    ):
        if cooldown_seconds <= 0:
            raise ValueError(
                "O cooldown deve ser maior que zero."
            )

        self._cooldown_seconds = float(
            cooldown_seconds,
        )

        self._last_delivered_at: dict[
            tuple[str, str],
            datetime,
        ] = {}

    @property
    def cooldown_seconds(self) -> float:
        return self._cooldown_seconds

    def can_deliver(
        self,
        event: MarketEvent,
    ) -> bool:
        key = self._event_key(
            event,
        )

        last_delivered_at = (
            self._last_delivered_at.get(
                key,
            )
        )

        if last_delivered_at is None:
            return True

        if event.observed_at <= last_delivered_at:
            return False

        elapsed_seconds = (
            event.observed_at
            - last_delivered_at
        ).total_seconds()

        return (
            elapsed_seconds
            >= self._cooldown_seconds
        )

    def mark_delivered(
        self,
        event: MarketEvent,
    ) -> None:
        key = self._event_key(
            event,
        )

        previous = self._last_delivered_at.get(
            key,
        )

        if (
            previous is None
            or event.observed_at > previous
        ):
            self._last_delivered_at[
                key
            ] = event.observed_at

    def clear(self) -> None:
        self._last_delivered_at.clear()

    @staticmethod
    def _event_key(
        event: MarketEvent,
    ) -> tuple[str, str]:
        return (
            event.symbol,
            event.event_type,
        )