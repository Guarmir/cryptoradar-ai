import pytest
from fastapi import HTTPException

from app.push.firebase_identity_verifier import FirebaseIdentityVerifier


def test_accepts_valid_bearer_and_returns_server_verified_uid():
    verifier = FirebaseIdentityVerifier(token_verifier=lambda token: {"uid": "user-123"} if token == "valid" else {})
    assert verifier.verify_bearer("Bearer valid") == "user-123"


def test_accepts_case_insensitive_bearer_prefix():
    verifier = FirebaseIdentityVerifier(token_verifier=lambda _: {"sub": "user-2"})
    assert verifier.verify_bearer("bearer token") == "user-2"


@pytest.mark.parametrize("header", [None, "", "Bearer", "Basic token", "Bearer a b", "token"])
def test_rejects_missing_or_malformed_authorization(header):
    verifier = FirebaseIdentityVerifier(token_verifier=lambda _: {"uid": "x"})
    with pytest.raises(HTTPException) as error:
        verifier.verify_bearer(header)
    assert error.value.status_code == 401


def test_rejects_invalid_token():
    def fail(_):
        raise ValueError("invalid")

    verifier = FirebaseIdentityVerifier(token_verifier=fail)
    with pytest.raises(HTTPException) as error:
        verifier.verify_bearer("Bearer invalid")
    assert error.value.status_code == 401


def test_rejects_token_without_uid():
    verifier = FirebaseIdentityVerifier(token_verifier=lambda _: {"aud": "p"})
    with pytest.raises(HTTPException) as error:
        verifier.verify_bearer("Bearer valid")
    assert error.value.status_code == 401
