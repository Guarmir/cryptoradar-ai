"""Vincula uma compra verificada a um UID Firebase autenticado.

A compra deve incluir o identificador de conta ofuscado enviado pelo
aplicativo ao iniciar a compra. Nao habilita PRO nem altera planos.
"""
from hashlib import sha256

from app.push.firebase_identity_verifier import FirebaseIdentityVerifier
from app.billing.google_play_subscription_verifier import (
    GooglePlaySubscriptionVerifier,
)
from app.billing.postgresql_google_play_subscription_store import (
    PostgreSQLGooglePlaySubscriptionStore,
)


class PurchaseIdentityMismatchError(Exception):
    """A Google Play nao confirma a conta Firebase que iniciou a compra."""


class PurchaseNotEntitledError(Exception):
    """A compra verificada nao da direito de acesso neste momento."""


def obfuscated_account_id(firebase_auth_uid: str) -> str:
    """Mesmo algoritmo a utilizar em GooglePlayPurchaseParam.applicationUserName."""
    if not isinstance(firebase_auth_uid, str) or not firebase_auth_uid.strip():
        raise ValueError("firebase_auth_uid obrigatorio")
    return sha256(firebase_auth_uid.strip().encode("utf-8")).hexdigest()


class GooglePlaySubscriptionClaimService:
    def __init__(
        self,
        *,
        identity_verifier: FirebaseIdentityVerifier,
        subscription_verifier: GooglePlaySubscriptionVerifier,
        subscription_store: PostgreSQLGooglePlaySubscriptionStore,
        package_name: str,
    ) -> None:
        if not isinstance(package_name, str) or not package_name.strip():
            raise ValueError("package_name obrigatorio")
        self._identity_verifier = identity_verifier
        self._subscription_verifier = subscription_verifier
        self._subscription_store = subscription_store
        self._package_name = package_name.strip()

    def claim(self, *, authorization: str | None, purchase_token: str) -> None:
        """Somente o servidor pode salvar uma compra vinculada e verificada.

        Rejeita compra sem conta ofuscada: ela nao prova o vinculo com UID.
        O chamador nunca informa UID, produto, estado, ou vencimento.
        """
        uid = self._identity_verifier.verify_bearer(authorization)
        verified = self._subscription_verifier.verify(purchase_token)
        if verified.obfuscated_account_id != obfuscated_account_id(uid):
            raise PurchaseIdentityMismatchError(
                "Compra sem vinculacao valida a identidade autenticada"
            )
        if not verified.entitled_now:
            raise PurchaseNotEntitledError("Assinatura nao esta ativa")
        # Compras vinculadas a tokens anteriores exigem politica propria para
        # upgrades, downgrade e recuperacao; nao assumir que sao transferiveis.
        if verified.linked_purchase_token:
            raise PurchaseIdentityMismatchError(
                "Compra encadeada exige validacao adicional"
            )
        self._subscription_store.save_verified(
            purchase_token=purchase_token,
            firebase_auth_uid=uid,
            package_name=self._package_name,
            product_id=verified.product_id,
            subscription_state=verified.state,
            acknowledgement_state=verified.acknowledgement_state,
            expires_at=verified.expires_at,
        )
