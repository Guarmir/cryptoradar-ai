from dataclasses import dataclass, field
from typing import Mapping, Optional


@dataclass(
    frozen=True,
)
class PushNotificationMessage:
    title: str
    body: str
    data: Mapping[str, str] = field(
        default_factory=dict,
    )

    def __post_init__(
        self,
    ) -> None:
        normalized_title = self.title.strip()
        normalized_body = self.body.strip()

        if not normalized_title:
            raise ValueError(
                "O título da notificação "
                "não pode ser vazio."
            )

        if not normalized_body:
            raise ValueError(
                "O corpo da notificação "
                "não pode ser vazio."
            )

        normalized_data = {}

        for key, value in self.data.items():
            normalized_key = str(key).strip()

            if not normalized_key:
                continue

            normalized_data[
                normalized_key
            ] = str(value)

        object.__setattr__(
            self,
            "title",
            normalized_title,
        )

        object.__setattr__(
            self,
            "body",
            normalized_body,
        )

        object.__setattr__(
            self,
            "data",
            normalized_data,
        )


@dataclass(
    frozen=True,
)
class PushSendResult:
    delivered: bool
    invalid_token: bool = False
    error_code: Optional[str] = None

    def __post_init__(
        self,
    ) -> None:
        if self.delivered and self.invalid_token:
            raise ValueError(
                "Uma entrega concluída não "
                "pode possuir token inválido."
            )


@dataclass(
    frozen=True,
)
class PushDeliveryOutcome:
    installation_id: str
    delivered: bool
    invalid_token: bool = False
    error_code: Optional[str] = None


@dataclass(
    frozen=True,
)
class PushDeliveryBatchResult:
    outcomes: tuple[
        PushDeliveryOutcome,
        ...,
    ]

    @property
    def total(self) -> int:
        return len(
            self.outcomes,
        )

    @property
    def delivered(self) -> int:
        return sum(
            1
            for outcome in self.outcomes
            if outcome.delivered
        )

    @property
    def failed(self) -> int:
        return (
            self.total
            - self.delivered
        )

    @property
    def invalid_tokens(self) -> int:
        return sum(
            1
            for outcome in self.outcomes
            if outcome.invalid_token
        )