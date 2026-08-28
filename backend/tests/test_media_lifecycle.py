"""Network-free lifecycle and compensation tests for ECO-1702."""

import io
import uuid
from dataclasses import replace
from typing import Any, cast

import httpx
import pytest
from PIL import Image

from app.services.editorial_authorization import AuthorizationContext
from app.services.editorial_storage import EditorialStorageError, SupabaseEditorialStorage
from app.services.media_lifecycle import (
    EditorialMediaInput,
    MediaLifecycleFailure,
    MediaLifecycleService,
)


def _jpeg() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (320, 240), "green").save(output, format="JPEG")
    return output.getvalue()


class FakeAuthorization:
    def __init__(self) -> None:
        self.capabilities: list[str] = []

    async def require_capability(self, context: AuthorizationContext, capability: str) -> None:
        self.capabilities.append(capability)


class FakeRepository:
    def __init__(self, *, fail_ready: bool = False) -> None:
        self.fail_ready = fail_ready
        self.created: dict[str, Any] | None = None
        self.ready: dict[str, Any] | None = None
        self.rejected: dict[str, Any] | None = None
        self.pending_cleanup: list[tuple[uuid.UUID, list[str]]] = []
        self.completed_cleanup: list[dict[str, Any]] = []

    async def owner_exists(self, owner_type: str, owner_id: uuid.UUID) -> bool:
        return True

    async def create_processing(self, **kwargs: Any) -> object:
        self.created = kwargs
        return object()

    async def mark_ready(self, **kwargs: Any) -> object:
        if self.fail_ready:
            raise RuntimeError("database DSN must never leak")
        self.ready = kwargs
        return cast(object, kwargs)

    async def mark_rejected(self, **kwargs: Any) -> object:
        self.rejected = kwargs
        return object()

    async def list_cleanup_pending(self, *, limit: int) -> list[tuple[uuid.UUID, list[str]]]:
        return self.pending_cleanup[:limit]

    async def cleanup_already_completed(self, asset_id: uuid.UUID) -> bool:
        return any(item["asset_id"] == asset_id for item in self.completed_cleanup)

    async def mark_cleanup_completed(self, **kwargs: Any) -> None:
        self.completed_cleanup.append(kwargs)


class FakeStorage:
    def __init__(self, *, fail_upload_at: int | None = None, fail_remove: bool = False) -> None:
        self.fail_upload_at = fail_upload_at
        self.fail_remove = fail_remove
        self.uploaded: list[str] = []
        self.removed: list[str] = []

    async def upload(self, path: str, content: bytes, *, content_type: str) -> None:
        if self.fail_upload_at == len(self.uploaded):
            raise EditorialStorageError("remote body with secret")
        assert content
        assert content_type == "image/webp"
        self.uploaded.append(path)

    async def remove(self, paths: list[str]) -> None:
        if self.fail_remove:
            raise EditorialStorageError("cleanup failed")
        self.removed.extend(paths)


def _payload() -> EditorialMediaInput:
    return EditorialMediaInput(
        owner_type="actor",
        owner_id=uuid.uuid4(),
        content=_jpeg(),
        declared_mime="image/jpeg",
        alt_text="Artesã trabalhando com fibras naturais.",
        credit="Acervo comunitário",
        license_code="CC-BY-4.0",
        request_id=uuid.uuid4(),
    )


@pytest.mark.asyncio
async def test_lifecycle_persists_processing_uploads_and_marks_ready() -> None:
    repository = FakeRepository()
    storage = FakeStorage()
    authorization = FakeAuthorization()
    service = MediaLifecycleService(
        cast(Any, repository), cast(Any, authorization), storage=storage
    )
    context = AuthorizationContext(actor_id=uuid.uuid4())

    await service.process_editorial_image(context, _payload())

    assert authorization.capabilities == ["content.draft.create"]
    assert repository.created is not None
    assert repository.ready is not None
    assert repository.created["asset_id"] == repository.ready["asset_id"]
    assert set(repository.ready["derivatives"]) == {"thumb", "card", "hero"}
    assert len(storage.uploaded) == 3
    assert len(set(storage.uploaded)) == 3
    assert all(path.endswith(".webp") for path in storage.uploaded)
    hero = repository.ready["derivatives"]["hero"]
    assert repository.ready["checksum_sha256"] == hero["checksum_sha256"]
    assert repository.ready["storage_key"] == hero["storage_key"]
    assert repository.rejected is None


