from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementScannerMarketAsset:
    coin_id: str
    symbol: str
    name: str
    current_price: float

    total_volume: Optional[float] = None
    market_cap: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    market_cap_rank: Optional[int] = None

    def __post_init__(
        self,
    ) -> None:
        coin_id = self.coin_id.strip()
        symbol = self.symbol.strip().upper()
        name = self.name.strip()

        if not coin_id:
            raise ValueError(
                "O coin_id não pode ser vazio."
            )

        if not symbol:
            raise ValueError(
                "O símbolo não pode ser vazio."
            )

        if not name:
            raise ValueError(
                "O nome não pode ser vazio."
            )

        if self.current_price <= 0:
            raise ValueError(
                "O preço deve ser maior que zero."
            )

        object.__setattr__(
            self,
            "coin_id",
            coin_id,
        )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )

        object.__setattr__(
            self,
            "name",
            name,
        )