from typing import Callable, Optional

from app.ai.market_domain import (
    MarketDomain,
)
from app.services.market_data_service import (
    get_market_data,
)


class AssetAnalysisDataError(
    RuntimeError
):
    pass


class CryptoAssetAnalysisProvider:
    def __init__(
        self,
        *,
        fetch_market_data: Optional[
            Callable[[str], Optional[dict]]
        ] = None,
    ) -> None:
        self._fetch_market_data = (
            fetch_market_data
            or get_market_data
        )

    @property
    def domain(
        self,
    ) -> MarketDomain:
        return MarketDomain.CRYPTO

    def fetch(
        self,
        asset_id: str,
    ) -> dict:
        normalized_asset_id = (
            asset_id.strip().lower()
        )

        if not normalized_asset_id:
            raise ValueError(
                "asset_id must not be empty"
            )

        market = self._fetch_market_data(
            normalized_asset_id
        )

        if not isinstance(
            market,
            dict,
        ) or not market:
            raise AssetAnalysisDataError(
                "Dados do ativo indisponíveis."
            )

        return market