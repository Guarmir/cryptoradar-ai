
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.early_movement.extreme_movement.extreme_movement_experimental_tracking import (
    ExtremeMovementExperimentalTrackingEvaluator,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_experimental_tracking_store import (
    PostgreSQLExtremeMovementExperimentalTrackingStore,
)


BASE_TIME = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def evaluator():
    return ExtremeMovementExperimentalTrackingEvaluator()


@pytest.fixture
def tracking(evaluator):
    return evaluator.start(
        coin_id="irys",
        observed_at=BASE_TIME,
        price=1.0,
        direction="up",
        score=65.0,
        evidence_count=3,
        state="priority",
    )


@pytest.fixture
def database():
    connection = MagicMock()
    cursor = connection.cursor.return_value
    cursor.fetchone.return_value = (42,)
    return connection, cursor


@pytest.fixture
def store(database):
    connection, _ = database
    return PostgreSQLExtremeMovementExperimentalTrackingStore(
        database_url="postgresql://test",
        scope_key="extreme-movement-shadow",
        connection_factory=lambda _: connection,
    )


def test_save_start_creates_tracking_and_history(
    store, database, tracking
):
    connection, cursor = database

    tracking_id = store.save_start(tracking)

    assert tracking_id == 42
    assert cursor.execute.call_count == 2
    assert "INSERT INTO" in cursor.execute.call_args_list[0].args[0]
    assert "RETURNING id" in cursor.execute.call_args_list[0].args[0]
    assert "experimental_price_history" in (
        cursor.execute.call_args_list[1].args[0]
    )
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_save_update_records_new_observation(
    store, database, evaluator, tracking
):
    connection, cursor = database

    updated = evaluator.update(
        tracking,
        observed_at=BASE_TIME + timedelta(minutes=20),
        price=1.05,
        direction="up",
        score=80.0,
        evidence_count=3,
        state="priority",
    )

    store.save_update(
        42,
        updated,
        is_selected=False,
    )

    assert cursor.execute.call_count == 2
    assert "UPDATE" in cursor.execute.call_args_list[0].args[0]
    assert "experimental_price_history" in (
        cursor.execute.call_args_list[1].args[0]
    )
    assert cursor.execute.call_args_list[1].args[1][-1] is False
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()


def test_save_close_marks_tracking_closed(
    store, database, evaluator, tracking
):
    connection, cursor = database

    closed = evaluator.close(
        tracking,
        closed_at=BASE_TIME + timedelta(minutes=60),
        reason="movement_invalidated",
    )

    store.save_close(42, closed)

    assert cursor.execute.call_count == 1
    assert "status = 'closed'" in cursor.execute.call_args.args[0]
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()


def test_save_start_rolls_back_on_database_error(
    store, database, tracking
):
    connection, cursor = database
    cursor.execute.side_effect = RuntimeError("database failure")

    with pytest.raises(RuntimeError, match="database failure"):
        store.save_start(tracking)

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_save_update_rejects_missing_tracking(
    store, database, evaluator, tracking
):
    connection, cursor = database
    cursor.fetchone.return_value = None

    updated = evaluator.update(
        tracking,
        observed_at=BASE_TIME + timedelta(minutes=20),
        price=1.05,
        direction="up",
        score=80.0,
        evidence_count=3,
        state="priority",
    )

    with pytest.raises(ValueError, match="duplicada"):
        store.save_update(
            42,
            updated,
            is_selected=True,
        )

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_save_close_rejects_missing_tracking(
    store, database, evaluator, tracking
):
    connection, cursor = database
    cursor.fetchone.return_value = None

    closed = evaluator.close(
        tracking,
        closed_at=BASE_TIME + timedelta(minutes=60),
        reason="movement_invalidated",
    )

    with pytest.raises(ValueError, match="nao encontrado"):
        store.save_close(42, closed)

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_store_validates_configuration():
    with pytest.raises(ValueError, match="URL"):
        PostgreSQLExtremeMovementExperimentalTrackingStore(
            database_url=" ",
            scope_key="test",
        )

    with pytest.raises(ValueError, match="Escopo"):
        PostgreSQLExtremeMovementExperimentalTrackingStore(
            database_url="postgresql://test",
            scope_key=" ",
        )

        
def test_load_active_recovers_tracking(store, database):
    connection, cursor = database

    cursor.fetchall.return_value = [
        (
            42,
            "irys",
            BASE_TIME,
            BASE_TIME + timedelta(minutes=20),
            1.0,
            1.05,
            "up",
            "up",
            65.0,
            80.0,
            3,
            3,
            "priority",
            2,
            1.05,
            1.0,
            "active",
            None,
            None,
        )
    ]

    results = store.load_active()

    assert len(results) == 1

    tracking_id, tracking = results[0]

    assert tracking_id == 42
    assert tracking.coin_id == "irys"
    assert tracking.initial_price == 1.0
    assert tracking.latest_price == 1.05
    assert tracking.observation_count == 2
    assert tracking.price_change_pct == pytest.approx(5.0)
    assert tracking.status == "active"

    sql = cursor.execute.call_args.args[0]
    params = cursor.execute.call_args.args[1]

    assert "status = 'active'" in sql
    assert params == ("extreme-movement-shadow",)

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_load_active_returns_empty_when_no_tracking(
    store, database
):
    connection, cursor = database
    cursor.fetchall.return_value = []

    assert store.load_active() == ()

    connection.commit.assert_called_once()
    connection.close.assert_called_once()


def test_load_active_rolls_back_on_database_error(
    store, database
):
    connection, cursor = database
    cursor.execute.side_effect = RuntimeError(
        "database unavailable"
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        store.load_active()

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()

    
def test_save_batch_creates_multiple_trackings(
    store, database, evaluator
):
    connection, cursor = database

    first = evaluator.start(
        coin_id="irys",
        observed_at=BASE_TIME,
        price=1.0,
        direction="up",
        score=65.0,
        evidence_count=3,
        state="priority",
    )

    second = evaluator.start(
        coin_id="bitcoin",
        observed_at=BASE_TIME,
        price=70000.0,
        direction="up",
        score=70.0,
        evidence_count=3,
        state="priority",
    )

    cursor.fetchone.side_effect = [(42,), (43,)]

    result = store.save_batch(starts=(first, second))

    assert result == (42, 43)
    assert cursor.execute.call_count == 4
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_save_batch_updates_multiple_trackings(
    store, database, evaluator
):
    connection, cursor = database

    first = evaluator.start(
        coin_id="irys",
        observed_at=BASE_TIME,
        price=1.0,
        direction="up",
        score=65.0,
        evidence_count=3,
        state="priority",
    )

    second = evaluator.start(
        coin_id="bitcoin",
        observed_at=BASE_TIME,
        price=70000.0,
        direction="up",
        score=70.0,
        evidence_count=3,
        state="priority",
    )

    first_updated = evaluator.update(
        first,
        observed_at=BASE_TIME + timedelta(minutes=20),
        price=1.05,
        direction="up",
        score=80.0,
        evidence_count=3,
        state="priority",
    )

    second_updated = evaluator.update(
        second,
        observed_at=BASE_TIME + timedelta(minutes=20),
        price=71000.0,
        direction="up",
        score=75.0,
        evidence_count=3,
        state="priority",
    )

    cursor.fetchone.side_effect = [(42,), (43,)]

    result = store.save_batch(
        updates=(
            (42, first_updated, True),
            (43, second_updated, False),
        )
    )

    assert result == ()
    assert cursor.execute.call_count == 4
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()

    history_calls = [
        call
        for call in cursor.execute.call_args_list
        if "INSERT INTO" in call.args[0]
        and store.HISTORY_TABLE in call.args[0]
    ]

    assert len(history_calls) == 2
    assert history_calls[0].args[1][-1] is True
    assert history_calls[1].args[1][-1] is False


def test_save_batch_rolls_back_entire_transaction(
    store, database, evaluator
):
    connection, cursor = database

    first = evaluator.start(
        coin_id="irys",
        observed_at=BASE_TIME,
        price=1.0,
        direction="up",
        score=65.0,
        evidence_count=3,
        state="priority",
    )

    second = evaluator.start(
        coin_id="bitcoin",
        observed_at=BASE_TIME,
        price=70000.0,
        direction="up",
        score=70.0,
        evidence_count=3,
        state="priority",
    )

    cursor.fetchone.side_effect = [(42,), None]

    with pytest.raises(ValueError, match="ID retornado"):
        store.save_batch(starts=(first, second))

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_save_batch_empty_does_not_connect(store, database):
    connection, _ = database

    assert store.save_batch() == ()

    connection.cursor.assert_not_called()
    connection.commit.assert_not_called()




def test_save_batch_closes_tracking(store, database, evaluator, tracking):
    connection, cursor = database
    closed = evaluator.close(
        tracking,
        closed_at=BASE_TIME + timedelta(hours=24),
        reason="observation_window_completed",
    )

    assert store.save_batch(closes=((42, closed),)) == ()
    assert cursor.execute.call_count == 1
    sql, params = cursor.execute.call_args.args
    assert "status = 'closed'" in sql
    assert "RETURNING id" in sql
    assert params[0] == closed.closed_at
    assert params[1] == "observation_window_completed"
    assert params[2] == 42
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_save_batch_combines_start_update_and_close(
    store, database, evaluator, tracking
):
    connection, cursor = database
    new_tracking = evaluator.start(
        coin_id="new-coin",
        observed_at=BASE_TIME,
        price=2.0,
        direction="up",
        score=70.0,
        evidence_count=2,
        state="priority",
    )
    updated = evaluator.update(
        tracking,
        observed_at=BASE_TIME + timedelta(minutes=20),
        price=1.05,
        direction="up",
        score=75.0,
        evidence_count=3,
        state="priority",
    )
    closed = evaluator.close(
        tracking,
        closed_at=BASE_TIME + timedelta(hours=24),
        reason="observation_window_completed",
    )
    cursor.fetchone.side_effect = [(43,), (42,), (42,)]

    result = store.save_batch(
        starts=(new_tracking,),
        updates=((42, updated, False),),
        closes=((42, closed),),
    )

    assert result == (43,)
    assert cursor.execute.call_count == 5
    sql_statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert "INSERT INTO" in sql_statements[0]
    assert store.HISTORY_TABLE in sql_statements[1]
    assert "UPDATE" in sql_statements[2]
    assert store.HISTORY_TABLE in sql_statements[3]
    assert "status = 'closed'" in sql_statements[4]
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()


def test_save_batch_rolls_back_when_close_is_missing(
    store, database, evaluator, tracking
):
    connection, cursor = database
    closed = evaluator.close(
        tracking,
        closed_at=BASE_TIME + timedelta(hours=24),
        reason="observation_window_completed",
    )
    cursor.fetchone.side_effect = [(43,), None]

    with pytest.raises(ValueError, match="Acompanhamento ausente"):
        store.save_batch(starts=(tracking,), closes=((42, closed),))

    assert cursor.execute.call_count == 3
    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_save_batch_rejects_active_close_without_connection(
    store, database, tracking
):
    connection, _ = database

    with pytest.raises(ValueError):
        store.save_batch(closes=((42, tracking),))

    connection.cursor.assert_not_called()
    connection.commit.assert_not_called()
