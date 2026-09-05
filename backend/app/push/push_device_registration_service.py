from typing import Optional

from app.push.push_device import PushDevice
from app.push.push_device_store import PushDeviceStore


class PushDeviceRegistrationService:
    def __init__(
        self,
        *,
        store: PushDeviceStore,
    ):
        self._store = store

    def register(
        self,
        *,
        installation_id: str,
        fcm_token: str,
        firebase_installation_id: Optional[
            str
        ] = None,
        platform: str = "android",
    ) -> PushDevice:
        device = PushDevice(
            installation_id=installation_id,
            fcm_token=fcm_token,
            firebase_installation_id=(
                firebase_installation_id
            ),
            platform=platform,
            enabled=True,
        )

        self._store.save_device(
            device,
        )

        return device