from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.push.authenticated_installation_api import (
    EnrollmentRateLimiter, InstallationEnrollmentFlow, create_installation_router,
)
from app.push.authenticated_installation_enrollment import AuthenticatedInstallationEnrollment
from app.push.fcm_possession_challenge import FcmPossessionChallenge


class Identity:
    def verify_bearer(self, authorization):
        if authorization not in ('Bearer alice', 'Bearer bob'):
            raise HTTPException(401, 'Unauthorized')
        return authorization.split()[1]


class ChallengeStore:
    def __init__(self):
        self.rows = {}

    def create(self, *, ttl_seconds, **row):
        self.rows[row['challenge_id']] = row

    def consume(self, **row):
        if self.rows.get(row['challenge_id']) != row:
            return False
        del self.rows[row['challenge_id']]
        return True

    def discard(self, challenge_id):
        self.rows.pop(challenge_id, None)


ISSUE = '/push/installations/challenge'
CONFIRM = '/push/installations/confirm'
HEADERS = {'Authorization': 'Bearer alice'}
DEST = {'fcm_token': 'device', 'firebase_installation_id': 'fid'}


@pytest.fixture
def setup():
    identity = Identity()
    deliver, owned, limiter = Mock(), Mock(), Mock()
    flow = InstallationEnrollmentFlow(identity=identity,
        challenge=FcmPossessionChallenge(identity_verifier=identity, store=ChallengeStore(), deliver=deliver),
        enrollment=AuthenticatedInstallationEnrollment(identity_verifier=identity, store=owned), limiter=limiter)
    app = FastAPI()
    app.include_router(create_installation_router(lambda: flow))
    return TestClient(app), deliver, owned, limiter


def issued(setup):
    client, deliver, _, _ = setup
    response = client.post(ISSUE, json=DEST, headers=HEADERS)
    assert response.status_code == 200
    proof = deliver.call_args.kwargs['proof']
    assert proof not in response.text
    assert response.json()['expires_in_seconds'] == 300
    return dict(DEST, challenge_id=response.json()['challenge_id'], proof=proof)


def test_confirm_enrolls_once(setup):
    args = issued(setup)
    client, _, owned, _ = setup
    response = client.post(CONFIRM, json=args, headers=HEADERS)
    assert response.status_code == 200
    assert set(response.json()) == {'installation_id', 'status'}
    owned.create_owned_device.assert_called_once_with(installation_id=response.json()['installation_id'],
        firebase_auth_uid='alice', fcm_token='device', firebase_installation_id='fid')
    assert client.post(CONFIRM, json=args, headers=HEADERS).status_code == 409
    assert owned.create_owned_device.call_count == 1


@pytest.mark.parametrize('field,value', [('proof','wrong'), ('fcm_token','other'), ('firebase_installation_id','other'), ('challenge_id','wrong')])
def test_mismatch_blocks_enrollment(setup, field, value):
    args = issued(setup)
    client, _, owned, _ = setup
    assert client.post(CONFIRM, json={**args, field: value}, headers=HEADERS).status_code == 409
    owned.create_owned_device.assert_not_called()


def test_other_account_rejected(setup):
    args = issued(setup)
    client, _, owned, _ = setup
    assert client.post(CONFIRM, json=args, headers={'Authorization':'Bearer bob'}).status_code == 409
    owned.create_owned_device.assert_not_called()


def test_auth_before_rate_or_delivery(setup):
    client, deliver, owned, limiter = setup
    assert client.post(ISSUE, json=DEST).status_code == 401
    limiter.reserve.assert_not_called()
    deliver.assert_not_called()
    owned.create_owned_device.assert_not_called()


def test_rate_limit_blocks_delivery(setup):
    client, deliver, _, limiter = setup
    limiter.reserve.side_effect = HTTPException(429, 'Rate limit')
    assert client.post(ISSUE, json=DEST, headers=HEADERS).status_code == 429
    deliver.assert_not_called()


def test_delivery_failure_no_secret(setup):
    client, deliver, owned, _ = setup
    deliver.side_effect = RuntimeError('sensitive-value')
    result = client.post(ISSUE, json=DEST, headers=HEADERS)
    assert result.status_code == 409
    assert 'sensitive-value' not in result.text
    owned.create_owned_device.assert_not_called()


def test_failed_insert_requires_new_challenge(setup):
    args = issued(setup)
    client, _, owned, _ = setup
    owned.create_owned_device.side_effect = RuntimeError('database details')
    response = client.post(CONFIRM, json=args, headers=HEADERS)
    assert response.status_code == 503
    assert 'database details' not in response.text
    assert client.post(CONFIRM, json=args, headers=HEADERS).status_code == 409


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('CRYPTORADAR_AUTHENTICATED_ENROLLMENT_ENABLED', raising=False)
    app = FastAPI()
    app.include_router(create_installation_router())
    assert TestClient(app).post(ISSUE, json=DEST, headers=HEADERS).status_code == 503


def test_invalid_body_does_not_echo_secret(setup):
    client, _, _, _ = setup
    proof = 'private-' * 30
    result = client.post(CONFIRM, json={**DEST, 'challenge_id':'id', 'proof':proof}, headers=HEADERS)
    assert result.status_code == 422
    assert proof not in result.text


@pytest.mark.parametrize('blocked', [False, True])
def test_rate_store_transaction(blocked):
    conn = Mock()
    cursor = conn.cursor.return_value
    cursor.fetchone.side_effect = [(1,), None] if blocked else [(1,), (1,), (1,)]
    limiter = EnrollmentRateLimiter('db','scope', lambda _:conn)
    if blocked:
        with pytest.raises(HTTPException) as exc:
            limiter.reserve(action='issue', uid='alice', token='device')
        assert exc.value.status_code == 429
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()
    else:
        limiter.reserve(action='issue', uid='alice', token='device')
        conn.commit.assert_called_once()
        assert cursor.execute.call_count == 5
    assert 'device' not in str(cursor.execute.call_args_list)
    assert 'alice' not in str(cursor.execute.call_args_list)
