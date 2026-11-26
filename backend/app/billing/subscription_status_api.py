"""Authenticated stored status, not a live Google Play entitlement."""
import os
from datetime import datetime
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel

from app.access.access_api_config import AccessApiConfig
from app.billing.subscription_status_store import SubscriptionStatusStore
from app.push.firebase_identity_verifier import FirebaseIdentityVerifier


class SubscriptionStatusResponse(BaseModel):
    status: Literal["stored_candidate", "no_stored_candidate"]
    subscription_state: str | None = None
    expires_at: datetime | None = None
    acknowledgement_state: str | None = None
    verified_at: datetime | None = None
    live_verified: Literal[False] = False
    pro_granted: Literal[False] = False


def create_status_store() -> SubscriptionStatusStore:
    if os.getenv("GOOGLE_PLAY_CLAIM_ENABLED", "").strip().lower() != "true":
        raise HTTPException(503, "Consulta de assinatura indisponivel.")
    config = AccessApiConfig.from_environment()
    return SubscriptionStatusStore(
        database_url=config.database_url or "",
        scope_key=os.getenv("GOOGLE_PLAY_SUBSCRIPTION_SCOPE_KEY", ""),
        package_name=os.getenv("GOOGLE_PLAY_PACKAGE_NAME", ""),
    )


def get_subscription_status(authorization: str | None, *,
                            identity_verifier=None, store=None) -> SubscriptionStatusResponse:
    verifier = identity_verifier if identity_verifier is not None else FirebaseIdentityVerifier()
    uid = verifier.verify_bearer(authorization)
    try:
        effective_store = store if store is not None else create_status_store()
        snapshot = effective_store.load_candidate(uid)
        if snapshot is None:
            return SubscriptionStatusResponse(status="no_stored_candidate")
        return SubscriptionStatusResponse(
            status="stored_candidate", subscription_state=snapshot.state,
            expires_at=snapshot.expires_at,
            acknowledgement_state=snapshot.acknowledgement_state,
            verified_at=snapshot.verified_at,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "Consulta de assinatura indisponivel.") from None
