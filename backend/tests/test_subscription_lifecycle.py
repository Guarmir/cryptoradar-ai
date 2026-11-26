from datetime import datetime, timedelta, timezone
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from cryptography.fernet import Fernet

from app.billing.subscription_lifecycle import (
    ACK, PRODUCT, SubscriptionLifecycle, eligible_snapshot, retain_token,
)

NOW = datetime(2026, 11, 26, tzinfo=timezone.utc)
TOKEN = 'private-test-token'
UID = 'test-uid'
DIGEST = sha256(TOKEN.encode()).hexdigest()


def snapshot(**changes):
    values = dict(obfuscated_account_id=sha256(UID.encode()).hexdigest(),
                  product_id=PRODUCT, linked_purchase_token=None, entitled_now=True,
                  state='SUBSCRIPTION_STATE_ACTIVE', acknowledgement_state=ACK,
                  expires_at=NOW + timedelta(days=1))
    values.update(changes)
    return SimpleNamespace(**values)


def test_valid_snapshot():
    assert eligible_snapshot(snapshot(), UID, NOW)


@pytest.mark.parametrize('changes', [
    {'obfuscated_account_id': 'wrong'}, {'product_id': 'wrong'},
    {'linked_purchase_token': 'previous'}, {'entitled_now': False},
    {'state': 'SUBSCRIPTION_STATE_EXPIRED'}, {'state': 'SUBSCRIPTION_STATE_ON_HOLD'},
    {'acknowledgement_state': 'ACKNOWLEDGEMENT_STATE_PENDING'}, {'expires_at': NOW},
    {'expires_at': NOW.replace(tzinfo=None)},
])
def test_ineligible_snapshot(changes):
    assert not eligible_snapshot(snapshot(**changes), UID, NOW)


def test_retain_encrypted_only():
    cipher = Fernet(Fernet.generate_key())
    cursor = Mock()
    cursor.fetchone.return_value = (DIGEST,)
    retain_token(cursor, scope='scope', package='pkg', uid=UID, token=TOKEN, cipher=cipher)
    sql, params = cursor.execute.call_args.args
    assert params[:4] == ('scope', 'pkg', DIGEST, UID)
    assert TOKEN not in repr(params)
    assert cipher.decrypt(params[4].encode()).decode() == TOKEN
    assert 'firebase_auth_uid = EXCLUDED.firebase_auth_uid' in sql


def test_retain_wrong_owner_fails():
    cursor = Mock()
    cursor.fetchone.return_value = None
    with pytest.raises(ValueError):
        retain_token(cursor, scope='scope', package='pkg', uid=UID, token=TOKEN,
                     cipher=Fernet(Fernet.generate_key()))


def subject(*, verified=None, error=None, idle=False, wrong_hash=False, missing_subscription=False):
    cipher = Fernet(Fernet.generate_key())
    conn = Mock()
    cursor = conn.cursor.return_value = Mock()
    # Simple fake context manager (works with normal psycopg cursors).
    from unittest.mock import MagicMock
    cm = MagicMock()
    cm.__enter__.return_value = cursor
    conn.cursor.return_value = cm
    row = ('wrong' if wrong_hash else DIGEST, UID, cipher.encrypt(TOKEN.encode()).decode())
    cursor.fetchone.side_effect = [None if idle else row, None if missing_subscription else (DIGEST,)]
    verifier = Mock()
    verifier.verify.return_value = verified or snapshot()
    verifier.verify.side_effect = error
    service = SubscriptionLifecycle(database_url='fake', scope='scope', package='pkg',
        verifier=verifier, cipher=cipher, connection_factory=lambda _: conn, now_provider=lambda: NOW)
    return service, conn, cursor, verifier


def queries(cursor):
    return [call.args for call in cursor.execute.call_args_list]


def test_refresh_renews_bounded_grants():
    service, conn, cursor, verifier = subject()
    assert service.refresh_one() == 'renewed'
    verifier.verify.assert_called_once_with(TOKEN)
    calls = queries(cursor)
    assert 'SKIP LOCKED' in calls[0][0]
    assert 'verified_at=NOW()' in calls[1][0]
    assert "INTERVAL '15 minutes'" in calls[2][0]
    assert 'cryptoradar_push_installation_owners' in calls[2][0]
    assert calls[3][1][0] == 300
    assert TOKEN not in repr(calls)
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.parametrize('changes', [{'entitled_now': False}, {'state': 'SUBSCRIPTION_STATE_EXPIRED'},
                                     {'obfuscated_account_id': 'other'}])
def test_negative_decision_revokes(changes):
    service, conn, cursor, _ = subject(verified=snapshot(**changes))
    assert service.refresh_one() == 'revoked'
    assert 'LEAST(valid_until,NOW())' in queries(cursor)[1][0]
    conn.commit.assert_called_once()


def test_missing_subscription_revokes():
    service, _, cursor, _ = subject(missing_subscription=True)
    assert service.refresh_one() == 'revoked'
    assert 'LEAST(valid_until,NOW())' in queries(cursor)[2][0]


@pytest.mark.parametrize('options', [{'error': RuntimeError('network')}, {'wrong_hash': True}])
def test_failure_does_not_extend_access(options):
    service, conn, cursor, verifier = subject(**options)
    assert service.refresh_one() == 'retry'
    calls = queries(cursor)
    assert len(calls) == 2
    assert calls[1][1][0] == 60
    assert 'installation_grants' not in repr(calls)
    if options.get('wrong_hash'):
        verifier.verify.assert_not_called()
    conn.commit.assert_called_once()


def test_idle():
    service, conn, _, verifier = subject(idle=True)
    assert service.refresh_one() == 'idle'
    verifier.verify.assert_not_called()
    conn.commit.assert_called_once()


def test_db_error_rolls_back():
    service, conn, cursor, _ = subject()
    cursor.execute.side_effect = RuntimeError('database')
    with pytest.raises(RuntimeError):
        service.refresh_one()
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()


def test_batch_stops_at_idle():
    service, *_ = subject()
    service.refresh_one = Mock(side_effect=['renewed', 'retry', 'revoked', 'idle'])
    assert service.run_batch() == {'renewed': 1, 'retry': 1, 'revoked': 1}
