import os
from dataclasses import dataclass
from typing import Mapping, Optional


MONITORING_ENABLED_ENV = (
    "CRYPTORADAR_MONITORING_ENABLED"
)

DATABASE_URL_ENV = (
    "CRYPTORADAR_DATABASE_URL"
)

MONITORING_SCOPE_ENV = (
    "CRYPTORADAR_MONITORING_SCOPE"
)

MONITORING_INTERVAL_ENV = (
    "CRYPTORADAR_MONITORING_INTERVAL_SECONDS"
)


@dataclass(frozen=True)
class MonitoringRuntimeConfig:
    enabled: bool = False
    database_url: Optional[str] = None
    scope_key: Optional[str] = None
    interval_seconds: float = 60.0

    def __post_init__(self):
        if self.interval_seconds <= 0:
            raise ValueError(
                "O intervalo do monitoramento "
                "deve ser maior que zero."
            )

        if not self.enabled:
            return

        if not self.database_url:
            raise ValueError(
                "CRYPTORADAR_DATABASE_URL é "
                "obrigatória quando o "
                "monitoramento está habilitado."
            )

        if not self.scope_key:
            raise ValueError(
                "CRYPTORADAR_MONITORING_SCOPE é "
                "obrigatório quando o "
                "monitoramento está habilitado."
            )

    @classmethod
    def from_environment(
        cls,
        environment: Optional[
            Mapping[str, str]
        ] = None,
    ) -> "MonitoringRuntimeConfig":
        source = (
            environment
            if environment is not None
            else os.environ
        )

        enabled = _parse_enabled(
            source.get(
                MONITORING_ENABLED_ENV,
            )
        )

        database_url = _optional_string(
            source.get(
                DATABASE_URL_ENV,
            )
        )

        scope_key = _optional_string(
            source.get(
                MONITORING_SCOPE_ENV,
            )
        )

        interval_seconds = (
            _parse_interval(
                source.get(
                    MONITORING_INTERVAL_ENV,
                )
            )
        )

        return cls(
            enabled=enabled,
            database_url=database_url,
            scope_key=scope_key,
            interval_seconds=interval_seconds,
        )


def _parse_enabled(
    value: Optional[str],
) -> bool:
    if value is None:
        return False

    normalized = (
        value.strip().lower()
    )

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
        "Valor inválido para "
        "CRYPTORADAR_MONITORING_ENABLED."
    )


def _parse_interval(
    value: Optional[str],
) -> float:
    if value is None:
        return 60.0

    normalized = value.strip()

    if not normalized:
        return 60.0

    try:
        parsed = float(
            normalized,
        )
    except ValueError as error:
        raise ValueError(
            "CRYPTORADAR_MONITORING_INTERVAL_SECONDS "
            "deve ser numérico."
        ) from error

    if parsed <= 0:
        raise ValueError(
            "CRYPTORADAR_MONITORING_INTERVAL_SECONDS "
            "deve ser maior que zero."
        )

    return parsed


def _optional_string(
    value: Optional[str],
) -> Optional[str]:
    if value is None:
        return None

    normalized = value.strip()

    return normalized or None