"""Tests for Supabase Storage Service and Avatar Upload endpoint (ECO-0406)."""

import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import AuthenticatedUser
from app.main import app
from app.services.storage_service import StorageService


@pytest.fixture
def storage_service() -> StorageService:
    return StorageService(supabase_url="https://test.supabase.co")


def test_storage_service_sanitize_filename(storage_service: StorageService) -> None:
    assert storage_service.sanitize_filename("../avatar picture!.png") == "avatar_picture_.png"
    assert storage_service.sanitize_filename("valid-name_123.jpg") == "valid-name_123.jpg"


def test_storage_service_validate_file_metadata_valid(storage_service: StorageService) -> None:
    for valid_mime in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        storage_service.validate_file_metadata("photo.jpg", valid_mime)


def test_storage_service_validate_file_metadata_invalid(storage_service: StorageService) -> None:
    with pytest.raises(HTTPException) as exc:
        storage_service.validate_file_metadata("file.pdf", "application/pdf")
    assert exc.value.status_code == 400
    assert "não suportado" in str(exc.value.detail)

    with pytest.raises(HTTPException) as exc:
        storage_service.validate_file_metadata("exe.bin", "application/x-executable")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_avatar_upload_url(storage_service: StorageService) -> None:
    user_id = uuid.uuid4()
    res = await storage_service.create_avatar_upload_url(user_id, "my_avatar.png", "image/png")

    assert "upload_url" in res
    assert "storage_key" in res
    assert "public_url" in res
    assert res["expires_in"] == 3600

    assert f"avatars/{user_id}/" in res["storage_key"]
    assert res["public_url"].startswith(f"https://test.supabase.co/storage/v1/object/public/avatars/{user_id}/")
    assert res["upload_url"].startswith(f"https://test.supabase.co/storage/v1/object/upload/sign/avatars/{user_id}/")

    # Security check: Ensure secret key is NEVER exposed in any returned field
    secret_val = settings.SUPABASE_SECRET_KEY.get_secret_value()
    if secret_val:
        assert secret_val not in res["upload_url"]
        assert secret_val not in res["public_url"]
        assert secret_val not in res["storage_key"]


def test_public_and_signed_url_formatting(storage_service: StorageService) -> None:
    pub_url = storage_service.get_public_url("editorial-media", "routes/pindobal_cover.jpg")
    assert pub_url == "https://test.supabase.co/storage/v1/object/public/editorial-media/routes/pindobal_cover.jpg"

    signed_url = storage_service.create_signed_url("avatars", "user123/file.jpg", expires_in=1800)
    assert "https://test.supabase.co/storage/v1/object/sign/avatars/user123/file.jpg" in signed_url
    assert "expires_in=1800" in signed_url


def test_avatar_upload_endpoint_authenticated(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid.uuid4()
    mock_user = AuthenticatedUser(
        id=user_id,
        email="user@example.com",
        is_anonymous=False,
        role="authenticated",
        claims={"sub": str(user_id)},
    )
    monkeypatch.setattr(
        "app.core.security.verify_supabase_jwt", lambda token, jwks_client=None: mock_user
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/me/avatar-upload",
        json={"filename": "avatar.webp", "mime_type": "image/webp"},
        headers={"Authorization": "Bearer valid_token"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "upload_url" in data
    assert f"avatars/{user_id}/" in data["storage_key"]
    assert "public_url" in data


def test_avatar_upload_endpoint_unauthorized() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/me/avatar-upload",
        json={"filename": "avatar.png", "mime_type": "image/png"},
    )
    assert response.status_code == 401


def test_avatar_upload_endpoint_invalid_mime(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid.uuid4()
    mock_user = AuthenticatedUser(
        id=user_id,
        email="user@example.com",
        is_anonymous=False,
        role="authenticated",
        claims={"sub": str(user_id)},
    )
    monkeypatch.setattr(
        "app.core.security.verify_supabase_jwt", lambda token, jwks_client=None: mock_user
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/me/avatar-upload",
        json={"filename": "doc.pdf", "mime_type": "application/pdf"},
        headers={"Authorization": "Bearer valid_token"},
    )
    assert response.status_code == 400
    assert "não suportado" in response.json()["error"]["message"]
