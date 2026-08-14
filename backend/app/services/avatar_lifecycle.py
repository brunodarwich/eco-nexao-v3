"""Safe multipart avatar processing and immutable Storage replacement."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.exc import SQLAlchemyError

from app.models.domain import MediaAsset
from app.repositories.avatar_lifecycle import AvatarLifecycleRepository
from app.services.avatar_storage import AvatarStorageError, SupabaseAvatarStorage
from app.services.media_processor import MediaProcessingError, MediaProcessor


class AvatarStorage(Protocol):
    async def upload(self, path: str, content: bytes) -> None: ...
    async def remove(self, paths: list[str]) -> None: ...


class AvatarLifecycleError(ValueError):
    """Safe avatar failure suitable for an API validation response."""


@dataclass(frozen=True, slots=True)
class AvatarResult:
    media_asset_id: uuid.UUID
    public_url: str
    derivatives: dict[str, str]
    alt_text: str


class AvatarLifecycleService:
    def __init__(
        self,
        repository: AvatarLifecycleRepository,
        *,
        storage: AvatarStorage | None = None,
        processor: MediaProcessor | None = None,
        public_base_url: str,
    ) -> None:
        self.repository = repository
        self.storage = storage or SupabaseAvatarStorage()
        self.processor = processor or MediaProcessor(max_bytes=5 * 1024 * 1024)
        self.public_base_url = public_base_url.rstrip("/")

    async def replace_avatar(
        self, *, user_id: uuid.UUID, content: bytes, declared_mime: str | None
    ) -> AvatarResult:
        try:
            processed = self.processor.process(content, declared_mime=declared_mime)
        except MediaProcessingError as exc:
            raise AvatarLifecycleError(str(exc)) from exc

        asset_id = uuid.uuid4()
        uploaded: list[str] = []
        metadata: dict[str, dict[str, str | int]] = {}
        try:
            for name, derivative in processed.derivatives.items():
                path = (
                    f"{user_id}/{asset_id}_{name}_"
                    f"{derivative.checksum_sha256}.webp"
                )
                await self.storage.upload(path, derivative.content)
                uploaded.append(path)
                metadata[name] = {
                    "storage_key": f"avatars/{path}",
                    "checksum_sha256": derivative.checksum_sha256,
                    "width_px": derivative.width,
                    "height_px": derivative.height,
                    "mime_type": derivative.mime_type,
                }

            hero = processed.derivatives["hero"]
            asset, previous = await self.repository.replace_avatar(
                user_id=user_id,
                asset_id=asset_id,
                storage_key=str(metadata["hero"]["storage_key"]),
                checksum_sha256=hero.checksum_sha256,
                width_px=hero.width,
                height_px=hero.height,
                derivatives=metadata,
            )
        except (AvatarStorageError, OSError, LookupError, RuntimeError, SQLAlchemyError) as exc:
            await self.repository.rollback()
            await self._remove_quietly(uploaded)
            raise AvatarLifecycleError("Não foi possível concluir o avatar com segurança.") from exc

        if previous is not None:
            previous_paths = self.storage_paths(previous)
            try:
                await self.storage.remove(previous_paths)
            except (AvatarStorageError, OSError):
                # MediaOrphanJob scans soft-deleted assets and reports these paths.
                await self.repository.mark_asset_for_cleanup(previous.id)
            else:
                try:
                    await self.repository.delete_asset(previous.id)
                except SQLAlchemyError:
                    await self.repository.rollback()

        return AvatarResult(
            media_asset_id=asset.id,
            public_url=self._public_url(str(metadata["thumb"]["storage_key"])),
            derivatives={
                name: self._public_url(str(value["storage_key"]))
                for name, value in metadata.items()
            },
            alt_text=asset.alt_text or "Foto de perfil do usuário.",
        )

    async def _remove_quietly(self, paths: list[str]) -> None:
        if not paths:
            return
        try:
            await self.storage.remove(paths)
        except (AvatarStorageError, OSError):
            return

    def _public_url(self, storage_key: str) -> str:
        path = storage_key.removeprefix("avatars/")
        return f"{self.public_base_url}/storage/v1/object/public/avatars/{path}"

    @staticmethod
    def storage_paths(asset: MediaAsset) -> list[str]:
        paths: set[str] = set()
        if asset.storage_key:
            paths.add(asset.storage_key)
        for value in (asset.derivatives or {}).values():
            if isinstance(value, dict) and isinstance(value.get("storage_key"), str):
                paths.add(str(value["storage_key"]))
        return sorted(paths)
