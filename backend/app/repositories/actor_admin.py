"""Repository layer for administrative actor domain operations (ECO-1603)."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from geoalchemy2.functions import ST_X, ST_Y, ST_MakePoint, ST_SetSRID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.taxonomy import get_canonical_category
from app.models.domain import (
    AccessibilityFeature,
    Actor,
    ActorAccessibilityFeature,
    ActorCategory,
    RouteActor,
)


class ActorAdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -------------------------------------------------------------------------
    # Categories
    # -------------------------------------------------------------------------

    async def get_category_by_id(self, category_id: uuid.UUID) -> ActorCategory | None:
        stmt = select(ActorCategory).where(ActorCategory.id == category_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_category_by_slug(self, slug: str) -> ActorCategory | None:
        stmt = select(ActorCategory).where(ActorCategory.slug == slug)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_categories(self) -> Sequence[ActorCategory]:
        stmt = select(ActorCategory).order_by(
            ActorCategory.sort_order.asc(), ActorCategory.label.asc()
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create_category(
        self,
        slug: str,
        label: str,
        icon: str | None = None,
        color: str | None = None,
        sort_order: int = 0,
    ) -> ActorCategory:
        canonical = get_canonical_category(slug)
        category = ActorCategory(
            id=uuid.uuid4(),
            slug=slug,
            label=label,
            icon=icon,
            color=color,
            sort_order=sort_order,
            is_public=canonical["is_public"],
            spatial_scope=canonical["spatial_scope"],
        )
        self.db.add(category)
        await self.db.flush()
        return category

    async def update_category(
        self,
        category_id: uuid.UUID,
        label: str | None = None,
        icon: str | None = None,
        color: str | None = None,
        sort_order: int | None = None,
    ) -> ActorCategory | None:
        category = await self.get_category_by_id(category_id)
        if not category:
            return None

        if label is not None:
            category.label = label
        if icon is not None:
            category.icon = icon
        if color is not None:
            category.color = color
        if sort_order is not None:
            category.sort_order = sort_order

        category.updated_at = datetime.now(UTC)
        await self.db.flush()
        return category

    # -------------------------------------------------------------------------
    # Accessibility Features
    # -------------------------------------------------------------------------

    async def get_accessibility_feature_by_id(
        self, feature_id: uuid.UUID
    ) -> AccessibilityFeature | None:
        stmt = select(AccessibilityFeature).where(AccessibilityFeature.id == feature_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_accessibility_feature_by_slug(self, slug: str) -> AccessibilityFeature | None:
        stmt = select(AccessibilityFeature).where(AccessibilityFeature.slug == slug)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_accessibility_features(self) -> Sequence[AccessibilityFeature]:
        stmt = select(AccessibilityFeature).order_by(AccessibilityFeature.label.asc())
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create_accessibility_feature(
        self,
        slug: str,
        label: str,
        description: str | None = None,
        icon: str | None = None,
    ) -> AccessibilityFeature:
        feature = AccessibilityFeature(
            id=uuid.uuid4(),
            slug=slug,
            label=label,
            description=description,
            icon=icon,
        )
        self.db.add(feature)
        await self.db.flush()
        return feature

    async def update_accessibility_feature(
        self,
        feature_id: uuid.UUID,
        label: str | None = None,
        description: str | None = None,
        icon: str | None = None,
    ) -> AccessibilityFeature | None:
        feature = await self.get_accessibility_feature_by_id(feature_id)
        if not feature:
            return None

        if label is not None:
            feature.label = label
        if description is not None:
            feature.description = description
        if icon is not None:
            feature.icon = icon

        feature.updated_at = datetime.now(UTC)
        await self.db.flush()
        return feature

    # -------------------------------------------------------------------------
    # Actors
    # -------------------------------------------------------------------------

    async def get_actor_by_id(
        self, actor_id: uuid.UUID, include_deleted: bool = True
    ) -> Actor | None:
        stmt = (
            select(Actor)
            .options(
                selectinload(Actor.category),
                selectinload(Actor.accessibility_features).selectinload(
                    ActorAccessibilityFeature.feature
                ),
            )
            .where(Actor.id == actor_id)
        )
        if not include_deleted:
            stmt = stmt.where(Actor.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_actor_by_slug(self, slug: str) -> Actor | None:
        stmt = select(Actor).where(Actor.slug == slug)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_actors(
        self,
        category_id: uuid.UUID | None = None,
        include_deleted: bool = False,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Actor], int]:
        base_stmt = select(Actor).options(
            selectinload(Actor.category),
            selectinload(Actor.accessibility_features).selectinload(
                ActorAccessibilityFeature.feature
            ),
        )

        if not include_deleted:
            base_stmt = base_stmt.where(Actor.deleted_at.is_(None))
        if category_id is not None:
            base_stmt = base_stmt.where(Actor.category_id == category_id)
        if q and q.strip():
            pattern = f"%{q.strip()}%"
            base_stmt = base_stmt.where(
                Actor.name.ilike(pattern) | Actor.slug.ilike(pattern)
            )

        # Count total query
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        # Query page
        paginated_stmt = (
            base_stmt.order_by(Actor.name.asc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(paginated_stmt)
        return res.scalars().all(), total

    async def create_actor(
        self,
        category_id: uuid.UUID,
        slug: str,
        name: str,
        description: str | None = None,
        sub_category: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state_code: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        instagram: str | None = None,
        website: str | None = None,
        opening_hours: dict[str, Any] | None = None,
        payment_methods: list[Any] | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        green_badge_status: str = "none",
        verification_status: str = "unverified",
    ) -> Actor:
        loc_geom = None
        if latitude is not None and longitude is not None:
            loc_geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        actor = Actor(
            id=uuid.uuid4(),
            category_id=category_id,
            slug=slug,
            name=name,
            description=description,
            sub_category=sub_category,
            address=address,
            city=city,
            state_code=state_code,
            phone=phone,
            email=email,
            instagram=instagram,
            website=website,
            opening_hours=opening_hours or {},
            payment_methods=payment_methods or [],
            location=loc_geom,
            green_badge_status=green_badge_status,
            verification_status=verification_status,
        )
        self.db.add(actor)
        await self.db.flush()
        return actor

    async def update_actor(
        self,
        actor_id: uuid.UUID,
        category_id: uuid.UUID | None = None,
        name: str | None = None,
        description: str | None = None,
        sub_category: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state_code: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        instagram: str | None = None,
        website: str | None = None,
        opening_hours: dict[str, Any] | None = None,
        payment_methods: list[Any] | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        green_badge_status: str | None = None,
        verification_status: str | None = None,
    ) -> Actor | None:
        actor = await self.get_actor_by_id(actor_id, include_deleted=True)
        if not actor:
            return None

        if category_id is not None:
            actor.category_id = category_id
        if name is not None:
            actor.name = name
        if description is not None:
            actor.description = description
        if sub_category is not None:
            actor.sub_category = sub_category
        if address is not None:
            actor.address = address
        if city is not None:
            actor.city = city
        if state_code is not None:
            actor.state_code = state_code
        if phone is not None:
            actor.phone = phone
        if email is not None:
            actor.email = email
        if instagram is not None:
            actor.instagram = instagram
        if website is not None:
            actor.website = website
        if opening_hours is not None:
            actor.opening_hours = opening_hours
        if payment_methods is not None:
            actor.payment_methods = payment_methods
        if latitude is not None and longitude is not None:
            actor.location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        if green_badge_status is not None:
            actor.green_badge_status = green_badge_status
        if verification_status is not None:
            actor.verification_status = verification_status

        actor.updated_at = datetime.now(UTC)
        await self.db.flush()
        return actor

    async def soft_delete_actor(self, actor_id: uuid.UUID) -> Actor | None:
        actor = await self.get_actor_by_id(actor_id, include_deleted=True)
        if not actor:
            return None
        actor.deleted_at = datetime.now(UTC)
        actor.updated_at = datetime.now(UTC)
        await self.db.flush()
        return actor

    async def set_actor_accessibility_features(
        self, actor_id: uuid.UUID, feature_ids: list[uuid.UUID]
    ) -> None:
        # Delete existing links
        stmt_del = select(ActorAccessibilityFeature).where(
            ActorAccessibilityFeature.actor_id == actor_id
        )
        res_del = await self.db.execute(stmt_del)
        for existing in res_del.scalars().all():
            await self.db.delete(existing)

        # Insert new links
        for feature_id in feature_ids:
            link = ActorAccessibilityFeature(
                id=uuid.uuid4(),
                actor_id=actor_id,
                feature_id=feature_id,
                verification_status="self_declared",
            )
            self.db.add(link)
        await self.db.flush()

    async def get_actor_coordinates(
        self, actor: Actor
    ) -> tuple[float | None, float | None]:
        if actor.location is None:
            return None, None
        stmt = select(
            ST_Y(actor.location).label("lat"),
            ST_X(actor.location).label("lon"),
        )
        res = await self.db.execute(stmt)
        row = res.one_or_none()
        if not row:
            return None, None
        return float(row.lat), float(row.lon)

    # -------------------------------------------------------------------------
    # Route Actors (Route Links)
    # -------------------------------------------------------------------------

    async def get_route_actor_by_id(self, link_id: uuid.UUID) -> RouteActor | None:
        stmt = select(RouteActor).where(
            RouteActor.id == link_id, RouteActor.archived_at.is_(None)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_route_actor_by_route_and_actor(
        self, route_id: uuid.UUID, actor_id: uuid.UUID
    ) -> RouteActor | None:
        stmt = select(RouteActor).where(
            RouteActor.route_id == route_id,
            RouteActor.actor_id == actor_id,
            RouteActor.archived_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_route_actors_by_actor(
        self, actor_id: uuid.UUID
    ) -> Sequence[RouteActor]:
        stmt = (
            select(RouteActor)
            .where(RouteActor.actor_id == actor_id, RouteActor.archived_at.is_(None))
            .order_by(RouteActor.sort_order.asc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def list_route_actors_by_route(
        self, route_id: uuid.UUID
    ) -> Sequence[RouteActor]:
        stmt = (
            select(RouteActor)
            .where(RouteActor.route_id == route_id, RouteActor.archived_at.is_(None))
            .order_by(RouteActor.sort_order.asc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create_route_actor(
        self,
        route_id: uuid.UUID,
        actor_id: uuid.UUID,
        distance_to_route_m: float | None = None,
        route_segment_index: int | None = None,
        origin_flags: dict[str, Any] | None = None,
        is_featured: bool = False,
        sort_order: int = 0,
    ) -> RouteActor:
        link = RouteActor(
            id=uuid.uuid4(),
            route_id=route_id,
            actor_id=actor_id,
            distance_to_route_m=distance_to_route_m,
            route_segment_index=route_segment_index,
            origin_flags=origin_flags or {},
            is_featured=is_featured,
            sort_order=sort_order,
        )
        self.db.add(link)
        await self.db.flush()
        return link

    async def update_route_actor(
        self,
        link_id: uuid.UUID,
        distance_to_route_m: float | None = None,
        route_segment_index: int | None = None,
        origin_flags: dict[str, Any] | None = None,
        is_featured: bool | None = None,
        sort_order: int | None = None,
    ) -> RouteActor | None:
        link = await self.get_route_actor_by_id(link_id)
        if not link:
            return None

        if distance_to_route_m is not None:
            link.distance_to_route_m = distance_to_route_m
        if route_segment_index is not None:
            link.route_segment_index = route_segment_index
        if origin_flags is not None:
            link.origin_flags = origin_flags
        if is_featured is not None:
            link.is_featured = is_featured
        if sort_order is not None:
            link.sort_order = sort_order

        link.updated_at = datetime.now(UTC)
        await self.db.flush()
        return link

    async def delete_route_actor(self, link_id: uuid.UUID) -> bool:
        link = await self.get_route_actor_by_id(link_id)
        if not link:
            return False
        await self.db.delete(link)
        await self.db.flush()
        return True
