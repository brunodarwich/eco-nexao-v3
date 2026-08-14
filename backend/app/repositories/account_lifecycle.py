"""Private persistence operations for irreversible account deletion."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import DeletedUserTombstone, MediaAsset, Profile


class AccountLifecycleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def start_deletion(self, user_id: uuid.UUID) -> DeletedUserTombstone:
        # Concurrent retries converge on one marker instead of racing two INSERTs.
        await self.db.execute(
            insert(DeletedUserTombstone)
            .values(user_id=user_id, status="processing")
            .on_conflict_do_nothing(index_elements=[DeletedUserTombstone.user_id])
        )
        await self.db.commit()
        marker = await self.db.scalar(
            select(DeletedUserTombstone)
            .where(DeletedUserTombstone.user_id == user_id)
            .with_for_update()
        )
        if marker is None:  # Defensive: the insert/select pair must always converge.
            raise RuntimeError("Deletion marker was not persisted.")
        return marker

    async def avatar_assets(self, user_id: uuid.UUID) -> list[MediaAsset]:
        result = await self.db.scalars(
            select(MediaAsset).where(
                MediaAsset.owner_type == "profile", MediaAsset.owner_id == user_id
            )
        )
        return list(result.all())

    async def purge_domain_data(self, user_id: uuid.UUID) -> None:
        # Profile dependants are removed by the versioned ON DELETE CASCADE FKs.
        await self.db.execute(delete(Profile).where(Profile.id == user_id))
        await self.db.execute(
            delete(MediaAsset).where(
                MediaAsset.owner_type == "profile", MediaAsset.owner_id == user_id
            )
        )
        await self.db.commit()

    async def complete_deletion(self, user_id: uuid.UUID) -> None:
        marker = await self.db.scalar(
            select(DeletedUserTombstone)
            .where(DeletedUserTombstone.user_id == user_id)
            .with_for_update()
        )
        if marker is None:
            marker = DeletedUserTombstone(user_id=user_id)
            self.db.add(marker)
        marker.status = "completed"
        marker.completed_at = datetime.now(UTC)
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
