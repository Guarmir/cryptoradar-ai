from fastapi import APIRouter, Header, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from app.billing.subscription_installation_grant import (
    GrantRequest, GrantResponse, register_installation_grant,
)


class _PrivateBillingRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request):
            try:
                return await handler(request)
            except RequestValidationError:
                return JSONResponse(status_code=422, content={"detail": "Dados invalidos."})
        return safe_handler

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

    private = APIRouter(route_class=_PrivateBillingRoute)

    @private.post("/billing/google-play/installation-grant", response_model=GrantResponse)
    def grant_endpoint(request: GrantRequest, response: Response,
                       authorization: str | None = Header(default=None)):
        response.headers["Cache-Control"] = "no-store"
        return register_installation_grant(request, authorization)

    router.include_router(private)
    return router
