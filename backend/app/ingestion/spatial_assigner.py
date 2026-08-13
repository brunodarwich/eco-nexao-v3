"""Calculate actor relationships with OSRM route geometries (ECO-0307)."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ingestion.osrm_importer import OSRMRouteResult


@dataclass
class ActorSpatialMetrics:
    actor_id: str
    route_id: str
    distance_to_route_m: float
    route_segment_index: int
    km_along_route: float
    origin_flags: dict[str, Any]


def calculate_actor_spatial_metrics(
    actor_lat: float,
    actor_lon: float,
    route_results: dict[str, OSRMRouteResult],
    db_session: Session | None = None,
) -> ActorSpatialMetrics:
    """Calculate route distance, position, segment index, and origin flags."""

    # Porto route is canonical for distance along route
    canonical_route = route_results.get("porto")

    if db_session:
        # PostGIS query if database session is present
        query = text(
            """
            SELECT 
                ST_Distance(
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                    ST_GeomFromText(:wkt_line, 4326)::geography
                ) as dist_m,
                ST_LineLocatePoint(
                    ST_GeomFromText(:wkt_line, 4326),
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                ) as frac
        """
        )
        res = db_session.execute(
            query,
            {
                "lat": actor_lat,
                "lon": actor_lon,
                "wkt_line": canonical_route.wkt_linestring if canonical_route else "",
            },
        ).fetchone()

        dist_m = float(res[0]) if res and res[0] is not None else 0.0
        frac = float(res[1]) if res and res[1] is not None else 0.0
    else:
        # Fallback pure python distance calculation for offline/fixture mode
        dist_m = 0.0
        frac = 0.0
        if canonical_route and canonical_route.points:
            # Find nearest point index in route
            min_d = float("inf")
            nearest_idx = 0
            for idx, pt in enumerate(canonical_route.points):
                d = (pt.latitude - actor_lat) ** 2 + (pt.longitude - actor_lon) ** 2
                if d < min_d:
                    min_d = d
                    nearest_idx = idx

            dist_m = math_point_dist_m(
                actor_lat,
                actor_lon,
                canonical_route.points[nearest_idx].latitude,
                canonical_route.points[nearest_idx].longitude,
            )
            frac = nearest_idx / max(1, len(canonical_route.points) - 1)

    total_dist_km = canonical_route.distance_m / 1000.0 if canonical_route else 45.229
    km_along_route = round(frac * total_dist_km, 3)
    segment_idx = (
        int(frac * (len(canonical_route.points) - 1))
        if canonical_route and canonical_route.points
        else 0
    )

    # Origin flags logic (porto, aeroporto, rodoviaria)
    origin_flags = {
        "porto": True,
        "aeroporto": True,
        "rodoviaria": True,
        "km_porto": km_along_route,
    }

    return ActorSpatialMetrics(
        actor_id="",
        route_id="",
        distance_to_route_m=round(dist_m, 2),
        route_segment_index=segment_idx,
        km_along_route=km_along_route,
        origin_flags=origin_flags,
    )


def math_point_dist_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine point distance in meters."""
    import math

    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
