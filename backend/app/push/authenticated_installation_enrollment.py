"""Prepare fresh authenticated installations; no legacy ownership claims.

Internal only. Do not expose until registration, token rotation and delivery
are integrated and protected against concurrent legacy writes.
"""
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class AuthenticatedInstallation:
    installation_id: str
    firebase_auth_uid: str


class AuthenticatedInstallationEnrollment:
    def __init__(self, *, identity_verifier, store, recover_existing=False):
        self._identity = identity_verifier
        self._store = store
        self._recover_existing = recover_existing

    def enroll(self, *, authorization: str | None, fcm_token: str,
               firebase_installation_id: str | None = None) -> AuthenticatedInstallation:
        uid = self._identity.verify_bearer(authorization)
        uid = self._required(uid, 128, 'firebase_auth_uid')
        token = self._required(fcm_token, 4096, 'fcm_token')
        fid = (None if firebase_installation_id is None else
               self._required(firebase_installation_id, 200, 'firebase_installation_id'))
        # Never accept a client-selected installation ID or transfer an old one.
        installation_id = str(uuid4())
        if self._recover_existing:
            installation_id = self._store.recover_or_create_owned_device(
                installation_id=installation_id, firebase_auth_uid=uid,
                fcm_token=token, firebase_installation_id=fid)
            return AuthenticatedInstallation(installation_id, uid)
        self._store.create_owned_device(installation_id=installation_id,
                                        firebase_auth_uid=uid, fcm_token=token,
                                        firebase_installation_id=fid)
        return AuthenticatedInstallation(installation_id, uid)

    @staticmethod
    def _required(value, maximum, name):
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise ValueError(f'{name} invalido')
        return value.strip()
