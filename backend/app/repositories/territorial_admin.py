"""Repository layer for administrative territorial domain operations (ECO-1602)."""

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from geoalchemy2.functions import ST_X, ST_Y, ST_AsGeoJSON, ST_MakePoint, ST_SetSRID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Region, Route, RouteGeometry, RouteOrigin


class TerritorialAdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -------------------------------------------------------------------------
    # Region Admin Repository
    # -------------------------------------------------------------------------

    async def get_region_by_id(self, region_id: uuid.UUID) -> Region | None:
        stmt = select(Region).where(Region.id == region_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_region_by_slug(self, slug: str) -> Region | None:
        stmt = select(Region).where(Region.slug == slug)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_regions(self, include_inactive: bool = True) -> Sequence[Region]:
        stmt = select(Region).order_by(Region.name.asc())
        if not include_inactive:
            stmt = stmt.where(Region.is_active.is_(True))
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create_region(
        self,
        slug: str,
        name: str,
        state_code: str,
        latitude: float | None = None,
        longitude: float | None = None,
        is_active: bool = True,
    ) -> Region:
        center_geom = None
        if latitude is not None and longitude is not None:
            center_geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        region = Region(
            id=uuid.uuid4(),
            slug=slug,
            name=name,
            state_code=state_code,
            center=center_geom,
            is_active=is_active,
        )
        self.db.add(region)
        await self.db.flush()
        return region

    async def update_region(
        self,
        region_id: uuid.UUID,
        name: str | None = None,
        state_code: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        is_active: bool | None = None,
    ) -> Region | None:
        region = await self.get_region_by_id(region_id)
        if not region:
            return None

        if name is not None:
            region.name = name
        if state_code is not None:
            region.state_code = state_code
        if is_active is not None:
            region.is_active = is_active
        if latitude is not None and longitude is not None:
            region.center = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        region.updated_at = datetime.now(UTC)
        await self.db.flush()
        return region

    async def get_region_coordinates(self, region: Region) -> tuple[float | None, float | None]:
        if region.center is None:
            return None, None
        stmt = select(
            ST_Y(region.center).label("lat"),
            ST_X(region.center).label("lon"),
        )
        res = await self.db.execute(stmt)
        row = res.first()
        if row:
            lat_val = float(row.lat) if row.lat is not None else None
            lon_val = float(row.lon) if row.lon is not None else None
            return lat_val, lon_val
        return None, None

    # -------------------------------------------------------------------------
    # Route Admin Repository
    # -------------------------------------------------------------------------

    async def get_route_by_id(self, route_id: uuid.UUID) -> Route | None:
        stmt = select(Route).where(Route.id == route_id, Route.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_route_by_slug(self, slug: str) -> Route | None:
        stmt = select(Route).where(Route.slug == slug, Route.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_routes(
        self,
        region_id: uuid.UUID | None = None,
        status: str | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Route], int]:
        stmt = select(Route).where(Route.deleted_at.is_(None))
        count_stmt = select(func.count()).select_from(Route).where(Route.deleted_at.is_(None))

        if region_id:
            stmt = stmt.where(Route.region_id == region_id)
            count_stmt = count_stmt.where(Route.region_id == region_id)
        if status:
            stmt = stmt.where(Route.status == status)
            count_stmt = count_stmt.where(Route.status == status)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(Route.title.ilike(pattern) | Route.city.ilike(pattern))
            count_stmt = count_stmt.where(Route.title.ilike(pattern) | Route.city.ilike(pattern))

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(Route.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        routes = res.scalars().all()

        return routes, total

    async def create_route(
        self,
        region_id: uuid.UUID,
        slug: str,
        title: str,
        city: str,
        state_code: str,
        summary: str | None = None,
        status: str = "draft",
        is_verified: bool = False,
        best_season: str | None = None,
        connectivity: str | None = None,
        road_access: str | None = None,
        payment_info: str | None = None,
        cover_media_id: uuid.UUID | None = None,
    ) -> Route:
        now = datetime.now(UTC)
        route = Route(
            id=uuid.uuid4(),
            region_id=region_id,
            slug=slug,
            title=title,
            summary=summary,
            city=city,
            state_code=state_code,
            status=status,
            is_verified=is_verified,
            verified_at=now if is_verified else None,
            best_season=best_season,
            connectivity=connectivity,
            road_access=road_access,
            payment_info=payment_info,
            cover_media_id=cover_media_id,
        )
        self.db.add(route)
        await self.db.flush()
        return route

    async def update_route(
        self,
        route_id: uuid.UUID,
        region_id: uuid.UUID | None = None,
        title: str | None = None,
        summary: str | None = None,
        city: str | None = None,
        state_code: str | None = None,
        status: str | None = None,
        is_verified: bool | None = None,
        best_season: str | None = None,
        connectivity: str | None = None,
        road_access: str | None = None,
        payment_info: str | None = None,
        cover_media_id: uuid.UUID | None = None,
    ) -> Route | None:
        route = await self.get_route_by_id(route_id)
        if not route:
            return None

        if region_id is not None:
            route.region_id = region_id
        if title is not None:
            route.title = title
        if summary is not None:
            route.summary = summary
        if city is not None:
            route.city = city
        if state_code is not None:
            route.state_code = state_code
        if status is not None:
            route.status = status
        if is_verified is not None:
            route.is_verified = is_verified
            if is_verified and not route.verified_at:
                route.verified_at = datetime.now(UTC)
        if best_season is not None:
            route.best_season = best_season
        if connectivity is not None:
            route.connectivity = connectivity
        if road_access is not None:
            route.road_access = road_access
        if payment_info is not None:
            route.payment_info = payment_info
        if cover_media_id is not None:
            route.cover_media_id = cover_media_id

        route.updated_at = datetime.now(UTC)
        await self.db.flush()
        return route

    async def archive_route(self, route_id: uuid.UUID) -> Route | None:
        route = await self.get_route_by_id(route_id)
        if not route:
            return None

        route.status = "archived"
        route.deleted_at = datetime.now(UTC)
        route.updated_at = datetime.now(UTC)
        await self.db.flush()
        return route

    # -------------------------------------------------------------------------
    # Route Origin Admin Repository
    # -------------------------------------------------------------------------

    async def get_origin_by_id(self, origin_id: uuid.UUID) -> RouteOrigin | None:
        stmt = select(RouteOrigin).where(RouteOrigin.id == origin_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_origin_by_code(self, route_id: uuid.UUID, code: str) -> RouteOrigin | None:
        stmt = select(RouteOrigin).where(RouteOrigin.route_id == route_id, RouteOrigin.code == code)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_origins_by_route(self, route_id: uuid.UUID) -> Sequence[RouteOrigin]:
        stmt = (
            select(RouteOrigin)
            .where(RouteOrigin.route_id == route_id)
            .order_by(RouteOrigin.sort_order.asc(), RouteOrigin.name.asc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create_origin(
        self,
        route_id: uuid.UUID,
        code: str,
        name: str,
        latitude: float,
        longitude: float,
        description: str | None = None,
        distance_m: int | None = None,
        duration_s: int | None = None,
        sort_order: int = 0,
    ) -> RouteOrigin:
        loc_geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        origin = RouteOrigin(
            id=uuid.uuid4(),
            route_id=route_id,
            code=code,
            name=name,
            description=description,
            location=loc_geom,
            distance_m=distance_m,
            duration_s=duration_s,
            sort_order=sort_order,
        )
        self.db.add(origin)
        await self.db.flush()
        return origin

    async def update_origin(
        self,
        origin_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        distance_m: int | None = None,
        duration_s: int | None = None,
        sort_order: int | None = None,
    ) -> RouteOrigin | None:
        origin = await self.get_origin_by_id(origin_id)
        if not origin:
            return None

        if name is not None:
            origin.name = name
        if description is not None:
            origin.description = description
        if distance_m is not None:
            origin.distance_m = distance_m
        if duration_s is not None:
            origin.duration_s = duration_s
        if sort_order is not None:
            origin.sort_order = sort_order
        if latitude is not None and longitude is not None:
            origin.location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        origin.updated_at = datetime.now(UTC)
        await self.db.flush()
        return origin

    async def delete_origin(self, origin_id: uuid.UUID) -> bool:
        origin = await self.get_origin_by_id(origin_id)
        if not origin:
            return False
        await self.db.delete(origin)
        await self.db.flush()
        return True

    async def get_origin_coordinates(self, origin: RouteOrigin) -> tuple[float, float]:
        stmt = select(
            ST_Y(origin.location).label("lat"),
            ST_X(origin.location).label("lon"),
        )
        res = await self.db.execute(stmt)
        row = res.first()
        if row and row.lat is not None and row.lon is not None:
            return float(row.lat), float(row.lon)
        return 0.0, 0.0

    # -------------------------------------------------------------------------
    # Route Geometry Admin Repository
    # -------------------------------------------------------------------------

    async def get_geometry_by_id(self, geometry_id: uuid.UUID) -> RouteGeometry | None:
        stmt = select(RouteGeometry).where(RouteGeometry.id == geometry_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_geometry_by_origin(
        self, route_origin_id: uuid.UUID, provider: str = "osrm"
    ) -> RouteGeometry | None:
        stmt = select(RouteGeometry).where(
            RouteGeometry.route_origin_id == route_origin_id,
            RouteGeometry.provider == provider,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_geometry(
        self,
        route_origin_id: uuid.UUID,
        coordinates: list[list[float]],
        provider: str = "osrm",
        encoded_polyline: str | None = None,
        distance_m: int | None = None,
        duration_s: int | None = None,
        bounds: dict[str, float] | None = None,
        source_hash: str | None = None,
    ) -> RouteGeometry:
        # Construct GeoJSON LineString for PostGIS
        # coordinates: [[lat, lon], ...] or [[lng, lat], ...]
        # Normalize to GeoJSON format [lng, lat]
        geojson_coords = []
        for pt in coordinates:
            if len(pt) >= 2:
                # If first elem is lat (-90..90) and second is lon (-180..180), order as [lon, lat]
                lat, lon = pt[0], pt[1]
                geojson_coords.append([lon, lat])

        geojson_dict = {"type": "LineString", "coordinates": geojson_coords}
        geojson_str = json.dumps(geojson_dict)

        stmt = select(ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326))
        res = await self.db.execute(stmt)
        geom = res.scalar_one()

        route_geom = RouteGeometry(
            id=uuid.uuid4(),
            route_origin_id=route_origin_id,
            provider=provider,
            geometry=geom,
            encoded_polyline=encoded_polyline,
            distance_m=distance_m,
            duration_s=duration_s,
            bounds=bounds,
            source_hash=source_hash,
            source_collected_at=datetime.now(UTC),
        )
        self.db.add(route_geom)
        await self.db.flush()
        return route_geom

    async def update_geometry(
        self,
        geometry_id: uuid.UUID,
        coordinates: list[list[float]] | None = None,
        encoded_polyline: str | None = None,
        distance_m: int | None = None,
        duration_s: int | None = None,
        bounds: dict[str, float] | None = None,
    ) -> RouteGeometry | None:
        geom_obj = await self.get_geometry_by_id(geometry_id)
        if not geom_obj:
            return None

        if coordinates is not None:
            geojson_coords = []
            for pt in coordinates:
                if len(pt) >= 2:
                    geojson_coords.append([pt[1], pt[0]])
            geojson_str = json.dumps({"type": "LineString", "coordinates": geojson_coords})
            res = await self.db.execute(
                select(ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326))
            )
            geom_obj.geometry = res.scalar_one()

        if encoded_polyline is not None:
            geom_obj.encoded_polyline = encoded_polyline
        if distance_m is not None:
            geom_obj.distance_m = distance_m
        if duration_s is not None:
            geom_obj.duration_s = duration_s
        if bounds is not None:
            geom_obj.bounds = bounds

        geom_obj.updated_at = datetime.now(UTC)
        await self.db.flush()
        return geom_obj

    async def get_geometry_geojson(self, route_geom: RouteGeometry) -> dict[str, Any] | None:
        stmt = select(ST_AsGeoJSON(route_geom.geometry))
        res = await self.db.execute(stmt)
        geojson_str = res.scalar_one_or_none()
        if geojson_str:
            return json.loads(geojson_str)  # type: ignore[no-any-return]
        return None
