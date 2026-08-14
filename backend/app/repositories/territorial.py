"""Repository layer for territorial domain data access (ECO-0501 to ECO-0506) with AsyncSession."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any
from typing import cast as typing_cast

from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_X, ST_Y, ST_AsGeoJSON
from sqlalchemy import cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.domain import (
    AccessibilityFeature,
    Actor,
    ActorAccessibilityFeature,
    ActorCategory,
    ActorExternalRef,
    ExternalSource,
    FavoriteRoute,
    Region,
    Route,
    RouteActor,
    RouteAlert,
    RouteGeometry,
    RouteOrigin,
)


class TerritorialRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -------------------------------------------------------------------------
    # ECO-0501: Regions & Bootstrap
    # -------------------------------------------------------------------------

    async def get_active_regions(self) -> list[Region]:
        """Fetch all active regions ordered by name."""
        stmt = select(Region).where(Region.is_active.is_(True)).order_by(Region.name.asc())
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def get_region_by_id(self, region_id: uuid.UUID) -> Region | None:
        """Fetch region by UUID."""
        stmt = select(Region).where(Region.id == region_id, Region.is_active.is_(True))
        return typing_cast(Region | None, await self.db.scalar(stmt))

    async def get_region_by_slug(self, slug: str) -> Region | None:
        """Fetch region by slug."""
        stmt = select(Region).where(Region.slug == slug, Region.is_active.is_(True))
        return typing_cast(Region | None, await self.db.scalar(stmt))

    # -------------------------------------------------------------------------
    # ECO-0502 & ECO-0503: Routes & Details
    # -------------------------------------------------------------------------

    async def list_routes(
        self,
        region_id: uuid.UUID | None = None,
        q: str | None = None,
        saved: bool | None = None,
        user_id: uuid.UUID | None = None,
        verified: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Route], int]:
        """List active routes with filtering, search and pagination."""
        stmt = select(Route).where(Route.deleted_at.is_(None), Route.status == "active")

        if region_id:
            stmt = stmt.where(Route.region_id == region_id)
        if verified is not None:
            stmt = stmt.where(Route.is_verified.is_(verified))
        if q and q.strip():
            search_term = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    Route.title.ilike(search_term),
                    Route.summary.ilike(search_term),
                    Route.city.ilike(search_term),
                )
            )
        if saved:
            stmt = stmt.join(
                FavoriteRoute,
                (FavoriteRoute.route_id == Route.id) & (FavoriteRoute.user_id == user_id),
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.scalar(count_stmt)) or 0

        # Paginate
        stmt = stmt.order_by(Route.title.asc()).offset(offset).limit(limit)
        res = await self.db.scalars(stmt)
        routes = list(res.all())

        return routes, total

    async def get_route_by_id(self, route_id: uuid.UUID) -> Route | None:
        """Fetch route detail by ID with preloaded origins."""
        stmt = (
            select(Route)
            .options(joinedload(Route.origins))
            .where(Route.id == route_id, Route.deleted_at.is_(None), Route.status == "active")
        )
        return typing_cast(Route | None, await self.db.scalar(stmt))

    async def get_route_origins(self, route_id: uuid.UUID) -> list[RouteOrigin]:
        """Fetch origins for a given route ordered by sort_order."""
        stmt = (
            select(RouteOrigin)
            .where(RouteOrigin.route_id == route_id)
            .order_by(RouteOrigin.sort_order.asc(), RouteOrigin.name.asc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    # -------------------------------------------------------------------------
    # ECO-0504: Route Geometry & Map Payload
    # -------------------------------------------------------------------------

    async def get_route_geometry(
        self, route_id: uuid.UUID, origin_id: uuid.UUID | None = None
    ) -> tuple[RouteGeometry | None, dict[str, Any] | None]:
        """Fetch route geometry and GeoJSON representation for a given origin or default origin."""
        stmt = (
            select(RouteGeometry, ST_AsGeoJSON(RouteGeometry.geometry).label("geojson_str"))
            .join(RouteOrigin, RouteGeometry.route_origin_id == RouteOrigin.id)
            .where(RouteOrigin.route_id == route_id)
        )

        if origin_id:
            stmt = stmt.where(RouteGeometry.route_origin_id == origin_id)
        else:
            stmt = stmt.order_by(RouteOrigin.sort_order.asc())

        exec_res = await self.db.execute(stmt)
        first_row = exec_res.first()
        if not first_row:
            return None, None

        geom, geojson_str = first_row[0], first_row[1]
        geojson_obj = json.loads(geojson_str) if geojson_str else None
        return geom, geojson_obj

    # -------------------------------------------------------------------------
    # ECO-0505: Route Alerts
    # -------------------------------------------------------------------------

    async def get_active_route_alerts(self, route_id: uuid.UUID) -> list[RouteAlert]:
        """Fetch active alerts for a route respecting time window."""
        now = datetime.now(UTC)
        stmt = (
            select(RouteAlert)
            .where(
                RouteAlert.route_id == route_id,
                RouteAlert.is_active.is_(True),
                or_(RouteAlert.starts_at.is_(None), RouteAlert.starts_at <= now),
                or_(RouteAlert.ends_at.is_(None), RouteAlert.ends_at >= now),
            )
            .order_by(RouteAlert.published_at.desc())
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    # -------------------------------------------------------------------------
    # ECO-0506: Actors & Categories
    # -------------------------------------------------------------------------

    async def list_actor_categories(self) -> list[ActorCategory]:
        """Fetch all actor categories ordered by sort_order."""
        stmt = select(ActorCategory).order_by(
            ActorCategory.sort_order.asc(), ActorCategory.label.asc()
        )
        res = await self.db.scalars(stmt)
        return list(res.all())

    async def list_route_actors(
        self,
        route_id: uuid.UUID,
        q: str | None = None,
        category_slug: str | None = None,
        origin_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[tuple[Actor, str, float | None, float | None]], int]:
        """List route actors with PostGIS coordinates, search and pagination."""
        stmt = (
            select(
                Actor,
                ActorCategory.slug.label("category_slug"),
                ActorCategory.label.label("category_label"),
                ST_Y(cast(Actor.location, Geometry)).label("latitude"),
                ST_X(cast(Actor.location, Geometry)).label("longitude"),
            )
            .join(RouteActor, Actor.id == RouteActor.actor_id)
            .join(ActorCategory, Actor.category_id == ActorCategory.id)
            .where(
                RouteActor.route_id == route_id,
                RouteActor.archived_at.is_(None),
                Actor.deleted_at.is_(None),
            )
        )

        if category_slug:
            stmt = stmt.where(ActorCategory.slug == category_slug)
        if origin_id:
            origin_code = (
                select(RouteOrigin.code)
                .where(RouteOrigin.id == origin_id, RouteOrigin.route_id == route_id)
                .scalar_subquery()
            )
            stmt = stmt.where(RouteActor.origin_flags[origin_code].as_boolean().is_(True))
        if q and q.strip():
            search_term = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    Actor.name.ilike(search_term),
                    Actor.description.ilike(search_term),
                    Actor.city.ilike(search_term),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.scalar(count_stmt)) or 0

        # Paginate
        stmt = (
            stmt.order_by(RouteActor.sort_order.asc(), Actor.name.asc()).offset(offset).limit(limit)
        )
        exec_res = await self.db.execute(stmt)
        results = exec_res.all()

        formatted_actors = []
        for row in results:
            actor = row[0]
            cat_slug = row[1]
            cat_label = row[2]
            lat = row[3]
            lon = row[4]
            actor._transient_cat_slug = cat_slug
            actor._transient_cat_label = cat_label
            actor._transient_lat = lat
            actor._transient_lon = lon
            formatted_actors.append((actor, cat_slug, lat, lon))

        return formatted_actors, total

    async def get_actor_by_id(
        self, actor_id: uuid.UUID
    ) -> tuple[Actor | None, float | None, float | None, list[dict[str, Any]], str | None]:
        """Fetch an actor with category, coordinates, accessibility and Google reference."""
        stmt = (
            select(
                Actor,
                ST_Y(cast(Actor.location, Geometry)).label("latitude"),
                ST_X(cast(Actor.location, Geometry)).label("longitude"),
            )
            .options(joinedload(Actor.category))
            .where(Actor.id == actor_id, Actor.deleted_at.is_(None))
        )
        exec_res = await self.db.execute(stmt)
        first_row = exec_res.first()
        if not first_row:
            return None, None, None, [], None

        actor, lat, lon = first_row[0], first_row[1], first_row[2]

        # Fetch accessibility features
        feat_stmt = (
            select(
                AccessibilityFeature.slug,
                AccessibilityFeature.label,
                ActorAccessibilityFeature.verification_status,
            )
            .join(
                ActorAccessibilityFeature,
                AccessibilityFeature.id == ActorAccessibilityFeature.feature_id,
            )
            .where(ActorAccessibilityFeature.actor_id == actor_id)
        )
        feat_exec = await self.db.execute(feat_stmt)
        feat_rows = feat_exec.all()
        features = (
            [{"slug": r[0], "label": r[1], "verification_status": r[2]} for r in feat_rows]
            if feat_rows
            else []
        )

        # Fetch external google_place_id if present
        ext_stmt = (
            select(ActorExternalRef.external_id)
            .join(ExternalSource, ExternalSource.id == ActorExternalRef.source_id)
            .where(
                ActorExternalRef.actor_id == actor_id,
                ExternalSource.slug == "google-places",
            )
        )
        google_place_id = await self.db.scalar(ext_stmt)

        return actor, lat, lon, features, google_place_id
