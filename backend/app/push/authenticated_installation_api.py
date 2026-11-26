"""Opt-in authenticated enrollment. Does not grant PRO or migrate legacy state."""
import os
from datetime import timedelta
from hashlib import sha256
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.push.authenticated_installation_enrollment import AuthenticatedInstallationEnrollment
from app.push.fcm_possession_challenge import ChallengeRejected, FcmPossessionChallenge
from app.push.firebase_identity_verifier import FirebaseIdentityVerifier
from app.push.postgresql_authenticated_installation_store import PostgreSQLAuthenticatedInstallationStore
from app.push.postgresql_fcm_challenge_store import PostgreSQLFcmChallengeStore
from app.push.push_registration_config import PushRegistrationConfig


class DestinationRequest(BaseModel):
    fcm_token: str = Field(min_length=1, max_length=4096)
    firebase_installation_id: str | None = Field(default=None, min_length=1, max_length=200)


class ConfirmRequest(DestinationRequest):
    challenge_id: str = Field(min_length=1, max_length=128)
    proof: str = Field(min_length=1, max_length=128)


class ChallengeResponse(BaseModel):
    challenge_id: str
    expires_in_seconds: Literal[300] = 300


class EnrollmentResponse(BaseModel):
    installation_id: str
    status: Literal['registered'] = 'registered'


class EnrollmentRateLimiter:
    """Shared fixed-duration buckets; atomic across workers, including consumed challenges."""
    def __init__(self, database_url, scope_key, connection_factory=None):
        self.url = database_url
        self.scope = scope_key
        self.factory = connection_factory

    def reserve(self, *, action, uid, token):
        if action not in ('issue', 'confirm'):
            raise ValueError('Operacao invalida.')
        digest = lambda value: sha256(value.encode('utf-8')).hexdigest()
        limits = (('global', 120), ('uid:' + digest(uid), 5 if action == 'issue' else 12),
                  ('destination:' + digest(token), 3 if action == 'issue' else 12))
        if self.factory is None:
            import psycopg
            connection = psycopg.connect(self.url)
        else:
            connection = self.factory(self.url)
        try:
            cursor = connection.cursor()
            try:
                # All transactions acquire bucket locks in the same order.
                for key, limit in limits:
                    cursor.execute('''INSERT INTO cryptoradar_fcm_enrollment_limits AS current_bucket
                        (scope_key, bucket_key, window_end, attempts)
                        VALUES (%s, %s, NOW() + INTERVAL '60 seconds', 1)
                        ON CONFLICT (scope_key, bucket_key) DO UPDATE SET
                        attempts = CASE WHEN current_bucket.window_end <= NOW() THEN 1 ELSE current_bucket.attempts + 1 END,
                        window_end = CASE WHEN current_bucket.window_end <= NOW() THEN NOW() + INTERVAL '60 seconds' ELSE current_bucket.window_end END
                        WHERE current_bucket.window_end <= NOW() OR current_bucket.attempts < %s
                        RETURNING attempts''', (self.scope, action + ':' + key, limit))
                    if cursor.fetchone() is None:
                        raise HTTPException(status_code=429, detail='Muitas tentativas. Tente novamente.', headers={'Retry-After': '60'})
                # Bounded, opportunistic cleanup; skip rows used by another worker.
                cursor.execute('''DELETE FROM cryptoradar_fcm_possession_challenges
                    WHERE (scope_key, challenge_id) IN (SELECT scope_key, challenge_id
                        FROM cryptoradar_fcm_possession_challenges WHERE scope_key = %s
                        AND expires_at <= NOW() ORDER BY expires_at LIMIT 100 FOR UPDATE SKIP LOCKED)''', (self.scope,))
                cursor.execute('''DELETE FROM cryptoradar_fcm_enrollment_limits
                    WHERE (scope_key, bucket_key) IN (SELECT scope_key, bucket_key
                        FROM cryptoradar_fcm_enrollment_limits WHERE scope_key = %s
                        AND window_end < NOW() - INTERVAL '1 hour' ORDER BY window_end LIMIT 100 FOR UPDATE SKIP LOCKED)''', (self.scope,))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()


