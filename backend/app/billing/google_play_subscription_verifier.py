"""Consulta a Google Play sobre uma assinatura, sem conceder permissoes.

Este componente nao vincula compras a usuarios, nao reconhece compras
(acknowledge) e nao altera planos. O acesso deve ser decidido por uma camada
autenticada com vinculacao persistente e prevencao de reutilizacao de tokens.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.parse import quote

GOOGLE_PLAY_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
_ALLOWED_ENTITLEMENT_STATES = frozenset({
    "SUBSCRIPTION_STATE_ACTIVE",
    "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
    "SUBSCRIPTION_STATE_CANCELED",
})


class GooglePlaySubscriptionVerificationError(Exception):
    """Falha ao consultar/verificar a resposta da Google Play."""


@dataclass(frozen=True)
class VerifiedGooglePlaySubscription:
    product_id: str
    state: str
    expires_at: datetime
    acknowledgement_state: str
    entitled_now: bool
    linked_purchase_token: str | None
    obfuscated_account_id: str | None = None


class GooglePlaySubscriptionVerifier:
    """Verifica produto, estado e validade utilizando a API oficial v2."""

    def __init__(
        self,
        *,
        package_name: str,
        product_id: str,
        credentials_provider: Callable[[], Any] | None = None,
        http_get: Callable[..., Any] | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        if not package_name or not package_name.strip():
            raise ValueError("package_name obrigatorio")
        if not product_id or not product_id.strip():
            raise ValueError("product_id obrigatorio")
        self._package_name = package_name.strip()
        self._product_id = product_id.strip()
        self._credentials_provider = credentials_provider
        self._http_get = http_get
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def verify(self, purchase_token: str) -> VerifiedGooglePlaySubscription:
        if not isinstance(purchase_token, str) or not purchase_token.strip():
            raise ValueError("purchase_token obrigatorio")
        try:
            credentials = self._credentials()
            if not credentials.valid:
                from google.auth.transport.requests import Request
                credentials.refresh(Request())
            if not credentials.valid or not credentials.token:
                raise GooglePlaySubscriptionVerificationError("Credencial Google invalida")
            import requests
            get = self._http_get or requests.get
            url = (
                "https://androidpublisher.googleapis.com/androidpublisher/v3/"
                f"applications/{quote(self._package_name, safe='')}/"
                "purchases/subscriptionsv2/tokens/"
                f"{quote(purchase_token.strip(), safe='')}"
            )
            response = get(
                url,
                headers={"Authorization": f"Bearer {credentials.token}"},
                timeout=15,
            )
            if response.status_code != 200:
                raise GooglePlaySubscriptionVerificationError(
                    f"Consulta Google Play falhou (HTTP {response.status_code})"
                )
            payload = response.json()
        except GooglePlaySubscriptionVerificationError:
            raise
        except Exception as exc:
            raise GooglePlaySubscriptionVerificationError(
                "Nao foi possivel consultar a assinatura na Google Play"
            ) from exc
        return self._parse(payload)

    def _credentials(self) -> Any:
        if self._credentials_provider is not None:
            return self._credentials_provider()
        import google.auth
        credentials, _ = google.auth.default(scopes=[GOOGLE_PLAY_SCOPE])
        return credentials

    def _parse(self, payload: Any) -> VerifiedGooglePlaySubscription:
        if not isinstance(payload, Mapping):
            raise GooglePlaySubscriptionVerificationError("Resposta invalida da Google Play")
        state = payload.get("subscriptionState")
        if not isinstance(state, str):
            raise GooglePlaySubscriptionVerificationError("Estado de assinatura ausente")
        line_items = payload.get("lineItems")
        if not isinstance(line_items, list):
            raise GooglePlaySubscriptionVerificationError("Itens da assinatura ausentes")
        matching = [item for item in line_items
                    if isinstance(item, Mapping) and item.get("productId") == self._product_id]
        if not matching:
            raise GooglePlaySubscriptionVerificationError("Produto de assinatura nao corresponde")
        try:
            expiries = [self._parse_timestamp(item["expiryTime"]) for item in matching]
        except (KeyError, ValueError, TypeError) as exc:
            raise GooglePlaySubscriptionVerificationError("Validade da assinatura invalida") from exc
        expires_at = max(expiries)
        now = self._now_provider()
        if now.tzinfo is None:
            raise ValueError("now_provider deve retornar datetime com fuso")
        acknowledgement = payload.get("acknowledgementState", "")
        linked_token = payload.get("linkedPurchaseToken")
        external_ids = payload.get("externalAccountIdentifiers")
        account_id = (external_ids.get("obfuscatedExternalAccountId")
                      if isinstance(external_ids, Mapping) else None)
        return VerifiedGooglePlaySubscription(
            product_id=self._product_id,
            state=state,
            expires_at=expires_at,
            acknowledgement_state=acknowledgement if isinstance(acknowledgement, str) else "",
            entitled_now=state in _ALLOWED_ENTITLEMENT_STATES and expires_at > now,
            linked_purchase_token=linked_token if isinstance(linked_token, str) else None,
            obfuscated_account_id=account_id if isinstance(account_id, str) else None,
        )

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if not isinstance(value, str):
            raise ValueError("timestamp invalido")
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("timestamp sem fuso")
        return date.astimezone(timezone.utc)
