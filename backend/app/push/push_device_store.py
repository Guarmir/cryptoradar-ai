from abc import ABC, abstractmethod
from typing import Optional

from app.push.push_device import PushDevice


class PushDeviceStore(ABC):
    @abstractmethod
    def load_device(
        self,
        installation_id: str,
    ) -> Optional[PushDevice]:
        raise NotImplementedError

    @abstractmethod
    def load_all(
        self,
    ) -> tuple[PushDevice, ...]:
        raise NotImplementedError

    @abstractmethod
    def load_enabled(
        self,
    ) -> tuple[PushDevice, ...]:
        raise NotImplementedError

    @abstractmethod
    def save_device(
        self,
        device: PushDevice,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_device(
        self,
        installation_id: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def clear(
        self,
    ) -> None:
        raise NotImplementedError