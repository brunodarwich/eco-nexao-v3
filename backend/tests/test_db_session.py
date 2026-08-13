"""Unit tests for database session lifecycle and readiness probes."""

from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.db.session import check_database_readiness, get_db


def _session_context(session: AsyncMock) -> MagicMock:
    """Build the async context manager returned by the session factory."""
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


@pytest.mark.asyncio
async def test_get_db_commits_after_successful_request() -> None:
    """A consumed dependency commits once and never rolls back."""
    session = AsyncMock()
    context = _session_context(session)

    with patch("app.db.session.AsyncSessionLocal", return_value=context):
        dependency = get_db()
        yielded_session = await anext(dependency)

        assert yielded_session is session
        with pytest.raises(StopAsyncIteration):
            await anext(dependency)

    session.commit.assert_awaited_once_with()
    session.rollback.assert_not_awaited()
    context.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.asyncio
async def test_get_db_rolls_back_and_preserves_request_exception() -> None:
    """An exception injected by the caller is rolled back and re-raised unchanged."""
    session = AsyncMock()
    context = _session_context(session)
    request_error = RuntimeError("request failed")

    with patch("app.db.session.AsyncSessionLocal", return_value=context):
        dependency = get_db()
        await anext(dependency)

        with pytest.raises(RuntimeError) as raised:
            await dependency.athrow(request_error)

    assert raised.value is request_error
    session.rollback.assert_awaited_once_with()
    session.commit.assert_not_awaited()
    context.__aexit__.assert_awaited_once()


def _connection_context(connection: AsyncMock) -> MagicMock:
    """Build the async context manager returned by the engine connection factory."""
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=connection)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


@pytest.mark.asyncio
@pytest.mark.parametrize(("postgis_installed", "expected"), [(True, True), (False, False)])
async def test_database_readiness_requires_postgres_and_postgis(
    postgis_installed: bool,
    expected: bool,
) -> None:
    """Readiness succeeds only when both SQL probes execute and PostGIS exists."""
    connection = AsyncMock()
    postgis_result = MagicMock()
    postgis_result.scalar_one.return_value = postgis_installed
    connection.execute.side_effect = [MagicMock(), postgis_result]
    context = _connection_context(connection)
    fake_engine = MagicMock()
    fake_engine.connect.return_value = context

    with patch("app.db.session.engine", fake_engine):
        assert await check_database_readiness() is expected

    fake_engine.connect.assert_called_once_with()
    assert connection.execute.await_count == 2
    executed_sql = [str(item.args[0]) for item in connection.execute.await_args_list]
    assert executed_sql == [
        "select 1",
        "select exists(select 1 from pg_extension where extname = 'postgis')",
    ]
    postgis_result.scalar_one.assert_called_once_with()
    context.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.asyncio
async def test_database_readiness_returns_false_for_sqlalchemy_errors() -> None:
    """A database/driver failure is converted to a safe negative readiness result."""
    connection = AsyncMock()
    database_error = OperationalError("select 1", {}, Exception("connection secret"))
    connection.execute.side_effect = database_error
    context = _connection_context(connection)
    fake_engine = MagicMock()
    fake_engine.connect.return_value = context

    with patch("app.db.session.engine", fake_engine):
        assert await check_database_readiness() is False

    fake_engine.connect.assert_called_once_with()
    connection.execute.assert_awaited_once()
    context.__aexit__.assert_has_awaits([call(database_error.__class__, database_error, ANY)])
