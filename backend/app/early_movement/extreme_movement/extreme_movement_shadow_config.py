import os


class ExtremeMovementShadowConfig:
    ENV_NAME = "EXTREME_MOVEMENT_SHADOW_ENABLED"

    @classmethod
    def is_enabled(cls) -> bool:
        value = os.getenv(cls.ENV_NAME, "false")
        return value.strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )