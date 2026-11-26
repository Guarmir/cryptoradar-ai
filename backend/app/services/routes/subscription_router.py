from fastapi import APIRouter, Header

from app.billing.subscription_api import (
    SubscriptionClaimRequest,
    SubscriptionClaimResponse,
    claim_subscription,
)


def create_subscription_router() -> APIRouter:
    router = APIRouter(tags=["billing"])

    @router.post(
        "/billing/google-play/claim",
        response_model=SubscriptionClaimResponse,
    )
    def claim_endpoint(
        request: SubscriptionClaimRequest,
        authorization: str | None = Header(default=None),
    ) -> SubscriptionClaimResponse:
        return claim_subscription(request, authorization)

    return router
