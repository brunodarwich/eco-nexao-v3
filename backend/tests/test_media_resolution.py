"""Tests for media resolution service and orphan cleanup dry-run job (ECO-1703)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.media_orphan_job import MediaOrphanJob
from app.models.domain import MediaAsset
from app.services.media_resolution import MediaResolutionService
from app.services.storage_service import StorageService


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def storage_service() -> StorageService:
    return StorageService(supabase_url="https://test-project.supabase.co")


def test_resolve_asset_urls_stored(storage_service: StorageService) -> None:
    asset_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    asset = MediaAsset(
        id=asset_id,
        owner_type="route",
        owner_id=owner_id,
        storage_key="editorial-media/routes/123/hero.webp",
        mime_type="image/webp",
        alt_text="Trilha na floresta",
        credit="Foto por João",
        license_code="CC-BY-4.0",
        processing_status="ready",
        media_kind="stored",
        derivatives={
            "thumb": {"storage_key": "editorial-media/routes/123/thumb.webp"},
            "card": {"storage_key": "editorial-media/routes/123/card.webp"},
            "hero": {"storage_key": "editorial-media/routes/123/hero.webp"},
        },
        sort_order=0,
    )

    resolver = MediaResolutionService(db=AsyncMock(), storage_service=storage_service)
    resolved = resolver.resolve_asset_urls(asset)

    assert resolved.id == asset_id
    assert resolved.owner_type == "route"
    assert resolved.owner_id == owner_id
    assert (
        resolved.url
        == "https://test-project.supabase.co/storage/v1/object/public/editorial-media/routes/123/hero.webp"
    )
    assert resolved.derivatives["thumb"].endswith("/thumb.webp")
    assert resolved.derivatives["card"].endswith("/card.webp")
    assert resolved.derivatives["hero"].endswith("/hero.webp")
    assert resolved.alt_text == "Trilha na floresta"
    assert resolved.credit == "Foto por João"
    assert resolved.license_code == "CC-BY-4.0"


def test_resolve_asset_urls_google_proxy(storage_service: StorageService) -> None:
    asset_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    asset = MediaAsset(
        id=asset_id,
        owner_type="actor",
        owner_id=owner_id,
        storage_key=None,
        mime_type="image/jpeg",
        alt_text="Fachada do restaurante",
        credit="Google Places",
        license_code="PROPRIETARY",
        processing_status="ready",
        media_kind="google_proxy",
        external_photo_reference="https://lh3.googleusercontent.com/p/places_photo_123",
        sort_order=1,
    )

    resolver = MediaResolutionService(db=AsyncMock(), storage_service=storage_service)
    resolved = resolver.resolve_asset_urls(asset)

    assert resolved.id == asset_id
    assert resolved.owner_type == "actor"
    assert resolved.url == "https://lh3.googleusercontent.com/p/places_photo_123"
    assert resolved.media_kind == "google_proxy"


@pytest.mark.asyncio
async def test_resolve_media_for_owner(mock_db: AsyncMock, storage_service: StorageService) -> None:
    owner_id = uuid.uuid4()
    asset1 = MediaAsset(
        id=uuid.uuid4(),
        owner_type="actor",
        owner_id=owner_id,
        storage_key="editorial-media/actors/hero.webp",
        mime_type="image/webp",
        processing_status="ready",
        media_kind="stored",
        sort_order=0,
    )
    asset2 = MediaAsset(
        id=uuid.uuid4(),
        owner_type="actor",
        owner_id=owner_id,
        storage_key="editorial-media/actors/gallery2.webp",
        mime_type="image/webp",
        processing_status="ready",
        media_kind="stored",
        sort_order=1,
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [asset1, asset2]
    mock_db.scalars.return_value = mock_scalars

    resolver = MediaResolutionService(db=mock_db, storage_service=storage_service)
    cover, gallery = await resolver.resolve_media_for_owner("actor", owner_id)

    assert cover is not None
    assert cover.id == asset1.id
    assert len(gallery) == 2
    assert gallery[0].id == asset1.id
    assert gallery[1].id == asset2.id


@pytest.mark.asyncio
async def test_batch_resolve_covers_for_owners(
    mock_db: AsyncMock, storage_service: StorageService
) -> None:
    owner_id_1 = uuid.uuid4()
    owner_id_2 = uuid.uuid4()

    asset1 = MediaAsset(
        id=uuid.uuid4(),
        owner_type="route",
        owner_id=owner_id_1,
        storage_key="editorial-media/r1/cover.webp",
        mime_type="image/webp",
        processing_status="ready",
        media_kind="stored",
        sort_order=0,
    )
    asset2 = MediaAsset(
        id=uuid.uuid4(),
        owner_type="route",
        owner_id=owner_id_2,
        storage_key="editorial-media/r2/cover.webp",
        mime_type="image/webp",
        processing_status="ready",
        media_kind="stored",
        sort_order=0,
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [asset1, asset2]
    mock_db.scalars.return_value = mock_scalars

    resolver = MediaResolutionService(db=mock_db, storage_service=storage_service)
    covers = await resolver.batch_resolve_covers_for_owners("route", [owner_id_1, owner_id_2])

    assert len(covers) == 2
    assert covers[owner_id_1].id == asset1.id
    assert covers[owner_id_2].id == asset2.id


@pytest.mark.asyncio
async def test_media_orphan_job_dry_run(mock_db: AsyncMock) -> None:
    rejected_asset = MediaAsset(
        id=uuid.uuid4(),
        owner_type="route",
        owner_id=uuid.uuid4(),
        storage_key="editorial-media/routes/rejected/main.webp",
        mime_type="image/webp",
        processing_status="rejected",
        deleted_at=None,
        derivatives={
            "thumb": {"storage_key": "editorial-media/routes/rejected/thumb.webp"}
        },
    )

    deleted_asset = MediaAsset(
        id=uuid.uuid4(),
        owner_type="actor",
        owner_id=uuid.uuid4(),
        storage_key="editorial-media/actors/deleted/main.webp",
        mime_type="image/webp",
        processing_status="ready",
        deleted_at=datetime.now(UTC),
        derivatives={},
    )

    mock_scalars_rejected = MagicMock()
    mock_scalars_rejected.all.return_value = [rejected_asset]

    mock_scalars_deleted = MagicMock()
    mock_scalars_deleted.all.return_value = [deleted_asset]

    mock_db.scalars.side_effect = [mock_scalars_rejected, mock_scalars_deleted]

    job = MediaOrphanJob(db=mock_db)
    report = await job.run_dry_run()

    assert report.is_dry_run is True
    assert report.total_assets_scanned == 2
    assert report.orphaned_assets_count == 2
    assert len(report.orphaned_storage_paths) == 3
    assert "editorial-media/routes/rejected/main.webp" in report.orphaned_storage_paths
    assert "editorial-media/routes/rejected/thumb.webp" in report.orphaned_storage_paths
    assert "editorial-media/actors/deleted/main.webp" in report.orphaned_storage_paths
