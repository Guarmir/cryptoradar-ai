
import os


class ExtremeMovementPersistenceConfig:
    ENV_NAME = "EXTREME_MOVEMENT_PERSISTENCE_ENABLED"

    @classmethod
    def is_enabled(cls) -> bool:
        value = os.getenv(
            cls.ENV_NAME,
            "false",
        )

        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
