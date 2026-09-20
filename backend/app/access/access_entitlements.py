from dataclasses import dataclass
from typing import Literal


AccessPlan = Literal[
    "free",
    "pro",
]


@dataclass(frozen=True)
class AccessEntitlements:
    plan: AccessPlan
    monitored_asset_limit: int
    automatic_market_alerts: bool
    futures_enabled: bool

    def __post_init__(self):
        if self.plan not in (
            "free",
            "pro",
        ):
            raise ValueError(
                "O plano de acesso deve ser "
                "'free' ou 'pro'."
            )

        if self.monitored_asset_limit < 1:
            raise ValueError(
                "O limite de ativos monitorados "
                "deve ser pelo menos 1."
            )

    @property
    def is_free(self) -> bool:
        return self.plan == "free"

    @property
    def is_pro(self) -> bool:
        return self.plan == "pro"