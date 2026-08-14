"""Persistence boundary for the editorial media processing lifecycle."""

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Actor, AuditLog, MediaAsset, Route, RouteOrigin


class MediaLifecycleRepository:
    """Keep media state and its audit record in the same database transaction."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def owner_exists(self, owner_type: str, owner_id: uuid.UUID) -> bool:
        if owner_type == "route":
            statement = select(Route.id).where(Route.id == owner_id)
        elif owner_type == "origin":
            statement = select(RouteOrigin.id).where(RouteOrigin.id == owner_id)
        elif owner_type == "actor":
            statement = select(Actor.id).where(Actor.id == owner_id)
        else:
            return False
        return await self.db.scalar(statement) is not None

    async def create_processing(
        self,
        *,
        asset_id: uuid.UUID,
        owner_type: str,
        owner_id: uuid.UUID,
        mime_type: str,
        alt_text: str,
        credit: str,
        license_code: str,
        actor_id: uuid.UUID,
        request_id: uuid.UUID | None,
    ) -> MediaAsset:
        asset = MediaAsset(
            id=asset_id,
            owner_type=owner_type,
            owner_id=owner_id,
            mime_type=mime_type,
            alt_text=alt_text,
            credit=credit,
            license_code=license_code,
            media_kind="stored",
            processing_status="processing",
        )
        self.db.add(asset)
        self._audit(
            actor_id=actor_id,
            action="CREATE",
            asset_id=asset_id,
            changes={"after": {"processing_status": "processing"}},
            request_id=request_id,
        )
        await self.db.commit()
        return asset

    async def mark_ready(
        self,
        *,
        asset_id: uuid.UUID,
        storage_key: str,
        checksum_sha256: str,
        width_px: int,
        height_px: int,
        derivatives: dict[str, Any],
        actor_id: uuid.UUID,
        request_id: uuid.UUID | None,
    ) -> MediaAsset:
        asset = await self._locked_asset(asset_id)
        asset.storage_key = storage_key
        asset.checksum_sha256 = checksum_sha256
        asset.width_px = width_px
        asset.height_px = height_px
        asset.derivatives = derivatives
        asset.processing_status = "ready"
        asset.processed_at = datetime.now(UTC)
        asset.rejected_reason = None
        self._audit(
            actor_id=actor_id,
            action="UPDATE",
            asset_id=asset_id,
            changes={
                "before": {"processing_status": "processing"},
                "after": {
                    "processing_status": "ready",
                    "checksum_sha256": checksum_sha256,
                    "derivatives": sorted(derivatives),
                },
            },
            request_id=request_id,
        )
        await self.db.commit()
        return asset

    async def mark_rejected(
        self,
        *,
        asset_id: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID,
        request_id: uuid.UUID | None,
        cleanup_pending: bool,
        orphan_storage_paths: list[str],
    ) -> MediaAsset:
        await self.db.rollback()
        asset = await self._locked_asset(asset_id)
        before = asset.processing_status
        asset.processing_status = "rejected"
        asset.processed_at = datetime.now(UTC)
        asset.rejected_reason = reason
        asset.storage_key = None
        asset.checksum_sha256 = None
        asset.width_px = None
        asset.height_px = None
        asset.derivatives = {}
        self._audit(
            actor_id=actor_id,
            action="UPDATE",
            asset_id=asset_id,
            changes={
                "before": {"processing_status": before},
                "after": {
                    "processing_status": "rejected",
                    "cleanup_pending": cleanup_pending,
                    "orphan_storage_paths": orphan_storage_paths,
                },
            },
            reason=reason,
            request_id=request_id,
        )
        await self.db.commit()
        return asset

    async def list_cleanup_pending(self, *, limit: int = 50) -> list[tuple[uuid.UUID, list[str]]]:
        """Return the latest auditable orphan paths without exposing Storage credentials."""
        statement = (
            select(AuditLog)
            .where(
                AuditLog.resource_type == "media",
                AuditLog.changes["after"]["cleanup_pending"].as_boolean().is_(True),
            )
            .order_by(AuditLog.timestamp.asc())
            .limit(limit)
        )
        logs = list((await self.db.scalars(statement)).all())
        pending: list[tuple[uuid.UUID, list[str]]] = []
        for log in logs:
            after = log.changes.get("after", {})
            paths = after.get("orphan_storage_paths", [])
            if isinstance(paths, list) and all(isinstance(path, str) for path in paths):
                pending.append((log.resource_id, paths))
        return pending

    async def cleanup_already_completed(self, asset_id: uuid.UUID) -> bool:
        statement = select(AuditLog).where(
            AuditLog.resource_type == "media",
            AuditLog.resource_id == asset_id,
        ).order_by(AuditLog.timestamp.desc())
        logs = list((await self.db.scalars(statement)).all())
        return any(log.changes.get("after", {}).get("cleanup_pending") is False for log in logs)

    async def mark_cleanup_completed(
        self,
        *,
        asset_id: uuid.UUID,
        paths: list[str],
        actor_id: uuid.UUID,
        request_id: uuid.UUID | None,
    ) -> None:
        self._audit(
            actor_id=actor_id,
            action="UPDATE",
            asset_id=asset_id,
            changes={
                "before": {"cleanup_pending": True, "orphan_storage_paths": paths},
                "after": {"cleanup_pending": False, "orphan_storage_paths": []},
            },
            reason="Limpeza compensatória de objetos órfãos concluída.",
            request_id=request_id,
        )
        await self.db.commit()

    async def _locked_asset(self, asset_id: uuid.UUID) -> MediaAsset:
        statement = select(MediaAsset).where(MediaAsset.id == asset_id).with_for_update()
        asset = cast(MediaAsset | None, await self.db.scalar(statement))
        if asset is None:
            raise LookupError("Registro de mídia não encontrado durante o processamento.")
        return asset

    def _audit(
        self,
        *,
        actor_id: uuid.UUID,
        action: str,
        asset_id: uuid.UUID,
        changes: dict[str, Any],
        request_id: uuid.UUID | None,
        reason: str | None = None,
    ) -> None:
        self.db.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                resource_type="media",
                resource_id=asset_id,
                changes=changes,
                reason=reason,
                request_id=request_id,
            )
        )
