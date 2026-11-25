"""Testes offline do armazenamento: sem banco ou compra reais."""

from datetime import datetime, timezone
from hashlib import sha256

import pytest

from app.billing.postgresql_google_play_subscription_store import (
    PostgreSQLGooglePlaySubscriptionStore,
    PurchaseTokenAlreadyClaimedError,
    StoredGooglePlaySubscription,
)


class FakeCursor:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.statements = []
        self.closed = False

    def execute(self, sql, params):
        self.statements.append((sql, params))

    def fetchone(self):
        return next(self.rows, None)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def store(connection):
    return PostgreSQLGooglePlaySubscriptionStore(
        database_url="postgresql://example", scope_key="crypto",
        connection_factory=lambda _: connection,
    )


def save(s, **overrides):
    args = dict(
        purchase_token="secret-purchase-token", firebase_auth_uid="uid-1",
        package_name="app.cryptoradar", product_id="cryptoradar_pro_monthly",
        subscription_state="SUBSCRIPTION_STATE_ACTIVE",
        acknowledgement_state="ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
        expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
    )
    args.update(overrides)
    s.save_verified(**args)


def test_save_hashes_token_and_commits():
    conn = FakeConnection([(1,)])
    save(store(conn))
    query, params = conn.cursor_instance.statements[0]
    assert params[1] == sha256(b"secret-purchase-token").hexdigest()
    assert "secret-purchase-token" not in repr(params)
    assert "RETURNING id" in query
    assert conn.commits == 1 and conn.rollbacks == 0 and conn.closed


def test_atomic_upsert_preserves_owner_and_package():
    conn = FakeConnection([(1,)])
    save(store(conn))
    sql = conn.cursor_instance.statements[0][0]
    assert "firebase_auth_uid = EXCLUDED.firebase_auth_uid" in sql
    assert "package_name = EXCLUDED.package_name" in sql
    assert "firebase_auth_uid =" not in sql.split("DO UPDATE SET", 1)[1].split("WHERE", 1)[0]


def test_existing_claim_by_other_user_rejected():
    conn = FakeConnection([None])
    with pytest.raises(PurchaseTokenAlreadyClaimedError):
        save(store(conn))
    assert conn.commits == 0 and conn.rollbacks == 1 and conn.closed


def test_read_found():
    expiry = datetime(2027, 1, 1, tzinfo=timezone.utc)
    conn = FakeConnection([("uid-1", "product", "active", "acknowledged", expiry)])
    result = store(conn).load_by_token("token")
    assert result == StoredGooglePlaySubscription("uid-1", "product", "active", "acknowledged", expiry)
    assert conn.cursor_instance.statements[0][1][1] == sha256(b"token").hexdigest()
    assert conn.closed


def test_read_missing():
    assert store(FakeConnection([None])).load_by_token("token") is None


@pytest.mark.parametrize("value", ["", "  ", None])
def test_invalid_token_fails_before_database(value):
    conn = FakeConnection([])
    with pytest.raises(ValueError):
        save(store(conn), purchase_token=value)
    assert not conn.closed


def test_naive_expiry_rejected():
    conn = FakeConnection([])
    with pytest.raises(ValueError, match="fuso"):
        save(store(conn), expires_at=datetime(2027, 1, 1))
    assert not conn.closed


def test_expiry_normalized_to_utc():
    from datetime import timedelta
    conn = FakeConnection([(1,)])
    tz = timezone(timedelta(hours=-3))
    save(store(conn), expires_at=datetime(2027, 1, 1, tzinfo=tz))
    assert conn.cursor_instance.statements[0][1][-1] == datetime(2027, 1, 1, 3, tzinfo=timezone.utc)


def test_scope_is_required():
    with pytest.raises(ValueError):
        PostgreSQLGooglePlaySubscriptionStore(database_url="db", scope_key=" ")


def test_credentials_not_in_error_on_claim():
    conn = FakeConnection([None])
    with pytest.raises(PurchaseTokenAlreadyClaimedError) as error:
        save(store(conn))
    assert "secret-purchase-token" not in str(error.value)
