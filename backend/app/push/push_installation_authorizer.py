"""Autoriza acesso a instalacoes APENAS mediante vinculo previamente verificado."""
from typing import Protocol

from fastapi import HTTPException, status

from app.push.firebase_identity_verifier import FirebaseIdentityVerifier


class InstallationOwnerReader(Protocol):
    def load_owner_uid(self, installation_id: str) -> str | None: ...


class PushInstallationAuthorizer:
    def __init__(
        self,
        *,
        identity_verifier: FirebaseIdentityVerifier,
        owner_store: InstallationOwnerReader,
    ) -> None:
        self._identity_verifier = identity_verifier
        self._owner_store = owner_store

    def authorize(
        self,
        *,
        authorization: str | None,
        installation_id: str,
    ) -> str:
        """Retorna UID autorizado; nunca cria vinculos por solicitacao do cliente."""
        uid = self._identity_verifier.verify_bearer(authorization)
        normalized_id = installation_id.strip()
        if not normalized_id:
            raise HTTPException(status_code=422, detail="Instalacao invalida.")
        stored_uid = self._owner_store.load_owner_uid(normalized_id)
        if stored_uid is None or stored_uid != uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso a instalacao nao autorizado.",
            )
        return uid
