import pytest
from app.push.fcm_possession_challenge import FcmPossessionChallenge, ChallengeRejected
from app.push.postgresql_fcm_challenge_store import PostgreSQLFcmChallengeStore
from unittest.mock import Mock


class Identity:
    def verify_bearer(self, authorization):
        if not authorization:
            raise PermissionError()
        return authorization


class Store:
    def __init__(self):
        self.rows = {}

    def create(self, *, ttl_seconds, **row):
        assert ttl_seconds == 300
        self.rows[row['challenge_id']] = row

    def consume(self, **row):
        if self.rows.get(row['challenge_id']) != row:
            return False
        del self.rows[row['challenge_id']]
        return True

    def discard(self, challenge_id):
        self.rows.pop(challenge_id, None)


@pytest.fixture
def setup():
    store = Store()
    deliver = Mock()
    service = FcmPossessionChallenge(identity_verifier=Identity(), store=store, deliver=deliver)
    cid = service.issue(authorization='uid', fcm_token='device', firebase_installation_id='fid')
    proof = deliver.call_args.kwargs['proof']
    return service, store, deliver, dict(authorization='uid', fcm_token='device', firebase_installation_id='fid', challenge_id=cid, proof=proof)


def test_success_and_replay(setup):
    service, _, _, args = setup
    assert service.verify(**args).firebase_auth_uid == 'uid'
    with pytest.raises(ChallengeRejected):
        service.verify(**args)


@pytest.mark.parametrize('field,value', [('authorization','other'), ('fcm_token','other'), ('firebase_installation_id','other'), ('proof','wrong'), ('challenge_id','wrong')])
def test_mismatch_does_not_consume(setup, field, value):
    service, _, _, args = setup
    with pytest.raises(ChallengeRejected):
        service.verify(**{**args, field:value})
    assert service.verify(**args).fcm_token == 'device'


def test_secret_not_persisted(setup):
    _, store, _, args = setup
    assert args['proof'] not in str(store.rows)
    assert 'device' not in str(store.rows)


def test_delivery_failure_discards(setup):
    service, store, deliver, _ = setup
    deliver.side_effect = RuntimeError('secret')
    with pytest.raises(ChallengeRejected, match='indisponivel'):
        service.issue(authorization='uid', fcm_token='other')
    assert len(store.rows) == 1


def test_unauthenticated(setup):
    service, _, deliver, _ = setup
    with pytest.raises(PermissionError):
        service.issue(authorization=None, fcm_token='device')
    assert deliver.call_count == 1


@pytest.mark.parametrize('result', [None, ('cid',)])
def test_atomic_consume_sql(result):
    conn = Mock()
    cursor = conn.cursor.return_value
    cursor.fetchone.return_value = result
    store = PostgreSQLFcmChallengeStore(database_url='db', scope_key='scope', connection_factory=lambda _:conn)
    assert store.consume(challenge_id='cid', uid='uid', destination_hash='dest', proof_hash='hash') is (result is not None)
    sql, params = cursor.execute.call_args.args
    assert 'DELETE' in sql and 'expires_at > NOW()' in sql and 'RETURNING' in sql
    assert params == ('scope','cid','uid','dest','hash')
    conn.commit.assert_called_once()