@pytest.mark.asyncio
async def test_partial_storage_failure_removes_only_objects_uploaded_by_attempt() -> None:
    repository = FakeRepository()
    storage = FakeStorage(fail_upload_at=1)
    service = MediaLifecycleService(
        cast(Any, repository), cast(Any, FakeAuthorization()), storage=storage
    )

    with pytest.raises(MediaLifecycleFailure, match="armazenar derivados"):
        await service.process_editorial_image(
            AuthorizationContext(actor_id=uuid.uuid4()), _payload()
        )

    assert storage.removed == storage.uploaded
    assert len(storage.removed) == 1
    assert repository.rejected is not None
    assert repository.rejected["cleanup_pending"] is False
    assert "secret" not in repository.rejected["reason"]


@pytest.mark.asyncio
async def test_ready_database_failure_compensates_all_objects_and_marks_rejected() -> None:
    repository = FakeRepository(fail_ready=True)
    storage = FakeStorage()
    service = MediaLifecycleService(
        cast(Any, repository), cast(Any, FakeAuthorization()), storage=storage
    )

    with pytest.raises(MediaLifecycleFailure, match="Falha interna"):
        await service.process_editorial_image(
            AuthorizationContext(actor_id=uuid.uuid4()), _payload()
        )

    assert storage.removed == storage.uploaded
    assert len(storage.removed) == 3
    assert repository.rejected is not None
    assert "DSN" not in repository.rejected["reason"]


@pytest.mark.asyncio
async def test_failed_compensation_is_explicitly_auditable() -> None:
    repository = FakeRepository(fail_ready=True)
    storage = FakeStorage(fail_remove=True)
    service = MediaLifecycleService(
        cast(Any, repository), cast(Any, FakeAuthorization()), storage=storage
    )

    with pytest.raises(MediaLifecycleFailure, match="Limpeza compensatória pendente"):
        await service.process_editorial_image(
            AuthorizationContext(actor_id=uuid.uuid4()), _payload()
        )

    assert repository.rejected is not None
    assert repository.rejected["cleanup_pending"] is True
    assert repository.rejected["orphan_storage_paths"] == storage.uploaded


@pytest.mark.asyncio
async def test_invalid_image_is_rejected_without_touching_storage() -> None:
    repository = FakeRepository()
    storage = FakeStorage()
    payload = _payload()
    invalid = replace(payload, content=b"invalid")
    service = MediaLifecycleService(
        cast(Any, repository), cast(Any, FakeAuthorization()), storage=storage
    )

    with pytest.raises(MediaLifecycleFailure, match="imagem válida"):
        await service.process_editorial_image(AuthorizationContext(actor_id=uuid.uuid4()), invalid)

    assert not storage.uploaded
    assert repository.rejected is not None


@pytest.mark.asyncio
async def test_storage_adapter_uses_secret_server_side_without_upsert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, request=request)

    monkeypatch.setattr("app.services.editorial_storage.settings.SUPABASE_URL", "https://x.test")
    monkeypatch.setattr(
        "app.services.editorial_storage.settings.SUPABASE_SECRET_KEY",
        cast(Any, type("Secret", (), {"get_secret_value": lambda self: "server-secret"})()),
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        storage = SupabaseEditorialStorage(client=client)
        await storage.upload("actor/id/file.webp", b"webp", content_type="image/webp")
        await storage.remove(["actor/id/file.webp"])

    assert requests[0].method == "POST"
    assert requests[0].headers["x-upsert"] == "false"
    assert requests[0].headers["authorization"] == "Bearer server-secret"
    assert requests[1].method == "DELETE"
    assert b"actor/id/file.webp" in requests[1].content


@pytest.mark.asyncio
async def test_cleanup_recovery_is_authorized_and_idempotent() -> None:
    repository = FakeRepository()
    asset_id = uuid.uuid4()
    repository.pending_cleanup = [(asset_id, ["actor/id/orphan.webp"])]
    storage = FakeStorage()
    authorization = FakeAuthorization()
    service = MediaLifecycleService(
        cast(Any, repository), cast(Any, authorization), storage=storage
    )
    context = AuthorizationContext(actor_id=uuid.uuid4())

    first = await service.recover_pending_cleanup(context)
    second = await service.recover_pending_cleanup(context)

    assert first == (1, 0)
    assert second == (0, 0)
    assert storage.removed == ["actor/id/orphan.webp"]
    assert authorization.capabilities == ["content.archive", "content.archive"]


@pytest.mark.asyncio
async def test_cleanup_recovery_reports_storage_failure_without_marking_done() -> None:
    repository = FakeRepository()
    repository.pending_cleanup = [(uuid.uuid4(), ["actor/id/orphan.webp"])]
    storage = FakeStorage(fail_remove=True)
    service = MediaLifecycleService(
        cast(Any, repository), cast(Any, FakeAuthorization()), storage=storage
    )

    assert await service.recover_pending_cleanup(AuthorizationContext(actor_id=uuid.uuid4())) == (
        0,
        1,
    )
    assert repository.completed_cleanup == []
