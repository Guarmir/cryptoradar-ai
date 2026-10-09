
import threading
import time
from collections.abc import Callable
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any


class CoinGeckoRequestBlocked(RuntimeError):
    pass


class CoinGeckoRequestCoordinator:
    def __init__(
        self,
        *,
        min_interval_seconds: float = 2.0,
        cooldown_seconds: float = 60.0,
        clock: Callable[[], float] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        if min_interval_seconds < 0:
            raise ValueError("Intervalo inválido.")

        if cooldown_seconds <= 0:
            raise ValueError("Cooldown inválido.")

        self._min_interval = min_interval_seconds
        self._cooldown = cooldown_seconds
        self._clock = clock or time.monotonic
        self._sleeper = sleeper or time.sleep
        self._lock = threading.Lock()
        self._next_request_at = 0.0
        self._blocked_until = 0.0

    def execute(
        self,
        request: Callable[[], Any],
    ) -> Any:
        # Serializa as chamadas HTTP entre threads.
        with self._lock:
            now = self._clock()

            if now < self._blocked_until:
                raise CoinGeckoRequestBlocked(
                    "CoinGecko temporariamente bloqueada."
                )

            wait = max(
                0.0,
                self._next_request_at - now,
            )

            if wait:
                self._sleeper(wait)

            now = self._clock()

            if now < self._blocked_until:
                raise CoinGeckoRequestBlocked(
                    "CoinGecko temporariamente bloqueada."
                )

            # Reserva o próximo intervalo antes da chamada.
            self._next_request_at = (
                now + self._min_interval
            )

            response = request()

            if getattr(response, "status_code", None) == 429:
                delay = self._retry_after_seconds(response)
                self._blocked_until = max(
                    self._blocked_until,
                    self._clock() + delay,
                )
                raise CoinGeckoRequestBlocked(
                    "Limite de requisições da CoinGecko atingido."
                )

            return response

    def _retry_after_seconds(self, response: Any) -> float:
        headers = getattr(response, "headers", {}) or {}
        value = headers.get("Retry-After")

        if value is None:
            return self._cooldown

        try:
            seconds = float(value)
            if 0 < seconds < 3600:
                return max(self._cooldown, seconds)
        except (TypeError, ValueError):
            pass

        try:
            date = parsedate_to_datetime(str(value))
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            seconds = (
                date - datetime.now(timezone.utc)
            ).total_seconds()
            if seconds > 0:
                return max(self._cooldown, seconds)
        except (TypeError, ValueError, OverflowError):
            pass

        return self._cooldown
