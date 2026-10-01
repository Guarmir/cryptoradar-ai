import os
from dataclasses import dataclass
from typing import Mapping, Optional


EARLY_MOVEMENT_SCANNER_ENABLED_ENV = (
    "CRYPTORADAR_EARLY_MOVEMENT_SCANNER_ENABLED"
)

EARLY_MOVEMENT_SCANNER_INTERVAL_ENV = (
    "CRYPTORADAR_EARLY_MOVEMENT_SCANNER_INTERVAL_SECONDS"
)

EARLY_MOVEMENT_SCANNER_PUSH_ENABLED_ENV = (
    "CRYPTORADAR_EARLY_MOVEMENT_SCANNER_PUSH_ENABLED"
)

EARLY_MOVEMENT_SCANNER_PUSH_COOLDOWN_ENV = (
    "CRYPTORADAR_EARLY_MOVEMENT_SCANNER_PUSH_COOLDOWN_SECONDS"
)

DATABASE_URL_ENV = (
    "CRYPTORADAR_DATABASE_URL"
)

PUSH_SCOPE_ENV = (
    "CRYPTORADAR_PUSH_SCOPE"
)


@dataclass(frozen=True)
class EarlyMovementScannerRuntimeConfig:
    enabled: bool = False
    interval_seconds: float = 300.0

    push_enabled: bool = False
    push_cooldown_seconds: float = 3600.0

    database_url: Optional[str] = None
    push_scope_key: Optional[str] = None

    def __post_init__(
        self,
    ) -> None:
        if self.interval_seconds <= 0:
            raise ValueError(
                "O intervalo do scanner deve "
                "ser maior que zero."
            )

        if self.push_cooldown_seconds <= 0:
            raise ValueError(
                "O cooldown do push do scanner "
                "deve ser maior que zero."
            )

        if not self.push_enabled:
            return

        if not self.database_url:
            raise ValueError(
                "CRYPTORADAR_DATABASE_URL e "
                "obrigatoria quando o push do "
                "scanner esta habilitado."
            )

        if not self.push_scope_key:
            raise ValueError(
                "CRYPTORADAR_PUSH_SCOPE e "
                "obrigatorio quando o push do "
                "scanner esta habilitado."
            )

    @classmethod
    def from_environment(
        cls,
        environment: Optional[
            Mapping[str, str]
        ] = None,
    ) -> "EarlyMovementScannerRuntimeConfig":
        source = (
            environment
            if environment is not None
            else os.environ
        )

        enabled = _parse_enabled(
            source.get(
                EARLY_MOVEMENT_SCANNER_ENABLED_ENV,
            ),
            environment_name=(
                EARLY_MOVEMENT_SCANNER_ENABLED_ENV
            ),
        )

        interval_seconds = (
            _parse_positive_float(
                source.get(
                    EARLY_MOVEMENT_SCANNER_INTERVAL_ENV,
                ),
               default=300.0,
                environment_name=(
                    EARLY_MOVEMENT_SCANNER_INTERVAL_ENV
                ),
            )
        )

        push_enabled = _parse_enabled(
            source.get(
                EARLY_MOVEMENT_SCANNER_PUSH_ENABLED_ENV,
            ),
            environment_name=(
                EARLY_MOVEMENT_SCANNER_PUSH_ENABLED_ENV
            ),
        )

        push_cooldown_seconds = (
            _parse_positive_float(
                source.get(
                    EARLY_MOVEMENT_SCANNER_PUSH_COOLDOWN_ENV,
                ),
                default=3600.0,
                environment_name=(
                    EARLY_MOVEMENT_SCANNER_PUSH_COOLDOWN_ENV
                ),
            )
        )

        database_url = _optional_string(
            source.get(
                DATABASE_URL_ENV,
            )
        )

        push_scope_key = _optional_string(
            source.get(
                PUSH_SCOPE_ENV,
            )
        )

        return cls(
            enabled=enabled,
            interval_seconds=interval_seconds,
            push_enabled=push_enabled,
            push_cooldown_seconds=(
                push_cooldown_seconds
            ),
            database_url=database_url,
            push_scope_key=push_scope_key,
        )


def _parse_enabled(
    value: Optional[str],
    *,
    environment_name: str,
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
        f"Valor invalido para {environment_name}."
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