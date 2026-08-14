"""Job for identifying and reporting orphaned media storage files (ECO-1703)."""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import MediaAsset


@dataclass(slots=True)
class OrphanReport:
    total_assets_scanned: int = 0
    orphaned_assets_count: int = 0
    orphaned_storage_paths: list[str] = field(default_factory=list)
    unreferenced_rejected_count: int = 0
    is_dry_run: bool = True


class MediaOrphanJob:
    """Scans media assets and storage references to report orphaned files in dry-run mode."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def run_dry_run(self) -> OrphanReport:
        """Perform a non-destructive dry-run scan of orphaned media assets."""
        report = OrphanReport(is_dry_run=True)

        # 1. Scan rejected assets with pending cleanup paths
        stmt_rejected = select(MediaAsset).where(
            MediaAsset.processing_status == "rejected",
            MediaAsset.deleted_at.is_(None),
        )
        res_rejected = await self.db.scalars(stmt_rejected)
        rejected_assets = list(res_rejected.all())
        report.total_assets_scanned += len(rejected_assets)

        for asset in rejected_assets:
            paths = []
            if asset.storage_key:
                paths.append(asset.storage_key)
            if asset.derivatives and isinstance(asset.derivatives, dict):
                for d_meta in asset.derivatives.values():
                    if isinstance(d_meta, dict) and "storage_key" in d_meta:
                        paths.append(str(d_meta["storage_key"]))
            if paths:
                report.orphaned_assets_count += 1
                report.orphaned_storage_paths.extend(paths)
                report.unreferenced_rejected_count += 1

        # 2. Scan soft-deleted assets
        stmt_deleted = select(MediaAsset).where(MediaAsset.deleted_at.is_not(None))
        res_deleted = await self.db.scalars(stmt_deleted)
        deleted_assets = list(res_deleted.all())
        report.total_assets_scanned += len(deleted_assets)

        for asset in deleted_assets:
            paths = []
            if asset.storage_key:
                paths.append(asset.storage_key)
            if asset.derivatives and isinstance(asset.derivatives, dict):
                for d_meta in asset.derivatives.values():
                    if isinstance(d_meta, dict) and "storage_key" in d_meta:
                        paths.append(str(d_meta["storage_key"]))
            if paths:
                report.orphaned_assets_count += 1
                report.orphaned_storage_paths.extend(paths)

        # Remove duplicates
        report.orphaned_storage_paths = sorted(list(set(report.orphaned_storage_paths)))
        return report
