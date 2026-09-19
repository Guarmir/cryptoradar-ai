import os
from dataclasses import dataclass
from typing import Mapping, Optional


DATABASE_URL_ENV = (
    "CRYPTORADAR_DATABASE_URL"
)

PUSH_SCOPE_ENV = (
    "CRYPTORADAR_PUSH_SCOPE"
)

MARKET_EVENT_PUSH_ENABLED_ENV = (
    "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED"
)

MARKET_EVENT_MINIMUM_CHANGE_ENV = (
    "CRYPTORADAR_MARKET_EVENT_MINIMUM_PRICE_CHANGE_PERCENT"
)

MARKET_EVENT_PUSH_COOLDOWN_ENV = (
    "CRYPTORADAR_MARKET_EVENT_PUSH_COOLDOWN_SECONDS"
)


@dataclass(frozen=True)
class MarketEventPushRuntimeConfig:
    enabled: bool = False
    database_url: Optional[str] = None
    scope_key: Optional[str] = None
    minimum_price_change_percent: float = 1.0
    cooldown_seconds: float = 300.0

    def __post_init__(self):
        if self.minimum_price_change_percent <= 0:
            raise ValueError(
                "A variacao minima de preco "
                "deve ser maior que zero."
            )

        if self.cooldown_seconds <= 0:
            raise ValueError(
                "O cooldown de push deve "
                "ser maior que zero."
            )

        if not self.enabled:
            return

        if not self.database_url:
            raise ValueError(
                "CRYPTORADAR_DATABASE_URL e "
                "obrigatoria quando o push de "
                "evento de mercado esta habilitado."
            )

        if not self.scope_key:
            raise ValueError(
                "CRYPTORADAR_PUSH_SCOPE e "
                "obrigatorio quando o push de "
                "evento de mercado esta habilitado."
            )

    @classmethod
    def from_environment(
        cls,
        environment: Optional[
            Mapping[str, str]
        ] = None,
    ) -> "MarketEventPushRuntimeConfig":
        source = (
            environment
            if environment is not None
            else os.environ
        )

        enabled = _parse_enabled(
            source.get(
                MARKET_EVENT_PUSH_ENABLED_ENV,
            )
        )

        database_url = _optional_string(
            source.get(
                DATABASE_URL_ENV,
            )
        )

        scope_key = _optional_string(
            source.get(
                PUSH_SCOPE_ENV,
            )
        )

        if not enabled:
            return cls(
                enabled=False,
                database_url=database_url,
                scope_key=scope_key,
            )

        minimum_price_change_percent = (
            _parse_positive_float(
                source.get(
                    MARKET_EVENT_MINIMUM_CHANGE_ENV,
                ),
                default=1.0,
                environment_name=(
                    MARKET_EVENT_MINIMUM_CHANGE_ENV
                ),
            )
        )

        cooldown_seconds = (
            _parse_positive_float(
                source.get(
                    MARKET_EVENT_PUSH_COOLDOWN_ENV,
                ),
                default=300.0,
                environment_name=(
                    MARKET_EVENT_PUSH_COOLDOWN_ENV
                ),
            )
        )

        return cls(
            enabled=True,
            database_url=database_url,
            scope_key=scope_key,
            minimum_price_change_percent=(
                minimum_price_change_percent
            ),
            cooldown_seconds=cooldown_seconds,
        )


def _parse_enabled(
    value: Optional[str],
) -> bool:
    if value is None:
        return False

    normalized = value.strip().lower()

    if normalized in (
        "",
        "0",
        "false",
        "no",
        "off",
    ):
        return False

    if normalized in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return True

    raise ValueError(
        "Valor invalido para "
        "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED."
    )


def _parse_positive_float(
    value: Optional[str],
    *,
    default: float,
    environment_name: str,
) -> float:
    if value is None:
        return default

    normalized = value.strip()

    if not normalized:
        return default

    try:
        parsed = float(
            normalized,
        )
    except ValueError as error:
        raise ValueError(
            f"{environment_name} deve ser numerico."
        ) from error

    if parsed <= 0:
        raise ValueError(
            f"{environment_name} deve ser maior que zero."
        )

    return parsed


def _optional_string(
    value: Optional[str],
) -> Optional[str]:
    if value is None:
        return None

    normalized = value.strip()

    return normalized or None