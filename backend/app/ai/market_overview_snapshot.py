from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class MarketOverviewAsset:
    symbol: str
    name: str
    price_usd: float
    change_24h_percent: Optional[float]
    market_cap_usd: Optional[float]
    volume_24h_usd: Optional[float]

    def __post_init__(self):
        normalized_symbol = (
            self.symbol.strip().upper()
        )

        normalized_name = (
            self.name.strip()
        )

        if not normalized_symbol:
            raise ValueError(
                "O simbolo do ativo nao pode ser vazio."
            )

        if not normalized_name:
            raise ValueError(
                "O nome do ativo nao pode ser vazio."
            )

        if self.price_usd <= 0:
            raise ValueError(
                "O preco do ativo deve ser maior que zero."
            )

        object.__setattr__(
            self,
            "symbol",
            normalized_symbol,
        )

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )


@dataclass(frozen=True)
class MarketOverviewSnapshot:
    total_market_cap_usd: float
    total_volume_24h_usd: float
    market_cap_change_24h_percent: float
    btc_dominance_percent: float
    eth_dominance_percent: Optional[float]
    assets: tuple[
        MarketOverviewAsset,
        ...,
    ]
    observed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.total_market_cap_usd < 0:
            raise ValueError(
                "A capitalizacao total nao pode ser negativa."
            )

        if self.total_volume_24h_usd < 0:
            raise ValueError(
                "O volume total nao pode ser negativo."
            )

        if not (
            0
            <= self.btc_dominance_percent
            <= 100
        ):
            raise ValueError(
                "A dominancia do BTC deve ficar entre 0 e 100."
            )

        if (
            self.eth_dominance_percent is not None
            and not (
                0
                <= self.eth_dominance_percent
                <= 100
            )
        ):
            raise ValueError(
                "A dominancia do ETH deve ficar entre 0 e 100."
            )

        observed_at = self.observed_at

        if observed_at is None:
            observed_at = datetime.now(
                timezone.utc,
            )

        elif observed_at.tzinfo is None:
            observed_at = (
                observed_at.replace(
                    tzinfo=timezone.utc,
                )
            )

        object.__setattr__(
            self,
            "observed_at",
            observed_at,
        )

    @property
    def advancing_asset_count(self) -> int:
        return sum(
            1
            for asset in self.assets
            if (
                asset.change_24h_percent
                is not None
                and asset.change_24h_percent > 0
            )
        )

    @property
    def declining_asset_count(self) -> int:
        return sum(
            1
            for asset in self.assets
            if (
                asset.change_24h_percent
                is not None
                and asset.change_24h_percent < 0
            )
        )