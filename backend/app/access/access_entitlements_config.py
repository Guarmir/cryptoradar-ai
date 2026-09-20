import os
from dataclasses import dataclass
from typing import Mapping, Optional

from app.access.access_entitlements import (
    AccessEntitlements,
)


FREE_ASSET_LIMIT_ENV = (
    "CRYPTORADAR_FREE_MONITORED_ASSET_LIMIT"
)

FREE_ALERTS_ENABLED_ENV = (
    "CRYPTORADAR_FREE_AUTOMATIC_MARKET_ALERTS"
)

FREE_FUTURES_ENABLED_ENV = (
    "CRYPTORADAR_FREE_FUTURES_ENABLED"
)

PRO_ASSET_LIMIT_ENV = (
    "CRYPTORADAR_PRO_MONITORED_ASSET_LIMIT"
)

PRO_ALERTS_ENABLED_ENV = (
    "CRYPTORADAR_PRO_AUTOMATIC_MARKET_ALERTS"
)

PRO_FUTURES_ENABLED_ENV = (
    "CRYPTORADAR_PRO_FUTURES_ENABLED"
)


@dataclass(frozen=True)
class AccessEntitlementsConfig:
    free: AccessEntitlements
    pro: AccessEntitlements

    @classmethod
    def from_environment(
        cls,
        environment: Optional[
            Mapping[str, str]
        ] = None,
    ) -> "AccessEntitlementsConfig":
        source = (
            environment
            if environment is not None
            else os.environ
        )

        free = AccessEntitlements(
            plan="free",
            monitored_asset_limit=(
                _parse_positive_int(
                    source.get(
                        FREE_ASSET_LIMIT_ENV,
                    ),
                    default=1,
                    environment_name=(
                        FREE_ASSET_LIMIT_ENV
                    ),
                )
            ),
            automatic_market_alerts=(
                _parse_bool(
                    source.get(
                        FREE_ALERTS_ENABLED_ENV,
                    ),
                    default=False,
                    environment_name=(
                        FREE_ALERTS_ENABLED_ENV
                    ),
                )
            ),
            futures_enabled=(
                _parse_bool(
                    source.get(
                        FREE_FUTURES_ENABLED_ENV,
                    ),
                    default=False,
                    environment_name=(
                        FREE_FUTURES_ENABLED_ENV
                    ),
                )
            ),
        )

        pro = AccessEntitlements(
            plan="pro",
            monitored_asset_limit=(
                _parse_positive_int(
                    source.get(
                        PRO_ASSET_LIMIT_ENV,
                    ),
                    default=10,
                    environment_name=(
                        PRO_ASSET_LIMIT_ENV
                    ),
                )
            ),
            automatic_market_alerts=(
                _parse_bool(
                    source.get(
                        PRO_ALERTS_ENABLED_ENV,
                    ),
                    default=True,
                    environment_name=(
                        PRO_ALERTS_ENABLED_ENV
                    ),
                )
            ),
            futures_enabled=(
                _parse_bool(
                    source.get(
                        PRO_FUTURES_ENABLED_ENV,
                    ),
                    default=True,
                    environment_name=(
                        PRO_FUTURES_ENABLED_ENV
                    ),
                )
            ),
        )

        return cls(
            free=free,
            pro=pro,
        )


def _parse_positive_int(
    value: Optional[str],
    *,
    default: int,
    environment_name: str,
) -> int:
    if value is None:
        return default

    normalized = value.strip()

    if not normalized:
        return default

    try:
        parsed = int(
            normalized,
        )
    except ValueError as error:
        raise ValueError(
            f"{environment_name} deve ser inteiro."
        ) from error

    if parsed < 1:
        raise ValueError(
            f"{environment_name} deve ser maior que zero."
        )

    return parsed


def _parse_bool(
    value: Optional[str],
    *,
    default: bool,
    environment_name: str,
) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return True

    if normalized in (
        "0",
        "false",
        "no",
        "off",
    ):
        return False

    raise ValueError(
        f"Valor invalido para {environment_name}."
    )