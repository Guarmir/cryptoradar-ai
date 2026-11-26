from fastapi import APIRouter, Header, Response

from app.billing.subscription_status_api import (
    SubscriptionStatusResponse,
    get_subscription_status,
)

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

    @router.get(
        "/billing/google-play/status",
        response_model=SubscriptionStatusResponse,
    )
    def status_endpoint(
        response: Response,
        authorization: str | None = Header(default=None),
    ) -> SubscriptionStatusResponse:
        response.headers["Cache-Control"] = "no-store"
        return get_subscription_status(authorization)

    return router
