from datetime import datetime
from typing import Any, Mapping, Optional

from app.monitoring.monitoring_observation import MonitoringObservation
from app.monitoring.monitoring_state import MonitoringState
from app.monitoring.monitoring_target import MonitoringTarget


def monitoring_target_to_dict(
    target: MonitoringTarget,
) -> dict[str, Any]:
    return {
        "symbol": target.symbol,
        "coin_id": target.coin_id,
        "trading_mode": target.trading_mode,
        "has_open_position": target.has_open_position,
        "position_side": target.position_side,
        "entry_price": target.entry_price,
        "leverage": target.leverage,
    }


def monitoring_target_from_dict(
    data: Mapping[str, Any],
) -> MonitoringTarget:
    return MonitoringTarget(
        symbol=str(
            data.get("symbol") or ""
        ),
        coin_id=_optional_string(
            data.get("coin_id"),
        ),
        trading_mode=data.get(
            "trading_mode",
            "spot",
        ),
        has_open_position=bool(
            data.get(
                "has_open_position",
                False,
            )
        ),
        position_side=_optional_string(
            data.get("position_side"),
        ),
        entry_price=_optional_float(
            data.get("entry_price"),
        ),
        leverage=_optional_float(
            data.get("leverage"),
        ),
    )


def monitoring_observation_to_dict(
    observation: MonitoringObservation,
) -> dict[str, Any]:
    return {
        "symbol": observation.symbol,
        "price": observation.price,
        "volume": observation.volume,
        "market_cap": observation.market_cap,
        "change_24h": observation.change_24h,
        "observed_at": (
            observation.observed_at.isoformat()
            if observation.observed_at is not None
            else None
        ),
    }


def monitoring_observation_from_dict(
    data: Mapping[str, Any],
) -> MonitoringObservation:
    price = _required_float(
        data.get("price"),
        field_name="price",
    )

    return MonitoringObservation(
        symbol=str(
            data.get("symbol") or ""
        ),
        price=price,
        volume=_optional_float(
            data.get("volume"),
        ),
        market_cap=_optional_float(
            data.get("market_cap"),
        ),
        change_24h=_optional_float(
            data.get("change_24h"),
        ),
        observed_at=_optional_datetime(
            data.get("observed_at"),
        ),
    )


def monitoring_state_to_dict(
    state: MonitoringState,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "target": monitoring_target_to_dict(
            state.target,
        ),
        "previous_observation": (
            monitoring_observation_to_dict(
                state.previous_observation,
            )
            if state.previous_observation
            is not None
            else None
        ),
        "current_observation": (
            monitoring_observation_to_dict(
                state.current_observation,
            )
            if state.current_observation
            is not None
            else None
        ),
        "observation_count":
            state.observation_count,
    }


def monitoring_state_from_dict(
    data: Mapping[str, Any],
) -> MonitoringState:
    schema_version = data.get(
        "schema_version",
    )

    if schema_version != 1:
        raise ValueError(
            "Versão de persistência "
            "do monitoramento não suportada."
        )

    raw_target = data.get(
        "target",
    )

    if not isinstance(
        raw_target,
        Mapping,
    ):
        raise ValueError(
            "Alvo persistido inválido."
        )

    raw_previous = data.get(
        "previous_observation",
    )

    raw_current = data.get(
        "current_observation",
    )

    previous_observation = (
        monitoring_observation_from_dict(
            raw_previous,
        )
        if isinstance(
            raw_previous,
            Mapping,
        )
        else None
    )

    current_observation = (
        monitoring_observation_from_dict(
            raw_current,
        )
        if isinstance(
            raw_current,
            Mapping,
        )
        else None
    )

    observation_count = data.get(
        "observation_count",
        0,
    )

    if (
        isinstance(
            observation_count,
            bool,
        )
        or not isinstance(
            observation_count,
            int,
        )
    ):
        raise ValueError(
            "Quantidade de observações "
            "persistida inválida."
        )

    return MonitoringState(
        target=monitoring_target_from_dict(
            raw_target,
        ),
        previous_observation=
            previous_observation,
        current_observation=
            current_observation,
        observation_count=
            observation_count,
    )


def _optional_string(
    value: Any,
) -> Optional[str]:
    if value is None:
        return None

    normalized = str(
        value,
    ).strip()

    return normalized or None


def _required_float(
    value: Any,
    *,
    field_name: str,
) -> float:
    parsed = _optional_float(
        value,
    )

    if parsed is None:
        raise ValueError(
            f"O campo '{field_name}' "
            "deve conter um número válido."
        )

    return parsed


def _optional_float(
    value: Any,
) -> Optional[float]:
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:
        parsed = float(
            value,
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    if parsed != parsed:
        return None

    if parsed in (
        float("inf"),
        float("-inf"),
    ):
        return None

    return parsed


def _optional_datetime(
    value: Any,
) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    if not isinstance(
        value,
        str,
    ):
        return None

    normalized = value.strip()

    if not normalized:
        return None

    if normalized.endswith(
        "Z"
    ):
        normalized = (
            f"{normalized[:-1]}+00:00"
        )

    try:
        return datetime.fromisoformat(
            normalized,
        )
    except ValueError:
        return None