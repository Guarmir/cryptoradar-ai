"""Authenticated Google Play claim. Does not grant PRO or acknowledge purchases."""
import os
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.access.access_api_config import AccessApiConfig
from app.billing.google_play_subscription_claim_service import (
    GooglePlaySubscriptionClaimService,
    PurchaseIdentityMismatchError,
    PurchaseNotEntitledError,
)
from app.billing.google_play_subscription_verifier import (
    GooglePlaySubscriptionVerifier,
    GooglePlaySubscriptionVerificationError,
)
from app.billing.postgresql_google_play_subscription_store import (
    PostgreSQLGooglePlaySubscriptionStore,
    PurchaseTokenAlreadyClaimedError,
)
from app.push.firebase_identity_verifier import FirebaseIdentityVerifier


class SubscriptionClaimRequest(BaseModel):
    purchase_token: str = Field(min_length=1, max_length=8192)


class SubscriptionClaimResponse(BaseModel):
    status: Literal["verified"] = "verified"
    pro_granted: Literal[False] = False


def create_claim_service() -> GooglePlaySubscriptionClaimService:
    # Opt-in: never enable billing implicitly when the API starts.
    if os.getenv("GOOGLE_PLAY_CLAIM_ENABLED", "").strip().lower() != "true":
        raise HTTPException(status_code=503, detail="Contratacao indisponivel.")
    package_name = os.getenv("GOOGLE_PLAY_PACKAGE_NAME", "").strip()
    scope_key = os.getenv("GOOGLE_PLAY_SUBSCRIPTION_SCOPE_KEY", "").strip()
    config = AccessApiConfig.from_environment()
    if not package_name or not scope_key or not config.database_url:
        raise HTTPException(status_code=503, detail="Contratacao indisponivel.")
    return GooglePlaySubscriptionClaimService(
        identity_verifier=FirebaseIdentityVerifier(),
        subscription_verifier=GooglePlaySubscriptionVerifier(
            package_name=package_name,
            product_id="cryptoradar_pro_monthly",
        ),
        subscription_store=PostgreSQLGooglePlaySubscriptionStore(
            database_url=config.database_url,
            scope_key=scope_key,
        ),
        package_name=package_name,
    )


def claim_subscription(
    request: SubscriptionClaimRequest,
    authorization: str | None,
    service: GooglePlaySubscriptionClaimService | None = None,
) -> SubscriptionClaimResponse:
    token = request.purchase_token.strip()
    if not token:
        raise HTTPException(status_code=422, detail="Token de compra obrigatorio.")
    try:
        effective_service = service if service is not None else create_claim_service()
        effective_service.claim(authorization=authorization, purchase_token=token)
    except HTTPException:
        raise
    except PurchaseIdentityMismatchError:
        raise HTTPException(status_code=403, detail="Compra nao vinculada a conta.") from None
    except PurchaseNotEntitledError:
        raise HTTPException(status_code=409, detail="Assinatura sem direito de acesso.") from None
    except PurchaseTokenAlreadyClaimedError:
        raise HTTPException(status_code=409, detail="Compra indisponivel para vinculacao.") from None
    except GooglePlaySubscriptionVerificationError:
        raise HTTPException(status_code=502, detail="Nao foi possivel verificar a compra.") from None
    except Exception:
        # Do not expose tokens, database details or Google credentials.
        raise HTTPException(status_code=503, detail="Validacao temporariamente indisponivel.") from None
    return SubscriptionClaimResponse()
