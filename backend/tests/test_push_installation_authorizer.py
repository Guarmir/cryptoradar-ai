from dataclasses import dataclass

import pytest
from fastapi import HTTPException

from app.push.firebase_identity_verifier import FirebaseIdentityVerifier
from app.push.postgresql_push_installation_owner_store import (
    PostgreSQLPushInstallationOwnerStore,
)
from app.push.push_installation_authorizer import PushInstallationAuthorizer


@dataclass
class _OwnerStore:
    owners: dict[str, str]

    def load_owner_uid(self, installation_id: str) -> str | None:
        return self.owners.get(installation_id)


def _authorizer(owners=None):
    return PushInstallationAuthorizer(
        identity_verifier=FirebaseIdentityVerifier(
            token_verifier=lambda token: {"uid": token}
        ),
        owner_store=_OwnerStore(owners or {}),
    )


def test_same_uid_and_bound_installation_is_authorized():
    assert _authorizer({"phone": "uid-1"}).authorize(
        authorization="Bearer uid-1", installation_id=" phone "
    ) == "uid-1"


def test_other_uid_cannot_access_bound_installation():
    with pytest.raises(HTTPException) as error:
        _authorizer({"phone": "uid-1"}).authorize(
            authorization="Bearer uid-2", installation_id="phone"
        )
    assert error.value.status_code == 403


def test_unbound_legacy_installation_is_not_claimed():
    with pytest.raises(HTTPException) as error:
        _authorizer().authorize(
            authorization="Bearer uid-1", installation_id="old-phone"
        )
    assert error.value.status_code == 403


def test_missing_token_is_rejected():
    with pytest.raises(HTTPException) as error:
        _authorizer({"phone": "uid-1"}).authorize(
            authorization=None, installation_id="phone"
        )
    assert error.value.status_code == 401


def test_blank_installation_is_rejected():
    with pytest.raises(HTTPException) as error:
        _authorizer().authorize(
            authorization="Bearer uid-1", installation_id="   "
        )
    assert error.value.status_code == 422


class _FakeCursor:
    def __init__(self, row):
        self.row = row
        self.statement = None
        self.parameters = None
        self.closed = False

    def execute(self, statement, parameters):
        self.statement = statement
        self.parameters = parameters

    def fetchone(self):
        return self.row

    def close(self):
        self.closed = True


class _FakeConnection:
    def __init__(self, row):
        self.fake_cursor = _FakeCursor(row)
        self.closed = False

    def cursor(self):
        return self.fake_cursor

    def close(self):
        self.closed = True


@pytest.mark.parametrize("row,expected", [(None, None), (("uid-1",), "uid-1")])
def test_postgresql_owner_lookup_uses_scope_and_closes_resources(row, expected):
    connection = _FakeConnection(row)
    store = PostgreSQLPushInstallationOwnerStore(
        database_url="postgresql://test", scope_key="scanner",
        connection_factory=lambda url: connection,
    )
    assert store.load_owner_uid(" phone ") == expected
    assert connection.fake_cursor.parameters == ("scanner", "phone")
    assert connection.fake_cursor.closed
    assert connection.closed


def test_blank_owner_store_identity_rejected():
    store = PostgreSQLPushInstallationOwnerStore(
        database_url="postgresql://test", scope_key="scanner",
        connection_factory=lambda url: _FakeConnection(None),
    )
    with pytest.raises(ValueError):
        store.load_owner_uid("  ")
