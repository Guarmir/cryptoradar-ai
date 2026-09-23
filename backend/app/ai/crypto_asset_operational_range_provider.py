from typing import Callable, Optional

from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
    calculate_asset_operational_range,
)
from app.ai.asset_operational_range_recurrence_assessment import (
    AssetOperationalRangeRecurrenceAssessment,
    calculate_asset_operational_range_recurrence,
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
        prices = self._load_prices(
            asset_id
        )

        if prices is None:
            return None

        return (
            calculate_asset_operational_range(
                current_price=current_price,
                prices=prices,
            )
        )

    def fetch_recurrence(
        self,
        *,
        asset_id: str,
        current_price: float,
    ) -> Optional[
        AssetOperationalRangeRecurrenceAssessment
    ]:
        prices = self._load_prices(
            asset_id
        )

        if prices is None:
            return None

        range_assessment = (
            calculate_asset_operational_range(
                current_price=current_price,
                prices=prices,
            )
        )

        if range_assessment is None:
            return None

        return (
            calculate_asset_operational_range_recurrence(
                prices=prices,
                range_assessment=(
                    range_assessment
                ),
            )
        )

    def fetch_historical_average_volume(
        self,
        *,
        asset_id: str,
    ) -> Optional[float]:
        chart_data = (
            self._load_chart_data(
                asset_id
            )
        )

        if chart_data is None:
            return None

        raw_volumes = chart_data.get(
            "total_volumes",
            [],
        )

        if not isinstance(
            raw_volumes,
            list,
        ):
            return None

        values = []

        for point in raw_volumes:
            value = self._extract_value(
                point
            )

            if (
                value is not None
                and value > 0
            ):
                values.append(
                    value
                )

        if not values:
            return None

        return (
            sum(values)
            / len(values)
        )

    def _load_prices(
        self,
        asset_id: str,
    ) -> Optional[tuple[float, ...]]:
        chart_data = (
            self._load_chart_data(
                asset_id
            )
        )

        if chart_data is None:
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
            price = self._extract_value(
                point
            )

            if price is not None:
                prices.append(
                    price
                )

        return tuple(
            prices
        )

    def _load_chart_data(
        self,
        asset_id: str,
    ) -> Optional[dict]:
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

        return chart_data

    @staticmethod
    def _extract_value(
        point,
    ) -> Optional[float]:
        candidate = None

        if (
            isinstance(
                point,
                (
                    list,
                    tuple,
                ),
            )
            and len(point) >= 2
        ):
            candidate = point[1]

        elif isinstance(
            point,
            dict,
        ):
            candidate = (
                point.get("price")
                or point.get("volume")
                or point.get("value")
            )

        if candidate is None:
            return None

        try:
            return float(
                candidate
            )

        except (
            TypeError,
            ValueError,
        ):
            return None