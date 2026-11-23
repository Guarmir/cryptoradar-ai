"""Cadastro de dispositivos push com protecao de instalacoes vinculadas.

O registro legado continua disponivel para instalacoes SEM proprietario.
Instalacoes vinculadas so podem renovar o token pelo fluxo autenticado.
Nenhum dos fluxos abaixo cria ou reivindica vinculos de propriedade.
"""

from typing import Optional, Protocol

from app.push.push_device import PushDevice
from app.push.push_device_store import PushDeviceStore


class PushInstallationOwnerReader(Protocol):
    def load_owner_uid(self, installation_id: str) -> Optional[str]: ...


class ProtectedInstallationRegistrationError(PermissionError):
    """O cadastro solicitado nao tem autorizacao sobre a instalacao."""


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

    def register_authenticated(
        self,
        *,
        installation_id: str,
        authenticated_uid: str,
        fcm_token: str,
        firebase_installation_id: Optional[str] = None,
        platform: str = "android",
    ) -> PushDevice:
        """Renova token de instalacao JA vinculada ao UID autenticado.

        A identidade deve vir de token Firebase verificado pelo servidor,
        nunca de um campo UID enviado sem autenticacao pelo cliente.
        """
        device = PushDevice(
            installation_id=installation_id,
            fcm_token=fcm_token,
            firebase_installation_id=firebase_installation_id,
            platform=platform,
            enabled=True,
        )
        uid = authenticated_uid.strip()
        if not uid:
            raise ProtectedInstallationRegistrationError(
                "Identidade autenticada obrigatoria."
            )
        if self._owner_store is None:
            raise ProtectedInstallationRegistrationError(
                "Autorizacao da instalacao indisponivel."
            )

        # Nao reivindicar dispositivos antigos, nem autorizar UID diferente.
        owner_uid = self._owner_store.load_owner_uid(device.installation_id)
        if owner_uid != uid:
            raise ProtectedInstallationRegistrationError(
                "Identidade nao autorizada para esta instalacao."
            )

        existing = self._store.load_device(device.installation_id)
        if existing is None:
            raise ProtectedInstallationRegistrationError(
                "Instalacao vinculada nao encontrada."
            )

        # Preservar estado operacional anterior na renovacao de token.
        updated_device = PushDevice(
            installation_id=device.installation_id,
            fcm_token=device.fcm_token,
            firebase_installation_id=device.firebase_installation_id,
            platform=device.platform,
            enabled=existing.enabled,
        )
        self._store.save_device(updated_device)
        return updated_device
