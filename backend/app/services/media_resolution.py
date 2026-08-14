"""Media resolution service for resolving storage keys, derivatives and URLs (ECO-1703)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import MediaAsset
from app.schemas.envelopes import ResolvedMediaItemSchema
from app.services.storage_service import StorageService


class MediaResolutionService:
    """Resolves raw MediaAsset DB records into client-ready payloads with URLs and metadata."""

    def __init__(self, db: AsyncSession, storage_service: StorageService | None = None) -> None:
        self.db = db
        self.storage_service = storage_service or StorageService()

    def resolve_asset_urls(self, asset: MediaAsset) -> ResolvedMediaItemSchema:
        """Resolve a single MediaAsset entity into a ResolvedMediaItemSchema with full URLs."""
        main_url = ""
        derivatives_urls: dict[str, str] = {}

        if asset.media_kind == "google_proxy" and asset.external_photo_reference:
            main_url = asset.external_photo_reference
        elif asset.storage_key:
            # Handle storage key prefixing if necessary
            key = asset.storage_key
            bucket = "editorial-media"
            path = key
            if "/" in key:
                parts = key.split("/", 1)
                if parts[0] in ("editorial-media", "avatars"):
                    bucket = parts[0]
                    path = parts[1]
            main_url = self.storage_service.get_public_url(bucket, path)

        if asset.derivatives and isinstance(asset.derivatives, dict):
            for d_name, d_meta in asset.derivatives.items():
                if isinstance(d_meta, dict) and "storage_key" in d_meta:
                    d_key = str(d_meta["storage_key"])
                    d_bucket = "editorial-media"
                    d_path = d_key
                    if "/" in d_key:
                        parts = d_key.split("/", 1)
                        if parts[0] in ("editorial-media", "avatars"):
                            d_bucket = parts[0]
                            d_path = parts[1]
                    derivatives_urls[d_name] = self.storage_service.get_public_url(d_bucket, d_path)

        return ResolvedMediaItemSchema(
            id=asset.id,
            owner_type=asset.owner_type,
            owner_id=asset.owner_id,
            url=main_url,
            derivatives=derivatives_urls,
            alt_text=asset.alt_text,
            credit=asset.credit,
            license_code=asset.license_code,
            media_kind=asset.media_kind,
            sort_order=asset.sort_order,
        )

    async def resolve_media_for_owner(
        self, owner_type: str, owner_id: uuid.UUID
    ) -> tuple[ResolvedMediaItemSchema | None, list[ResolvedMediaItemSchema]]:
        """Fetch and resolve cover media and gallery items for a single owner."""
        stmt = (
            select(MediaAsset)
            .where(
                MediaAsset.owner_type == owner_type,
                MediaAsset.owner_id == owner_id,
                MediaAsset.deleted_at.is_(None),
                MediaAsset.processing_status == "ready",
            )
            .order_by(MediaAsset.sort_order.asc(), MediaAsset.created_at.asc())
        )
        res = await self.db.scalars(stmt)
        assets = list(res.all())

        if not assets:
            return None, []

        resolved_items = [self.resolve_asset_urls(a) for a in assets]
        cover_item = resolved_items[0] if resolved_items else None
        return cover_item, resolved_items

    async def resolve_asset_by_id(
        self, asset_id: uuid.UUID, *, owner_type: str, owner_id: uuid.UUID
    ) -> ResolvedMediaItemSchema | None:
        """Resolve an exact ready asset while enforcing its expected owner."""
        asset = await self.db.scalar(
            select(MediaAsset).where(
                MediaAsset.id == asset_id,
                MediaAsset.owner_type == owner_type,
                MediaAsset.owner_id == owner_id,
                MediaAsset.deleted_at.is_(None),
                MediaAsset.processing_status == "ready",
            )
        )
        return self.resolve_asset_urls(asset) if asset is not None else None

    async def batch_resolve_covers_for_owners(
        self, owner_type: str, owner_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, ResolvedMediaItemSchema]:
        """Fetch and resolve the primary cover item for a list of owner IDs in a single query."""
        if not owner_ids:
            return {}

        stmt = (
            select(MediaAsset)
            .where(
                MediaAsset.owner_type == owner_type,
                MediaAsset.owner_id.in_(owner_ids),
                MediaAsset.deleted_at.is_(None),
                MediaAsset.processing_status == "ready",
            )
            .order_by(MediaAsset.sort_order.asc(), MediaAsset.created_at.asc())
        )
        res = await self.db.scalars(stmt)
        assets = list(res.all())

        covers: dict[uuid.UUID, ResolvedMediaItemSchema] = {}
        for asset in assets:
            if asset.owner_id not in covers:
                covers[asset.owner_id] = self.resolve_asset_urls(asset)

        return covers
