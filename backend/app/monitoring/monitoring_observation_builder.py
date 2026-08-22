from datetime import datetime
from typing import Any, Mapping, Optional

from app.monitoring.monitoring_observation import MonitoringObservation
from app.monitoring.monitoring_target import MonitoringTarget


def build_monitoring_observation(
    target: MonitoringTarget,
    market_data: Mapping[str, Any],
) -> MonitoringObservation:
    price = _required_positive_float(
        _first_available(
            market_data,
            "current_price",
            "price",
            "price_usd",
        ),
        field_name="price",
    )

    volume = _optional_non_negative_float(
        _first_available(
            market_data,
            "total_volume",
            "volume",
            "volume_24h",
        ),
    )

    market_cap = _optional_non_negative_float(
        _first_available(
            market_data,
            "market_cap",
        ),
    )

    change_24h = _optional_float(
        _first_available(
            market_data,
            "price_change_percentage_24h",
            "change_24h",
        ),
    )

    observed_at = _parse_datetime(
        _first_available(
            market_data,
            "last_updated",
            "observed_at",
        ),
    )

    return MonitoringObservation(
        symbol=target.symbol,
        price=price,
        volume=volume,
        market_cap=market_cap,
        change_24h=change_24h,
        observed_at=observed_at,
    )


def _first_available(
    data: Mapping[str, Any],
    *keys: str,
) -> Any:
    for key in keys:
        value = data.get(key)

        if value is not None:
            return value

    return None


def _required_positive_float(
    value: Any,
    *,
    field_name: str,
) -> float:
    parsed = _optional_float(value)

    if parsed is None or parsed <= 0:
        raise ValueError(
            f"O campo '{field_name}' deve conter "
            "um número maior que zero."
        )

    return parsed


def _optional_non_negative_float(
    value: Any,
) -> Optional[float]:
    parsed = _optional_float(value)

    if parsed is None:
        return None

    if parsed < 0:
        return None

    return parsed


def _optional_float(
    value: Any,
) -> Optional[float]:
    if value is None:
        return None

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None

    if parsed != parsed:
        return None

    if parsed in (float("inf"), float("-inf")):
        return None

    return parsed


def _parse_datetime(
    value: Any,
) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        return None

    normalized = value.strip()

    if not normalized:
        return None

    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        return datetime.fromisoformat(
            normalized,
        )
    except ValueError:
        return None