"""Rollback and sanitization tests for the server-side avatar lifecycle."""

import uuid
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image

from app.services.avatar_lifecycle import AvatarLifecycleError, AvatarLifecycleService
from app.services.avatar_storage import AvatarStorageError


def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (1600, 1200), "green").save(output, format="PNG")
    return output.getvalue()


class Repository:
    def __init__(self) -> None:
        self.saved: dict[str, object] | None = None
        self.rolled_back = False
        self.cleanup_assets: list[uuid.UUID] = []
        self.previous = None

    async def replace_avatar(self, **kwargs: object):
        self.saved = kwargs
        return SimpleNamespace(id=kwargs["asset_id"], alt_text="Avatar"), self.previous

    async def delete_asset(self, _asset_id: uuid.UUID) -> None: ...

    async def mark_asset_for_cleanup(self, asset_id: uuid.UUID) -> None:
        self.cleanup_assets.append(asset_id)

    async def rollback(self) -> None:
        self.rolled_back = True


class Storage:
    def __init__(self, fail_at: int | None = None, fail_remove: bool = False) -> None:
        self.uploaded: list[tuple[str, bytes]] = []
        self.removed: list[str] = []
        self.fail_at = fail_at
        self.fail_remove = fail_remove

    async def upload(self, path: str, content: bytes) -> None:
        if self.fail_at == len(self.uploaded):
            raise AvatarStorageError("failure")
        self.uploaded.append((path, content))

    async def remove(self, paths: list[str]) -> None:
        if self.fail_remove:
            raise AvatarStorageError("failure")
        self.removed.extend(paths)


async def test_avatar_is_reencoded_to_three_webp_derivatives_before_persisting() -> None:
    repository = Repository()
    storage = Storage()
    service = AvatarLifecycleService(
        repository, storage=storage, public_base_url="https://unit-test.supabase.co"
    )

    result = await service.replace_avatar(
        user_id=uuid.uuid4(), content=png_bytes(), declared_mime="image/png"
    )

    assert len(storage.uploaded) == 3
    assert {path.split("_")[-2] for path, _ in storage.uploaded} == {"thumb", "card", "hero"}
    assert all(Image.open(BytesIO(content)).format == "WEBP" for _, content in storage.uploaded)
    assert repository.saved is not None
    assert result.public_url.endswith(".webp")


async def test_partial_upload_is_removed_and_database_is_rolled_back() -> None:
    repository = Repository()
    storage = Storage(fail_at=1)
    service = AvatarLifecycleService(
        repository, storage=storage, public_base_url="https://unit-test.supabase.co"
    )

    with pytest.raises(AvatarLifecycleError, match="segurança"):
        await service.replace_avatar(
            user_id=uuid.uuid4(), content=png_bytes(), declared_mime="image/png"
        )

    assert repository.rolled_back is True
    assert storage.removed == [storage.uploaded[0][0]]


async def test_declared_mime_mismatch_is_rejected_before_storage() -> None:
    storage = Storage()
    service = AvatarLifecycleService(
        Repository(), storage=storage, public_base_url="https://unit-test.supabase.co"
    )
    with pytest.raises(AvatarLifecycleError):
        await service.replace_avatar(
            user_id=uuid.uuid4(), content=png_bytes(), declared_mime="image/jpeg"
        )
    assert storage.uploaded == []


async def test_previous_avatar_remove_failure_marks_row_for_orphan_job() -> None:
    repository = Repository()
    previous_id = uuid.uuid4()
    repository.previous = SimpleNamespace(
        id=previous_id,
        storage_key="avatars/user/old.webp",
        derivatives={},
    )
    service = AvatarLifecycleService(
        repository,
        storage=Storage(fail_remove=True),
        public_base_url="https://unit-test.supabase.co",
    )

    await service.replace_avatar(
        user_id=uuid.uuid4(), content=png_bytes(), declared_mime="image/png"
    )

    assert repository.cleanup_assets == [previous_id]
