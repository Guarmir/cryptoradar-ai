from abc import ABC, abstractmethod
from typing import Optional

from app.access.access_entitlements import (
    AccessPlan,
)


class AccessPlanStore(ABC):
    @abstractmethod
    def load_plan(
        self,
        installation_id: str,
    ) -> Optional[AccessPlan]:
        raise NotImplementedError

    @abstractmethod
    def save_plan(
        self,
        *,
        installation_id: str,
        plan: AccessPlan,
    ) -> None:
        raise NotImplementedError