from abc import ABC, abstractmethod

from app.push.push_delivery_models import (
    PushNotificationMessage,
    PushSendResult,
)


class PushSender(ABC):
    @abstractmethod
    def send(
        self,
        *,
        fcm_token: str,
        message: PushNotificationMessage,
    ) -> PushSendResult:
        raise NotImplementedError