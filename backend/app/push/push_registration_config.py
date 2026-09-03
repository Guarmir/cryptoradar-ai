import os
from dataclasses import dataclass
from typing import Mapping, Optional


DATABASE_URL_ENV = (
    "CRYPTORADAR_DATABASE_URL"
)

PUSH_REGISTRATION_ENABLED_ENV = (
    "CRYPTORADAR_PUSH_REGISTRATION_ENABLED"
)

PUSH_SCOPE_ENV = (
    "CRYPTORADAR_PUSH_SCOPE"
)


@dataclass(
    frozen=True,
)
class PushRegistrationConfig:
    enabled: bool = False
    database_url: Optional[str] = None
    scope_key: Optional[str] = None

    def __post_init__(
        self,
    ):
        if not self.enabled:
            return

        if not self.database_url:
            raise ValueError(
                "CRYPTORADAR_DATABASE_URL é "
                "obrigatória quando o registro "
                "de push está habilitado."
            )

        if not self.scope_key:
            raise ValueError(
                "CRYPTORADAR_PUSH_SCOPE é "
                "obrigatório quando o registro "
                "de push está habilitado."
            )

    @classmethod
    def from_environment(
        cls,
        environment: Optional[
            Mapping[str, str]
        ] = None,
    ) -> "PushRegistrationConfig":
        source = (
            environment
            if environment is not None
            else os.environ
        )

        enabled = _parse_enabled(
            source.get(
                PUSH_REGISTRATION_ENABLED_ENV,
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

        return cls(
            enabled=enabled,
            database_url=database_url,
            scope_key=scope_key,
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
        "CRYPTORADAR_PUSH_REGISTRATION_ENABLED."
    )


def _optional_string(
    value: Optional[str],
) -> Optional[str]:
    if value is None:
        return None

    normalized = value.strip()

    return normalized or None