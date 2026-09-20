from app.access.access_entitlements import (
    AccessPlan,
)
from app.access.access_plan_store import (
    AccessPlanStore,
)


class AccessPlanResolver:
    def __init__(
        self,
        *,
        store: AccessPlanStore,
    ):
        self._store = store

    def resolve_plan(
        self,
        installation_id: str,
    ) -> AccessPlan:
        normalized_installation_id = (
            installation_id.strip()
        )

        if not normalized_installation_id:
            raise ValueError(
                "O installation_id "
                "nao pode ser vazio."
            )

        stored_plan = self._store.load_plan(
            normalized_installation_id,
        )

        if stored_plan is None:
            return "free"

        return stored_plan