def deliver_fcm_challenge(*, fcm_token, challenge_id, proof):
    # Data-only: never display the proof in a notification or log it.
    from firebase_admin import messaging
    messaging.send(messaging.Message(token=fcm_token, data={
        'type': 'installation_possession_challenge',
        'challenge_id': challenge_id, 'proof': proof,
    }, android=messaging.AndroidConfig(ttl=timedelta(seconds=300))))


class InstallationEnrollmentFlow:
    def __init__(self, *, identity, challenge, enrollment, limiter):
        self.identity = identity
        self.challenge = challenge
        self.enrollment = enrollment
        self.limiter = limiter

    def _check(self, action, request, authorization):
        uid = self.identity.verify_bearer(authorization)
        token = request.fcm_token.strip()
        fid = request.firebase_installation_id
        if not token or (fid is not None and not fid.strip()):
            raise HTTPException(status_code=422, detail='Destino invalido.')
        self.limiter.reserve(action=action, uid=uid, token=token)
        return dict(authorization=authorization, fcm_token=token,
                    firebase_installation_id=fid.strip() if fid is not None else None)

    def issue(self, request, authorization):
        args = self._check('issue', request, authorization)
        return ChallengeResponse(challenge_id=self.challenge.issue(**args))

    def confirm(self, request, authorization):
        args = self._check('confirm', request, authorization)
        dest = self.challenge.verify(**args, challenge_id=request.challenge_id, proof=request.proof)
        # The consumed proof cannot be reused. A failed insert requires a new challenge.
        result = self.enrollment.enroll(authorization=authorization, fcm_token=dest.fcm_token,
                                       firebase_installation_id=dest.firebase_installation_id)
        return EnrollmentResponse(installation_id=result.installation_id)


def create_flow():
    if os.getenv('CRYPTORADAR_AUTHENTICATED_ENROLLMENT_ENABLED', '').strip().lower() != 'true':
        raise HTTPException(status_code=503, detail='Vinculacao indisponivel.')
    config = PushRegistrationConfig.from_environment()
    if not config.enabled or not config.database_url or not config.scope_key:
        raise HTTPException(status_code=503, detail='Vinculacao indisponivel.')
    identity = FirebaseIdentityVerifier()
    kwargs = dict(database_url=config.database_url, scope_key=config.scope_key)
    return InstallationEnrollmentFlow(identity=identity,
        challenge=FcmPossessionChallenge(identity_verifier=identity,
            store=PostgreSQLFcmChallengeStore(**kwargs), deliver=deliver_fcm_challenge),
        enrollment=AuthenticatedInstallationEnrollment(identity_verifier=identity,
            store=PostgreSQLAuthenticatedInstallationStore(**kwargs)),
        limiter=EnrollmentRateLimiter(**kwargs))


class _PrivateValidationRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request):
            try:
                return await handler(request)
            except RequestValidationError:
                # FastAPI normally echoes invalid input, which may contain proof/token.
                return JSONResponse(status_code=422, content={'detail': 'Dados invalidos.'})
        return safe_handler


def create_installation_router(flow_factory=None):
    router = APIRouter(tags=['authenticated-installation'], route_class=_PrivateValidationRoute)

    def run(action, request, authorization):
        try:
            flow = (flow_factory or create_flow)()
            return getattr(flow, action)(request, authorization)
        except HTTPException:
            raise
        except ChallengeRejected:
            raise HTTPException(status_code=409, detail='Verificacao indisponivel ou invalida.') from None
        except ValueError:
            raise HTTPException(status_code=422, detail='Dados invalidos.') from None
        except Exception:
            raise HTTPException(status_code=503, detail='Vinculacao temporariamente indisponivel.') from None

    @router.post('/push/installations/challenge', response_model=ChallengeResponse)
    def issue(request: DestinationRequest, authorization: str | None = Header(default=None)):
        return run('issue', request, authorization)

    @router.post('/push/installations/confirm', response_model=EnrollmentResponse)
    def confirm(request: ConfirmRequest, authorization: str | None = Header(default=None)):
        return run('confirm', request, authorization)

    return router
