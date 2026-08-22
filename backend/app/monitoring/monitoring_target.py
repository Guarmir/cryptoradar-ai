from dataclasses import dataclass
from typing import Literal, Optional

TradingMode = Literal["spot", "futures"]
PositionSide = Literal["long", "short"]


@dataclass(frozen=True)
class MonitoringTarget:
    symbol: str
    coin_id: Optional[str] = None
    trading_mode: TradingMode = "spot"
    has_open_position: bool = False
    position_side: Optional[PositionSide] = None
    entry_price: Optional[float] = None
    leverage: Optional[float] = None

    def __post_init__(self):
        normalized_symbol = self.symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("O símbolo do ativo não pode ser vazio.")

        object.__setattr__(
            self,
            "symbol",
            normalized_symbol,
        )

        if self.coin_id is not None:
            normalized_coin_id = self.coin_id.strip().lower()

            object.__setattr__(
                self,
                "coin_id",
                normalized_coin_id or None,
            )

        if self.trading_mode not in ("spot", "futures"):
            raise ValueError(
                "O modo de negociação deve ser 'spot' ou 'futures'."
            )

        if not self.has_open_position:
            if self.position_side is not None:
                raise ValueError(
                    "Uma posição fechada não pode possuir direção."
                )

            if self.entry_price is not None:
                raise ValueError(
                    "Uma posição fechada não pode possuir preço de entrada."
                )

            if self.leverage is not None:
                raise ValueError(
                    "Uma posição fechada não pode possuir alavancagem."
                )

            return

        if self.entry_price is None or self.entry_price <= 0:
            raise ValueError(
                "Uma posição aberta exige preço de entrada maior que zero."
            )

        if self.trading_mode == "spot":
            if self.position_side is not None:
                raise ValueError(
                    "Posições Spot não utilizam direção LONG/SHORT."
                )

            if self.leverage is not None:
                raise ValueError(
                    "Posições Spot não utilizam alavancagem."
                )

            return

        if self.position_side not in ("long", "short"):
            raise ValueError(
                "Posições Futures exigem direção 'long' ou 'short'."
            )

        if self.leverage is None or self.leverage < 1:
            raise ValueError(
                "Posições Futures exigem alavancagem igual ou superior a 1x."
            )

    @property
    def is_spot(self) -> bool:
        return self.trading_mode == "spot"

    @property
    def is_futures(self) -> bool:
        return self.trading_mode == "futures"

    @property
    def is_long(self) -> bool:
        return (
            self.is_futures
            and self.has_open_position
            and self.position_side == "long"
        )

    @property
    def is_short(self) -> bool:
        return (
            self.is_futures
            and self.has_open_position
            and self.position_side == "short"
        )