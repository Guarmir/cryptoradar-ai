import os
from dataclasses import dataclass
from typing import Mapping, Optional


DATABASE_URL_ENV = (
    "CRYPTORADAR_DATABASE_URL"
)

ACCESS_ENABLED_ENV = (
    "CRYPTORADAR_ACCESS_ENABLED"
)

ACCESS_SCOPE_ENV = (
    "CRYPTORADAR_ACCESS_SCOPE"
)


@dataclass(frozen=True)
class AccessApiConfig:
    enabled: bool = False
    database_url: Optional[str] = None
    scope_key: Optional[str] = None

    def __post_init__(self):
        if not self.enabled:
            return

        if not self.database_url:
            raise ValueError(
                "CRYPTORADAR_DATABASE_URL e "
                "obrigatoria quando o acesso "
                "comercial esta habilitado."
            )

        if not self.scope_key:
            raise ValueError(
                "CRYPTORADAR_ACCESS_SCOPE e "
                "obrigatorio quando o acesso "
                "comercial esta habilitado."
            )

    @classmethod
    def from_environment(
        cls,
        environment: Optional[
            Mapping[str, str]
        ] = None,
    ) -> "AccessApiConfig":
        source = (
            environment
            if environment is not None
            else os.environ
        )

        return cls(
            enabled=_parse_enabled(
                source.get(
                    ACCESS_ENABLED_ENV,
                )
            ),
            database_url=_optional_string(
                source.get(
                    DATABASE_URL_ENV,
                )
            ),
            scope_key=_optional_string(
                source.get(
                    ACCESS_SCOPE_ENV,
                )
            ),
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
        "CRYPTORADAR_ACCESS_ENABLED."
    )


def _optional_string(
    value: Optional[str],
) -> Optional[str]:
    if value is None:
        return None

    normalized = value.strip()

    return normalized or None