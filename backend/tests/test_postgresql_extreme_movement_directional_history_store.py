
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.early_movement.extreme_movement.postgresql_extreme_movement_directional_history_store import (
    PostgreSQLExtremeMovementDirectionalHistoryStore,
)


TIMESTAMP = datetime(
    2026, 11, 16, 12, 0, tzinfo=timezone.utc
)


def make_comparison(*, with_diagnostics=True):
    diagnostics = ()

    if with_diagnostics:
        diagnostics = (
            SimpleNamespace(
                coin_id="bitcoin",
                state="sustained",
                direction="up",
                previous_direction="unknown",
                observation_count=4,
                consecutive_moves=3,
                alternating_moves=0,
                latest_price_change_pct=1.5,
            ),
        )

    return SimpleNamespace(
        directional_continuities=diagnostics
    )


def make_store():
    connection = MagicMock()
    cursor = connection.cursor.return_value

    store = PostgreSQLExtremeMovementDirectionalHistoryStore(
        database_url="postgresql://test",
        scope_key="extreme-movement-shadow",
        connection_factory=lambda _: connection,
    )

    return store, connection, cursor


def test_salva_diagnostico_direcional():
    store, connection, cursor = make_store()

    store.save(
        make_comparison(),
        observed_at=TIMESTAMP,
    )

    cursor.execute.assert_called_once()
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()

    sql, params = cursor.execute.call_args.args

    assert (
        "cryptoradar_extreme_movement_directional_history"
        in sql
    )
    assert "ON CONFLICT" in sql
    assert "IS DISTINCT FROM" in sql
    assert "2 hours" in sql
    assert TIMESTAMP in params


def test_nao_abre_conexao_sem_diagnosticos():
    store, connection, _ = make_store()

    store.save(
        make_comparison(with_diagnostics=False),
        observed_at=TIMESTAMP,
    )

    connection.cursor.assert_not_called()
    connection.commit.assert_not_called()


def test_rejeita_horario_sem_fuso():
    store, connection, _ = make_store()

    with pytest.raises(ValueError):
        store.save(
            make_comparison(),
            observed_at=datetime(2026, 11, 16, 12, 0),
        )

    connection.cursor.assert_not_called()


def test_rollback_em_erro_de_gravacao():
    store, connection, cursor = make_store()

    cursor.execute.side_effect = RuntimeError(
        "Falha simulada no PostgreSQL"
    )

    with pytest.raises(RuntimeError):
        store.save(
            make_comparison(),
            observed_at=TIMESTAMP,
        )

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_rejeita_configuracao_invalida():
    with pytest.raises(ValueError):
        PostgreSQLExtremeMovementDirectionalHistoryStore(
            database_url="",
            scope_key="extreme-movement-shadow",
        )

    with pytest.raises(ValueError):
        PostgreSQLExtremeMovementDirectionalHistoryStore(
            database_url="postgresql://test",
            scope_key="",
        )
