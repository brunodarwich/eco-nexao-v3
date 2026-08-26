"""Read-only persistence boundary for ephemeral routing previews."""

import uuid
from typing import cast as typing_cast

from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Route, RouteGeometry, RouteOrigin


class RoutingRepository:
    """Resolve only editorial route data; dynamic coordinates are never persisted."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_active_route_region_id(self, route_id: uuid.UUID) -> uuid.UUID | None:
        statement = select(Route.region_id).where(
            Route.id == route_id,
            Route.deleted_at.is_(None),
            Route.status == "active",
        )
        return typing_cast(uuid.UUID | None, await self.db.scalar(statement))

    async def list_official_destination_endpoints(
        self, route_id: uuid.UUID
    ) -> list[tuple[float, float]]:
        """Return endpoints of persisted official geometries as (latitude, longitude)."""
        endpoint = func.ST_EndPoint(cast(RouteGeometry.geometry, Geometry))
        statement = (
            select(ST_Y(endpoint), ST_X(endpoint))
            .join(RouteOrigin, RouteOrigin.id == RouteGeometry.route_origin_id)
            .where(RouteOrigin.route_id == route_id)
            .order_by(RouteOrigin.sort_order.asc(), RouteGeometry.id.asc())
        )
        rows = (await self.db.execute(statement)).all()
        return [
            (float(row[0]), float(row[1]))
            for row in rows
            if row[0] is not None and row[1] is not None
        ]
