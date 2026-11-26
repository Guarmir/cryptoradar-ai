from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.billing import subscription_api as api
from app.services.routes.subscription_router import create_subscription_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(create_subscription_router())
    return TestClient(app)


@pytest.fixture
def service(monkeypatch):
    service = Mock(spec=api.GooglePlaySubscriptionClaimService)
    monkeypatch.setattr(api, "create_claim_service", lambda: service)
    return service


def test_verified_without_grant(client, service):
    response = client.post("/billing/google-play/claim", json={"purchase_token": " token "}, headers={"Authorization": "Bearer firebase"})
    assert response.status_code == 200
    assert response.json() == {"status": "verified", "pro_granted": False}
    service.claim.assert_called_once_with(authorization="Bearer firebase", purchase_token="token")


@pytest.mark.parametrize("payload", [{}, {"purchase_token": ""}, {"purchase_token": "   "}])
def test_invalid_token(client, service, payload):
    assert client.post("/billing/google-play/claim", json=payload).status_code == 422
    service.claim.assert_not_called()


@pytest.mark.parametrize("error, code", [
    (HTTPException(401, "Invalid authentication", headers={"WWW-Authenticate": "Bearer"}), 401),
    (api.PurchaseIdentityMismatchError("secret"), 403),
    (api.PurchaseNotEntitledError("secret"), 409),
    (api.PurchaseTokenAlreadyClaimedError("secret"), 409),
    (api.GooglePlaySubscriptionVerificationError("secret"), 502),
    (RuntimeError("secret"), 503),
])
def test_errors(client, service, error, code):
    service.claim.side_effect = error
    response = client.post("/billing/google-play/claim", json={"purchase_token": "token"})
    assert response.status_code == code
    assert "secret" not in response.text
    if code == 401:
        assert response.headers["WWW-Authenticate"] == "Bearer"


def test_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_PLAY_CLAIM_ENABLED", raising=False)
    assert client.post("/billing/google-play/claim", json={"purchase_token": "token"}).status_code == 503
