import pytest

from app.access.postgresql_access_plan_store import (
    PostgreSQLAccessPlanStore,
)


class _FakeCursor:
    def __init__(
        self,
        connection,
    ):
        self._connection = connection
        self._selected_row = None
        self.rowcount = 0

    def execute(
        self,
        query,
        parameters,
    ):
        normalized_query = (
            " ".join(
                query.split()
            ).upper()
        )

        if normalized_query.startswith(
            "SELECT"
        ):
            scope_key = parameters[0]
            installation_id = parameters[1]

            plan = (
                self._connection.rows.get(
                    (
                        scope_key,
                        installation_id,
                    )
                )
            )

            if plan is None:
                self._selected_row = None
            else:
                self._selected_row = (
                    plan,
                )

            return

        if normalized_query.startswith(
            "INSERT"
        ):
            scope_key = parameters[0]
            installation_id = parameters[1]
            plan = parameters[2]

            self._connection.rows[
                (
                    scope_key,
                    installation_id,
                )
            ] = plan

            self.rowcount = 1
            return

        raise AssertionError(
            f"SQL inesperado: {query}"
        )

    def fetchone(
        self,
    ):
        return self._selected_row

    def close(
        self,
    ):
        pass


class _FakeConnection:
    def __init__(
        self,
    ):
        self.rows = {}
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def cursor(
        self,
    ):
        return _FakeCursor(
            self,
        )

    def commit(
        self,
    ):
        self.commit_count += 1

    def rollback(
        self,
    ):
        self.rollback_count += 1

    def close(
        self,
    ):
        self.close_count += 1


def _build_store(
    connection,
    *,
    scope_key="access-test",
):
    return PostgreSQLAccessPlanStore(
        database_url="postgresql://test",
        scope_key=scope_key,
        connection_factory=(
            lambda database_url: connection
        ),
    )


def test_missing_plan_returns_none():
    connection = _FakeConnection()

    store = _build_store(
        connection,
    )

    assert (
        store.load_plan(
            "device-1",
        )
        is None
    )


def test_saves_and_loads_free_plan():
    connection = _FakeConnection()

    store = _build_store(
        connection,
    )

    store.save_plan(
        installation_id="device-1",
        plan="free",
    )

    assert (
        store.load_plan(
            "device-1",
        )
        == "free"
    )

    assert connection.commit_count == 1


def test_saves_and_loads_pro_plan():
    connection = _FakeConnection()

    store = _build_store(
        connection,
    )

    store.save_plan(
        installation_id="device-1",
        plan="pro",
    )

    assert (
        store.load_plan(
            "device-1",
        )
        == "pro"
    )


def test_updating_existing_plan_replaces_previous_value():
    connection = _FakeConnection()

    store = _build_store(
        connection,
    )

    store.save_plan(
        installation_id="device-1",
        plan="free",
    )

    store.save_plan(
        installation_id="device-1",
        plan="pro",
    )

    assert (
        store.load_plan(
            "device-1",
        )
        == "pro"
    )


def test_different_scopes_are_isolated():
    connection = _FakeConnection()

    first_store = _build_store(
        connection,
        scope_key="scope-a",
    )

    second_store = _build_store(
        connection,
        scope_key="scope-b",
    )

    first_store.save_plan(
        installation_id="device-1",
        plan="pro",
    )

    assert (
        first_store.load_plan(
            "device-1",
        )
        == "pro"
    )

    assert (
        second_store.load_plan(
            "device-1",
        )
        is None
    )


def test_empty_installation_id_is_rejected_on_save():
    connection = _FakeConnection()

    store = _build_store(
        connection,
    )

    with pytest.raises(ValueError):
        store.save_plan(
            installation_id="   ",
            plan="free",
        )


def test_invalid_plan_is_rejected():
    connection = _FakeConnection()

    store = _build_store(
        connection,
    )

    with pytest.raises(ValueError):
        store.save_plan(
            installation_id="device-1",
            plan="premium",
        )


def test_constructor_requires_database_url():
    with pytest.raises(ValueError):
        PostgreSQLAccessPlanStore(
            database_url=" ",
            scope_key="access-test",
        )


def test_constructor_requires_scope_key():
    with pytest.raises(ValueError):
        PostgreSQLAccessPlanStore(
            database_url="postgresql://test",
            scope_key=" ",
        )