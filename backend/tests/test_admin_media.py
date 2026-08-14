"""Test suite for ECO-1702 Admin Media processing and cleanup recovery endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.security import AuthenticatedUser, get_current_user
from app.main import app
from app.models.domain import MediaAsset
from app.services.dependencies import (
    get_editorial_authorization_service,
    get_media_lifecycle_service,
)
from app.services.media_lifecycle import (
    MediaLifecycleFailure,
    MediaLifecycleService,
)


def authenticated_user(*, anonymous: bool = False) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=uuid.uuid4(),
        email="editor@econexao.org",
        is_anonymous=anonymous,
        role="authenticated",
        claims={},
    )


def mock_media_asset(
    asset_id: uuid.UUID | None = None,
    owner_type: str = "route",
    owner_id: uuid.UUID | None = None,
) -> MediaAsset:
    sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    return MediaAsset(
        id=asset_id or uuid.uuid4(),
        owner_type=owner_type,
        owner_id=owner_id or uuid.uuid4(),
        mime_type="image/webp",
        alt_text="Imagem de teste",
        credit="Foto por SEMTUR",
        license_code="CC-BY-4.0",
        media_kind="stored",
        processing_status="ready",
        storage_key="media/test/hero.webp",
        checksum_sha256=sha,
        width_px=1200,
        height_px=800,
        sort_order=0,
        derivatives={
            "hero": {
                "storage_key": "media/test/hero.webp",
                "width_px": 1200,
                "height_px": 800,
                "checksum_sha256": sha,
            }
        },
        processed_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_lifecycle_service() -> AsyncMock:
    service = AsyncMock(spec=MediaLifecycleService)
    return service


@pytest.fixture
def mock_auth_service() -> AsyncMock:
    service = AsyncMock()
    return service


def test_admin_media_process_anonymous_user_returns_403(
    mock_lifecycle_service: AsyncMock,
    mock_auth_service: AsyncMock,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: authenticated_user(anonymous=True)
    app.dependency_overrides[get_media_lifecycle_service] = lambda: mock_lifecycle_service
    app.dependency_overrides[get_editorial_authorization_service] = lambda: mock_auth_service

    client = TestClient(app)
    try:
        response = client.post(
            "/api/v1/admin/media/process",
            data={
                "owner_type": "route",
                "owner_id": str(uuid.uuid4()),
                "alt_text": "Alt text test",
                "credit": "SEMTUR",
                "license_code": "CC-BY-4.0",
            },
            files={"image": ("test.webp", b"fake_image_bytes", "image/webp")},
        )
        assert response.status_code == 403
        assert "não possui acesso editorial" in response.json()["error"]["message"]
    finally:
        app.dependency_overrides.clear()


def test_admin_media_process_value_error_returns_422(
    mock_lifecycle_service: AsyncMock,
    mock_auth_service: AsyncMock,
) -> None:
    user = authenticated_user()
    err_msg = "Proprietário não encontrado."
    mock_lifecycle_service.process_editorial_image.side_effect = ValueError(err_msg)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_media_lifecycle_service] = lambda: mock_lifecycle_service
    app.dependency_overrides[get_editorial_authorization_service] = lambda: mock_auth_service

    client = TestClient(app)
    try:
        response = client.post(
            "/api/v1/admin/media/process",
            data={
                "owner_type": "route",
                "owner_id": str(uuid.uuid4()),
                "alt_text": "Alt text test",
                "credit": "SEMTUR",
                "license_code": "CC-BY-4.0",
            },
            files={"image": ("test.webp", b"fake_image_bytes", "image/webp")},
        )
        assert response.status_code == 422
        assert "Proprietário não encontrado" in response.json()["error"]["message"]
    finally:
        app.dependency_overrides.clear()


def test_admin_media_process_lifecycle_failure_returns_422(
    mock_lifecycle_service: AsyncMock,
    mock_auth_service: AsyncMock,
) -> None:
    user = authenticated_user()
    asset_id = uuid.uuid4()
    mock_lifecycle_service.process_editorial_image.side_effect = MediaLifecycleFailure(
        "Formato corrompido", asset_id=asset_id
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_media_lifecycle_service] = lambda: mock_lifecycle_service
    app.dependency_overrides[get_editorial_authorization_service] = lambda: mock_auth_service

    client = TestClient(app)
    try:
        response = client.post(
            "/api/v1/admin/media/process",
            data={
                "owner_type": "route",
                "owner_id": str(uuid.uuid4()),
                "alt_text": "Alt text test",
                "credit": "SEMTUR",
                "license_code": "CC-BY-4.0",
            },
            files={"image": ("test.webp", b"fake_image_bytes", "image/webp")},
        )
        assert response.status_code == 422
        assert f"Mídia rejeitada ({asset_id})" in response.json()["error"]["message"]
    finally:
        app.dependency_overrides.clear()


def test_admin_media_process_success_returns_201(
    mock_lifecycle_service: AsyncMock,
    mock_auth_service: AsyncMock,
) -> None:
    user = authenticated_user()
    asset = mock_media_asset()
    mock_lifecycle_service.process_editorial_image.return_value = asset

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_media_lifecycle_service] = lambda: mock_lifecycle_service
    app.dependency_overrides[get_editorial_authorization_service] = lambda: mock_auth_service

    client = TestClient(app)
    try:
        response = client.post(
            "/api/v1/admin/media/process",
            data={
                "owner_type": "route",
                "owner_id": str(asset.owner_id),
                "alt_text": "Alt text test",
                "credit": "SEMTUR",
                "license_code": "CC-BY-4.0",
            },
            files={"image": ("test.webp", b"fake_bytes", "image/webp")},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["id"] == str(asset.id)
        assert body["data"]["mime_type"] == "image/webp"
        assert body["data"]["alt_text"] == "Imagem de teste"
        assert body["data"]["processing_status"] == "ready"
    finally:
        app.dependency_overrides.clear()


def test_admin_media_cleanup_recover_anonymous_returns_403(
    mock_lifecycle_service: AsyncMock,
    mock_auth_service: AsyncMock,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: authenticated_user(anonymous=True)
    app.dependency_overrides[get_media_lifecycle_service] = lambda: mock_lifecycle_service
    app.dependency_overrides[get_editorial_authorization_service] = lambda: mock_auth_service

    client = TestClient(app)
    try:
        response = client.post("/api/v1/admin/media/cleanup/recover", json={"limit": 10})
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_media_cleanup_recover_success_returns_200(
    mock_lifecycle_service: AsyncMock,
    mock_auth_service: AsyncMock,
) -> None:
    user = authenticated_user()
    mock_lifecycle_service.recover_pending_cleanup.return_value = (5, 0)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_media_lifecycle_service] = lambda: mock_lifecycle_service
    app.dependency_overrides[get_editorial_authorization_service] = lambda: mock_auth_service

    client = TestClient(app)
    try:
        response = client.post("/api/v1/admin/media/cleanup/recover", json={"limit": 20})
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["completed"] == 5
        assert body["data"]["failed"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dependency_factories_build_services() -> None:
    from app.services.dependencies import (
        get_actor_admin_service,
        get_content_service,
        get_editorial_authorization_service,
        get_media_lifecycle_service,
        get_storage_service,
        get_territorial_admin_service,
        get_territorial_service,
        get_user_service,
        get_workflow_admin_service,
    )

    mock_db = AsyncMock()
    assert get_territorial_service(mock_db) is not None
    assert get_user_service(mock_db) is not None
    assert get_storage_service() is not None
    assert get_content_service() is not None
    assert get_editorial_authorization_service(mock_db) is not None
    assert get_territorial_admin_service(mock_db) is not None
    assert get_actor_admin_service(mock_db) is not None
    assert get_workflow_admin_service(mock_db) is not None
    assert get_media_lifecycle_service(mock_db) is not None


@pytest.mark.asyncio
async def test_media_lifecycle_repository_methods() -> None:
    from app.models.domain import AuditLog
    from app.repositories.media_lifecycle import MediaLifecycleRepository

    mock_db = AsyncMock()

    # owner_exists tests
    repo = MediaLifecycleRepository(mock_db)
    mock_db.scalar.return_value = uuid.uuid4()
    assert await repo.owner_exists("route", uuid.uuid4()) is True
    assert await repo.owner_exists("origin", uuid.uuid4()) is True
    assert await repo.owner_exists("actor", uuid.uuid4()) is True
    assert await repo.owner_exists("invalid", uuid.uuid4()) is False

    # create_processing test
    asset_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    asset = await repo.create_processing(
        asset_id=asset_id,
        owner_type="route",
        owner_id=owner_id,
        mime_type="image/webp",
        alt_text="Alt",
        credit="Credit",
        license_code="CC-BY-4.0",
        actor_id=actor_id,
        request_id=None,
    )
    assert asset.id == asset_id
    assert asset.processing_status == "processing"

    # mark_ready test
    existing_asset = mock_media_asset(asset_id=asset_id, owner_id=owner_id)
    mock_db.scalar.return_value = existing_asset
    updated = await repo.mark_ready(
        asset_id=asset_id,
        storage_key="media/key.webp",
        checksum_sha256="sha",
        width_px=100,
        height_px=100,
        derivatives={"hero": {}},
        actor_id=actor_id,
        request_id=None,
    )
    assert updated.processing_status == "ready"

    # mark_rejected test
    rejected = await repo.mark_rejected(
        asset_id=asset_id,
        reason="Corrupt",
        actor_id=actor_id,
        request_id=None,
        cleanup_pending=True,
        orphan_storage_paths=["media/path.webp"],
    )
    assert rejected.processing_status == "rejected"

    # list_cleanup_pending test
    log_mock = MagicMock(spec=AuditLog)
    log_mock.resource_id = asset_id
    log_mock.changes = {
        "after": {"cleanup_pending": True, "orphan_storage_paths": ["media/path.webp"]}
    }
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [log_mock]
    mock_db.scalars.return_value = scalars_mock

    pending = await repo.list_cleanup_pending(limit=10)
    assert len(pending) == 1
    assert pending[0] == (asset_id, ["media/path.webp"])

    # cleanup_already_completed test
    completed_log = MagicMock(spec=AuditLog)
    completed_log.changes = {"after": {"cleanup_pending": False}}
    scalars_mock.all.return_value = [completed_log]
    assert await repo.cleanup_already_completed(asset_id) is True

    # mark_cleanup_completed test
    await repo.mark_cleanup_completed(
        asset_id=asset_id,
        paths=["media/path.webp"],
        actor_id=actor_id,
        request_id=None,
    )
    assert mock_db.commit.called


