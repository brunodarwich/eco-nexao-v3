"""Transactional acceptance tests for ECO-1501."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from app.ingestion.osrm_importer import OSRMRouteResult
from app.ingestion.pindobal_repository import PindobalPersistenceRepository
from app.ingestion.seed_pindobal import run_seed_pindobal
from app.models.domain import IngestionRun, Region, Route, RouteGeometry, RouteOrigin


def osrm_result(code: str) -> OSRMRouteResult:
    return OSRMRouteResult(
        origin_code=code,
        origin_name=code.title(),
        points_count=2,
        start_point=(-2.4, -54.7),
        end_point=(-2.5, -54.9),
        distance_m=1000,
        wkt_linestring="LINESTRING(-54.7 -2.4, -54.9 -2.5)",
        wkt_start_point="POINT(-54.7 -2.4)",
        bounds={"min_lat": -2.5, "max_lat": -2.4, "min_lon": -54.9, "max_lon": -54.7},
        points=[],
        is_valid=True,
    )


def fake_session() -> tuple[Mock, AsyncMock]:
    session = Mock()
    transaction = AsyncMock()
    session.begin = Mock(return_value=transaction)
    session.add_all = Mock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.scalar = AsyncMock(return_value=0)
    result = Mock()
    result.tuples.return_value = []
    result.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    return session, transaction


@pytest.mark.asyncio
async def test_persist_adds_complete_slice_inside_one_transaction() -> None:
    session, transaction = fake_session()
    repository = PindobalPersistenceRepository(session)
    repository._one = AsyncMock(return_value=None)  # type: ignore[method-assign]
    now = datetime.now(UTC)

    run_id, stats = await repository.persist(
        report={
            "manifest": {
                "valid_files": 9,
                "files": [
                    {"name": f"rota_{code}_OSRM_01.csv", "sha256": "a" * 64}
                    for code in ("porto", "aeroporto", "rodoviaria")
                ],
            }
        },
        osrm_results={code: osrm_result(code) for code in ("porto", "aeroporto", "rodoviaria")},
        started_at=now,
        finished_at=now,
    )

    assert isinstance(run_id, uuid.UUID)
    added = [call.args[0] for call in session.add.call_args_list]
    assert sum(isinstance(item, Region) for item in added) == 1
    assert sum(isinstance(item, Route) for item in added) == 1
    assert sum(isinstance(item, RouteOrigin) for item in added) == 3
    assert sum(isinstance(item, RouteGeometry) for item in added) == 3
    assert sum(isinstance(item, IngestionRun) for item in added) == 1
    assert stats["territorial"]["regions_created"] == 1
    transaction.__aenter__.assert_awaited_once()
    transaction.__aexit__.assert_awaited_once_with(None, None, None)


@pytest.mark.asyncio
async def test_induced_failure_exits_transaction_with_exception_for_rollback() -> None:
    session, transaction = fake_session()
    repository = PindobalPersistenceRepository(session)
    repository._one = AsyncMock(return_value=None)  # type: ignore[method-assign]
    now = datetime.now(UTC)

    with pytest.raises(RuntimeError, match="induzida"):
        await repository.persist(
            report={"manifest": {"valid_files": 9}},
            osrm_results={code: osrm_result(code) for code in ("porto", "aeroporto", "rodoviaria")},
            started_at=now,
            finished_at=now,
            fail_after="route",
        )

    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is RuntimeError
    assert session.add.call_count > 0
    transaction.__aexit__.assert_awaited_once()


def test_apply_path_without_explicit_async_session_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="sessão DB explícita"):
        run_seed_pindobal(dry_run=False)


def test_persistence_counts_reconcile_every_input_family() -> None:
    """The persisted report must never silently omit Google/cutout dispositions."""
    from app.ingestion.pindobal_repository import PersistenceCounts

    counts = PersistenceCounts(
        read=7,
        created=1,
        updated=1,
        unchanged=2,
        rejected=1,
        candidates=2,
    )

    assert counts.reconciles() is True


def test_apply_environment_rejects_noncanonical_test_file() -> None:
    """A file merely labelled APP_ENV=test must not select an arbitrary project."""
    from app.ingestion.seed_pindobal import apply_from_test_environment

    backend_dir = Path(__file__).resolve().parents[1]
    noncanonical_env = backend_dir / ".env"

    with pytest.raises(RuntimeError, match="canônico"):
        import asyncio

        asyncio.run(apply_from_test_environment(backend_dir, noncanonical_env))
