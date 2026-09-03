from dataclasses import dataclass


@dataclass(
    frozen=True,
)
class PushDevice:
    installation_id: str
    fcm_token: str
    platform: str = "android"
    enabled: bool = True

    def __post_init__(
        self,
    ):
        normalized_installation_id = (
            self.installation_id.strip()
        )

        normalized_fcm_token = (
            self.fcm_token.strip()
        )

        normalized_platform = (
            self.platform.strip().lower()
        )

        if not normalized_installation_id:
            raise ValueError(
                "O identificador da instalação "
                "não pode ser vazio."
            )

        if not normalized_fcm_token:
            raise ValueError(
                "O token FCM "
                "não pode ser vazio."
            )

        if not normalized_platform:
            raise ValueError(
                "A plataforma "
                "não pode ser vazia."
            )

        object.__setattr__(
            self,
            "installation_id",
            normalized_installation_id,
        )

        object.__setattr__(
            self,
            "fcm_token",
            normalized_fcm_token,
        )

        object.__setattr__(
            self,
            "platform",
            normalized_platform,
        )

    @property
    def can_receive_push(
        self,
    ) -> bool:
        return self.enabled and bool(
            self.fcm_token,
        )