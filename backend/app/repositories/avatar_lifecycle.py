"""Persistence boundary for atomic avatar replacement."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import MediaAsset, Profile


class AvatarLifecycleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def replace_avatar(
        self,
        *,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
        storage_key: str,
        checksum_sha256: str,
        width_px: int,
        height_px: int,
        derivatives: dict[str, Any],
    ) -> tuple[MediaAsset, MediaAsset | None]:
        profile = await self.db.scalar(
            select(Profile).where(Profile.id == user_id).with_for_update()
        )
        if profile is None:
            profile = Profile(id=user_id, status="active")
            self.db.add(profile)
            await self.db.flush()

        previous = None
        if profile.avatar_media_id is not None:
            previous = await self.db.scalar(
                select(MediaAsset)
                .where(MediaAsset.id == profile.avatar_media_id)
                .with_for_update()
            )

        now = datetime.now(UTC)
        asset = MediaAsset(
            id=asset_id,
            owner_type="profile",
            owner_id=user_id,
            storage_key=storage_key,
            mime_type="image/webp",
            alt_text="Foto de perfil do usuário.",
            credit="Imagem enviada pelo usuário.",
            license_code="PROPRIETARY",
            processing_status="ready",
            checksum_sha256=checksum_sha256,
            width_px=width_px,
            height_px=height_px,
            derivatives=derivatives,
            processed_at=now,
            media_kind="stored",
        )
        self.db.add(asset)
        if previous is not None:
            # Persist cleanup intent in the same commit as the profile swap. If
            # the process stops before Storage deletion, MediaOrphanJob sees it.
            previous.deleted_at = now
        profile.avatar_media_id = asset_id
        profile.updated_at = now
        await self.db.commit()
        return asset, previous

    async def delete_asset(self, asset_id: uuid.UUID) -> None:
        await self.db.execute(delete(MediaAsset).where(MediaAsset.id == asset_id))
        await self.db.commit()

    async def mark_asset_for_cleanup(self, asset_id: uuid.UUID) -> None:
        """Soft-delete an object-backed row so MediaOrphanJob can report it."""
        asset = await self.db.scalar(
            select(MediaAsset).where(MediaAsset.id == asset_id).with_for_update()
        )
        if asset is not None:
            asset.deleted_at = datetime.now(UTC)
            await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
