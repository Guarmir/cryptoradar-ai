from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class MonitoringObservation:
    symbol: str
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    change_24h: Optional[float] = None
    observed_at: Optional[datetime] = None

    def __post_init__(self):
        normalized_symbol = self.symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("O símbolo do ativo não pode ser vazio.")

        object.__setattr__(
            self,
            "symbol",
            normalized_symbol,
        )

        if self.price <= 0:
            raise ValueError(
                "O preço observado deve ser maior que zero."
            )

        if self.volume is not None and self.volume < 0:
            raise ValueError(
                "O volume observado não pode ser negativo."
            )

        if self.market_cap is not None and self.market_cap < 0:
            raise ValueError(
                "A capitalização de mercado não pode ser negativa."
            )

        resolved_observed_at = self.observed_at

        if resolved_observed_at is None:
            resolved_observed_at = datetime.now(
                timezone.utc,
            )

        elif resolved_observed_at.tzinfo is None:
            resolved_observed_at = resolved_observed_at.replace(
                tzinfo=timezone.utc,
            )

        object.__setattr__(
            self,
            "observed_at",
            resolved_observed_at,
        )