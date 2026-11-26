"""Internal, single-use FCM possession challenge. No public route.

Use a shared persistent store across workers. Delivery must send the secret
only to the requested FCM destination, never in the HTTP response or logs.
"""
from dataclasses import dataclass
from hashlib import sha256
from secrets import token_urlsafe
from typing import Protocol


class ChallengeRejected(Exception):
    """Invalid, expired or already consumed challenge."""


@dataclass(frozen=True)
class VerifiedDestination:
    firebase_auth_uid: str
    fcm_token: str
    firebase_installation_id: str | None


class ChallengeStore(Protocol):
    def create(self, *, challenge_id: str, uid: str, destination_hash: str,
               proof_hash: str, ttl_seconds: int) -> None: ...
    def consume(self, *, challenge_id: str, uid: str, destination_hash: str,
                proof_hash: str) -> bool: ...
    def discard(self, challenge_id: str) -> None: ...


def _required(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError('Campo de verificacao invalido.')
    return value.strip()


def _digest(value):
    return sha256(value.encode('utf-8')).hexdigest()


def _destination_hash(token, fid):
    import json
    return _digest(json.dumps([token, fid], separators=(',', ':')))


class FcmPossessionChallenge:
    def __init__(self, *, identity_verifier, store: ChallengeStore, deliver):
        self._identity = identity_verifier
        self._store = store
        self._deliver = deliver

    def _destination(self, authorization, fcm_token, firebase_installation_id):
        uid = _required(self._identity.verify_bearer(authorization), 128)
        token = _required(fcm_token, 4096)
        fid = (None if firebase_installation_id is None else
               _required(firebase_installation_id, 200))
        return VerifiedDestination(uid, token, fid)

    def issue(self, *, authorization, fcm_token, firebase_installation_id=None):
        dest = self._destination(authorization, fcm_token, firebase_installation_id)
        challenge_id = token_urlsafe(24)
        proof = token_urlsafe(32)
        self._store.create(challenge_id=challenge_id, uid=dest.firebase_auth_uid,
                           destination_hash=_destination_hash(dest.fcm_token, dest.firebase_installation_id),
                           proof_hash=_digest(proof), ttl_seconds=300)
        try:
            self._deliver(fcm_token=dest.fcm_token, challenge_id=challenge_id, proof=proof)
        except Exception:
            self._store.discard(challenge_id)
            raise ChallengeRejected('Envio de verificacao indisponivel.') from None
        return challenge_id

    def verify(self, *, authorization, fcm_token, challenge_id, proof,
               firebase_installation_id=None):
        dest = self._destination(authorization, fcm_token, firebase_installation_id)
        if not self._store.consume(challenge_id=_required(challenge_id, 128),
                                   uid=dest.firebase_auth_uid,
                                   destination_hash=_destination_hash(dest.fcm_token, dest.firebase_installation_id),
                                   proof_hash=_digest(_required(proof, 128))):
            raise ChallengeRejected('Verificacao invalida ou expirada.')
        return dest
