"""Cadastro de dispositivos push com protecao de instalacoes vinculadas.

O registro legado continua disponivel para instalacoes SEM proprietario.
Instalacoes vinculadas so poderao atualizar o token por um futuro fluxo
AUTENTICADO. Nao utilizar este servico para reivindicar instalacoes.
"""

from typing import Optional, Protocol

from app.push.push_device import PushDevice
from app.push.push_device_store import PushDeviceStore


class PushInstallationOwnerReader(Protocol):
    def load_owner_uid(self, installation_id: str) -> Optional[str]: ...


class ProtectedInstallationRegistrationError(PermissionError):
    """O registro publico nao pode modificar instalacao vinculada."""


class PushDeviceRegistrationService:
    def __init__(
        self,
        *,
        store: PushDeviceStore,
        owner_store: Optional[PushInstallationOwnerReader] = None,
    ) -> None:
        self._store = store
        self._owner_store = owner_store

    def register(
        self,
        *,
        installation_id: str,
        fcm_token: str,
        firebase_installation_id: Optional[str] = None,
        platform: str = "android",
    ) -> PushDevice:
        device = PushDevice(
            installation_id=installation_id,
            fcm_token=fcm_token,
            firebase_installation_id=firebase_installation_id,
            platform=platform,
            enabled=True,
        )

        if self._owner_store is not None:
            # Falha na consulta deve impedir o cadastro, nunca autoriza-lo.
            owner_uid = self._owner_store.load_owner_uid(
                device.installation_id,
            )
            if owner_uid is not None:
                raise ProtectedInstallationRegistrationError(
                    "Instalacao protegida: registro autenticado necessario."
                )

        self._store.save_device(device)
        return device
