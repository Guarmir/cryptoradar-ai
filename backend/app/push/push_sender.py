from abc import ABC, abstractmethod

from app.push.push_delivery_models import (
    PushNotificationMessage,
    PushSendResult,
)
from app.push.push_device import (
    PushDevice,
)


class PushSender(ABC):
    @abstractmethod
    def send(
        self,
        *,
        device: PushDevice,
        message: PushNotificationMessage,
    ) -> PushSendResult:
        raise NotImplementedError