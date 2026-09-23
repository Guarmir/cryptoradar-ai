from typing import Callable, Optional

from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
    calculate_asset_operational_range,
)
from app.services.market_data_service import (
    get_chart_data,
)


class CryptoAssetOperationalRangeProvider:
    def __init__(
        self,
        *,
        fetch_chart_data: Optional[
            Callable[[str, int], dict]
        ] = None,
        days: int = 1,
    ) -> None:
        if days < 1:
            raise ValueError(
                "days must be at least 1"
            )

        self._fetch_chart_data = (
            fetch_chart_data
            or get_chart_data
        )

        self._days = days

    def fetch(
        self,
        *,
        asset_id: str,
        current_price: float,
    ) -> Optional[
        AssetOperationalRangeAssessment
    ]:
        normalized_asset_id = (
            asset_id.strip().lower()
        )

        if not normalized_asset_id:
            raise ValueError(
                "asset_id must not be empty"
            )

        chart_data = (
            self._fetch_chart_data(
                normalized_asset_id,
                self._days,
            )
        )

        if not isinstance(
            chart_data,
            dict,
        ):
            return None

        raw_prices = chart_data.get(
            "prices",
            [],
        )

        if not isinstance(
            raw_prices,
            list,
        ):
            return None

        prices = []

        for point in raw_prices:
            price = (
                self._extract_price(
                    point
                )
            )

            if price is not None:
                prices.append(
                    price
                )

        return (
            calculate_asset_operational_range(
                current_price=current_price,
                prices=prices,
            )
        )

    @staticmethod
    def _extract_price(
        point,
    ) -> Optional[float]:
        candidate = None

        if (
            isinstance(point, (list, tuple))
            and len(point) >= 2
        ):
            candidate = point[1]

        elif isinstance(point, dict):
            candidate = (
                point.get("price")
                or point.get("value")
            )

        if candidate is None:
            return None

        try:
            return float(candidate)

        except (
            TypeError,
            ValueError,
        ):
            return None