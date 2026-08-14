"""Network-free tests for real avatar Storage and multipart API boundaries."""

import uuid
from unittest.mock import AsyncMock

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.v1.auth import get_current_user
from app.core.security import AuthenticatedUser
from app.main import app
from app.services.avatar_lifecycle import AvatarResult
from app.services.avatar_storage import SupabaseAvatarStorage
from app.services.dependencies import get_avatar_lifecycle_service
from app.services.storage_service import StorageService


def test_storage_service_only_formats_public_urls() -> None:
    service = StorageService(supabase_url="https://test.supabase.co")
    assert service.get_public_url("avatars", "user/avatar.webp") == (
        "https://test.supabase.co/storage/v1/object/public/avatars/user/avatar.webp"
    )
    assert not hasattr(service, "create_avatar_upload_url")
    assert not hasattr(service, "create_signed_url")


async def test_avatar_storage_uses_server_secret_and_official_object_routes(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.avatar_storage.settings.SUPABASE_SECRET_KEY", SecretStr("secret")
    )
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if "/object/list/avatars" in str(request.url):
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        storage = SupabaseAvatarStorage(client=client)
        await storage.upload("user/avatar.webp", b"webp")
        await storage.remove(["avatars/user/avatar.webp"])
        assert await storage.list_user_paths("user") == []

    assert requests[0].method == "POST"
    assert "/storage/v1/object/avatars/user/avatar.webp" in str(requests[0].url)
    assert requests[0].headers["x-upsert"] == "false"
    assert requests[1].method == "DELETE"
    assert requests[2].method == "POST"
    assert all(
        request.headers.get("authorization", "").startswith("Bearer ")
        for request in requests
    )


def test_multipart_avatar_endpoint_delegates_real_bytes() -> None:
    user_id = uuid.uuid4()
    user = AuthenticatedUser(user_id, "user@example.com", False, "authenticated", {})
    service = AsyncMock()
    service.replace_avatar.return_value = AvatarResult(
        media_asset_id=uuid.uuid4(),
        public_url="https://unit-test.supabase.co/avatar.webp",
        derivatives={"thumb": "https://unit-test.supabase.co/avatar.webp"},
        alt_text="Foto de perfil do usuário.",
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_avatar_lifecycle_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/api/v1/me/avatar",
            files={"file": ("avatar.png", b"real-image-bytes", "image/png")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["media_asset_id"] == str(
        service.replace_avatar.return_value.media_asset_id
    )
    service.replace_avatar.assert_awaited_once_with(
        user_id=user_id, content=b"real-image-bytes", declared_mime="image/png"
    )


def test_multipart_avatar_endpoint_requires_authentication() -> None:
    response = TestClient(app).post(
        "/api/v1/me/avatar",
        files={"file": ("avatar.png", b"bytes", "image/png")},
    )
    assert response.status_code == 401
