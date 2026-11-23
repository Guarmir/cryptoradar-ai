from dataclasses import dataclass


@dataclass(frozen=True)
class PushNotificationPreferences:
    """Preferencias de alertas do scanner para uma instalacao.

    Quando nao ha registro armazenado, todas as categorias ficam habilitadas,
    preservando o comportamento das instalacoes antigas.
    """

    observation_enabled: bool = True
    early_movement_enabled: bool = True
    confirmed_movement_enabled: bool = True

    def __post_init__(self) -> None:
        for name in (
            "observation_enabled",
            "early_movement_enabled",
            "confirmed_movement_enabled",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} deve ser booleano.")

    def allows_state(self, state: str | None) -> bool:
        """Para estados desconhecidos, preserva o comportamento anterior."""
        if state == "observation":
            return self.observation_enabled
        if state == "early_movement":
            return self.early_movement_enabled
        if state == "confirmed_movement":
            return self.confirmed_movement_enabled
        return True
