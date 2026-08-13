"""Unit tests for PoiUpdateJob (ECO-0403)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.connectors.google_places import (
    GooglePlacesConnector,
    GooglePlacesError,
)
from app.ingestion.poi_update_job import (
    PoiUpdateConcurrencyError,
    PoiUpdateJob,
    PoiUpdateJobReport,
)
from app.models.domain import (
    Actor,
    ActorExternalRef,
    ExternalSource,
    IngestionRun,
    RawSourceRecord,
)


@pytest.fixture
def mock_session() -> MagicMock:
    """Build a mock SQLAlchemy session tracking added objects."""
    session = MagicMock()
    added_objects: list[object] = []

    def fake_add(obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            object.__setattr__(obj, "id", uuid.uuid4())
        added_objects.append(obj)

    session.add.side_effect = fake_add
    session.added_objects = added_objects
    return session


@pytest.fixture
def mock_places_connector() -> AsyncMock:
    """Build a mock Places connector."""
    connector = AsyncMock(spec=GooglePlacesConnector)
    connector.place_details.return_value = {
        "id": "place-123",
        "nationalPhoneNumber": "(93) 99999-0001",
        "websiteUri": "https://pousadadopindobal.com.br",
        "rating": 4.8,
        "userRatingCount": 120,
        "regularOpeningHours": {"openNow": True},
    }
    return connector


def test_poi_update_job_validation(mock_session: MagicMock) -> None:
    """Reject invalid initialization parameters."""
    mock_connector = MagicMock(spec=GooglePlacesConnector)
    with pytest.raises(ValueError, match="max_cost_limit"):
        PoiUpdateJob(mock_session, mock_connector, max_cost_limit=-1.0)

    with pytest.raises(ValueError, match="cost_per_request"):
        PoiUpdateJob(mock_session, mock_connector, cost_per_request=-0.01)

    with pytest.raises(ValueError, match="request_timeout_s"):
        PoiUpdateJob(mock_session, mock_connector, request_timeout_s=0)


@pytest.mark.asyncio
async def test_poi_update_job_concurrency_lock(
    mock_session: MagicMock,
    mock_places_connector: AsyncMock,
) -> None:
    """Prevent concurrent execution of POI update job via memory lock."""
    # Ensure lock is clean
    PoiUpdateJob.ingestion_runs.clear()

    source = ExternalSource(id=uuid.uuid4(), slug="google_places", name="Google Places")
    mock_execute = MagicMock()
    mock_execute.scalar_one_or_none.return_value = source
    mock_execute.all.return_value = []
    mock_session.execute.return_value = mock_execute

    job1 = PoiUpdateJob(mock_session, mock_places_connector)
    job2 = PoiUpdateJob(mock_session, mock_places_connector)

    PoiUpdateJob.ingestion_runs.add("poi_update_job")

    with pytest.raises(PoiUpdateConcurrencyError, match="already running"):
        await job2.run()

    # Clear lock and verify successful single run releases lock
    PoiUpdateJob.ingestion_runs.clear()
    report = await job1.run()

    assert isinstance(report, PoiUpdateJobReport)
    assert report.status == "completed"
    assert "poi_update_job" not in PoiUpdateJob.ingestion_runs


@pytest.mark.asyncio
async def test_poi_update_job_updates_pois_and_creates_records(
    mock_session: MagicMock,
    mock_places_connector: AsyncMock,
) -> None:
    """Successfully update POIs, refresh Actor fields and store RawSourceRecord."""
    PoiUpdateJob.ingestion_runs.clear()

    source_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    source = ExternalSource(id=source_id, slug="google_places", name="Google Places")

    actor = Actor(
        id=actor_id,
        slug="pousada-pindobal",
        name="Pousada Pindobal",
        category_id=uuid.uuid4(),
        phone=None,
        website=None,
        google_rating=None,
        google_review_count=None,
    )
    ref = ActorExternalRef(
        id=uuid.uuid4(),
        actor_id=actor_id,
        source_id=source_id,
        external_id="places-chkey-1",
        last_seen_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    # First scalar_one_or_none returns source, subsequent all returns POI query results
    exec_result_source = MagicMock()
    exec_result_source.scalar_one_or_none.return_value = source

    exec_result_pois = MagicMock()
    exec_result_pois.all.return_value = [(ref, actor)]

    mock_session.execute.side_effect = [exec_result_source, exec_result_pois]

    job = PoiUpdateJob(mock_session, mock_places_connector, cost_per_request=0.017)
    report = await job.run()

    assert report.status == "completed"
    assert report.updated_count == 1
    assert report.total_scanned == 1
    assert report.failed_count == 0
    assert report.total_cost == 0.017

    assert actor.phone == "(93) 99999-0001"
    assert actor.website == "https://pousadadopindobal.com.br"
    assert actor.google_rating == 4.8
    assert actor.google_review_count == 120
    assert actor.google_data_refreshed_at is not None

    raw_records = [o for o in mock_session.added_objects if isinstance(o, RawSourceRecord)]
    assert len(raw_records) == 1
    assert raw_records[0].external_id == "places-chkey-1"
    assert raw_records[0].payload["rating"] == 4.8


@pytest.mark.asyncio
async def test_poi_update_job_respects_max_cost_limit(
    mock_session: MagicMock,
    mock_places_connector: AsyncMock,
) -> None:
    """Stop execution early when maximum cost limit would be exceeded."""
    PoiUpdateJob.ingestion_runs.clear()

    source_id = uuid.uuid4()
    source = ExternalSource(id=source_id, slug="google_places", name="Google Places")

    items = []
    for i in range(3):
        act = Actor(
            id=uuid.uuid4(),
            slug=f"poi-{i}",
            name=f"POI {i}",
            category_id=uuid.uuid4(),
        )
        r = ActorExternalRef(
            id=uuid.uuid4(),
            actor_id=act.id,
            source_id=source_id,
            external_id=f"place-{i}",
        )
        items.append((r, act))

    exec_source = MagicMock()
    exec_source.scalar_one_or_none.return_value = source

    exec_pois = MagicMock()
    exec_pois.all.return_value = items

    mock_session.execute.side_effect = [exec_source, exec_pois]

    # Limit set to 0.02, cost per call is 0.017 -> Only 1 call allowed
    job = PoiUpdateJob(
        mock_session,
        mock_places_connector,
        max_cost_limit=0.02,
        cost_per_request=0.017,
    )
    report = await job.run()

    assert report.status == "partial"
    assert report.updated_count == 1
    assert report.skipped_count == 2
    assert report.total_cost == 0.017
    assert mock_places_connector.place_details.call_count == 1


@pytest.mark.asyncio
async def test_poi_update_job_handles_partial_failures_and_resumption(
    mock_session: MagicMock,
    mock_places_connector: AsyncMock,
) -> None:
    """Resiliently handle upstream API failures per item without failing entire batch."""
    PoiUpdateJob.ingestion_runs.clear()

    source_id = uuid.uuid4()
    source = ExternalSource(id=source_id, slug="google_places", name="Google Places")

    actor1 = Actor(id=uuid.uuid4(), slug="p1", name="POI 1", category_id=uuid.uuid4())
    ref1 = ActorExternalRef(
        id=uuid.uuid4(), actor_id=actor1.id, source_id=source_id, external_id="bad-place"
    )

    actor2 = Actor(id=uuid.uuid4(), slug="p2", name="POI 2", category_id=uuid.uuid4())
    ref2 = ActorExternalRef(
        id=uuid.uuid4(), actor_id=actor2.id, source_id=source_id, external_id="good-place"
    )

    exec_source = MagicMock()
    exec_source.scalar_one_or_none.return_value = source

    exec_pois = MagicMock()
    exec_pois.all.return_value = [(ref1, actor1), (ref2, actor2)]

    mock_session.execute.side_effect = [exec_source, exec_pois]

    # Mock place_details to fail on bad-place and succeed on good-place
    async def fake_place_details(place_id: str, fields: tuple[str, ...]) -> dict[str, object]:
        if place_id == "bad-place":
            raise GooglePlacesError("Upstream failure")
        return {"id": "good-place", "rating": 4.5}

    mock_places_connector.place_details.side_effect = fake_place_details

    job = PoiUpdateJob(mock_session, mock_places_connector, cost_per_request=0.01)
    report = await job.run()

    assert report.status == "completed"
    assert report.total_scanned == 2
    assert report.updated_count == 1
    assert report.failed_count == 1
    assert report.total_cost == 0.01

    ingestion_runs = [o for o in mock_session.added_objects if isinstance(o, IngestionRun)]
    assert len(ingestion_runs) == 1
    assert ingestion_runs[0].stats["failed"] == 1
    assert ingestion_runs[0].stats["updated"] == 1
